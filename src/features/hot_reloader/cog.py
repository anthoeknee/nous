import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from discord.ext import commands, tasks
from pathlib import Path
from src.utils.logging import logger
from src.events import events, FileChangeEvent, FeatureReloadEvent
import importlib
import sys
import time
from queue import Queue
import hashlib


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, change_queue: Queue):
        self.change_queue = change_queue
        self.cooldown = {}
        self.cooldown_time = 1.0  # Seconds
        self.last_change = None
        self.file_hashes = {}

    def get_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file contents"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash: {e}")
            return None

    def on_modified(self, event):
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.suffix != ".py":
            return

        # Deduplicate changes
        current_time = time.time()
        if self.last_change and self.last_change[0] == file_path:
            if current_time - self.last_change[1] < self.cooldown_time:
                return

        # Check if file content has actually changed
        current_hash = self.get_file_hash(file_path)
        if current_hash is None:
            return

        if (
            file_path in self.file_hashes
            and self.file_hashes[file_path] == current_hash
        ):
            return  # File content hasn't changed

        self.file_hashes[file_path] = current_hash
        self.last_change = (file_path, current_time)

        # Convert path to module path
        try:
            relative_path = file_path.relative_to(Path.cwd() / "src")
            module_path = ".".join(["src"] + list(relative_path.parent.parts))

            # Put the change in the queue instead of emitting directly
            self.change_queue.put((relative_path, module_path))
        except ValueError:
            pass


class HotReloader(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.change_queue = Queue()
        self.observer = Observer()
        self.file_handler = FileChangeHandler(self.change_queue)
        self.processing_lock = asyncio.Lock()

        # Start monitoring src directory
        src_path = Path.cwd() / "src"
        self.observer.schedule(self.file_handler, str(src_path), recursive=True)

        # Start monitoring
        self.start_monitoring.start()
        self.process_changes.start()

        # Register event handlers
        self.register_events()

    def register_events(self):
        """Register event handlers for file changes"""

        @events.on(FileChangeEvent)
        async def handle_file_change(event: FileChangeEvent):
            # Prevent processing if we're already handling a change
            if self.processing_lock.locked():
                return

            async with self.processing_lock:
                path = event.file_path
                module = event.module_path

                # Skip if it's the hot_reloader itself
                if "hot_reloader" in str(path):
                    return

                # Handle feature reloads
                if "features" in path.parts:
                    feature_name = path.parts[path.parts.index("features") + 1]
                    logger.info(f"Attempting to reload feature: {feature_name}")

                    try:
                        success = await self.bot.feature_manager.reload_feature(
                            feature_name
                        )
                        await events.emit(
                            FeatureReloadEvent(
                                feature_name=feature_name, success=success
                            )
                        )
                    except Exception as e:
                        await events.emit(
                            FeatureReloadEvent(
                                feature_name=feature_name, success=False, error=e
                            )
                        )

                # Handle module reloads
                elif module in sys.modules:
                    try:
                        logger.info(f"Reloading module: {module}")
                        importlib.reload(sys.modules[module])
                    except Exception as e:
                        logger.error(f"Failed to reload module {module}: {e}")

        @events.on(FeatureReloadEvent)
        async def handle_feature_reload(event: FeatureReloadEvent):
            status = "successfully" if event.success else "failed to"
            message = f"Feature '{event.feature_name}' {status} reload"
            if event.error:
                message += f": {str(event.error)}"
            logger.info(message)

    def cog_unload(self):
        self.start_monitoring.cancel()
        self.process_changes.cancel()
        self.observer.stop()
        self.observer.join()

    @tasks.loop(count=1)
    async def start_monitoring(self):
        self.observer.start()

    @tasks.loop(seconds=1)
    async def process_changes(self):
        """Process any queued file changes"""
        while not self.change_queue.empty():
            relative_path, module_path = self.change_queue.get()
            await events.emit(
                FileChangeEvent(
                    file_path=relative_path,
                    module_path=module_path,
                    change_type="modified",
                )
            )

    @commands.command(name="reload_feature")
    @commands.is_owner()
    async def reload_feature_command(self, ctx, feature_name: str):
        """Manually reload a feature"""
        try:
            success = await self.bot.feature_manager.reload_feature(feature_name)
            await events.emit(
                FeatureReloadEvent(feature_name=feature_name, success=success)
            )
            await ctx.send(
                f"Feature '{feature_name}' {'reloaded' if success else 'failed to reload'}"
            )
        except Exception as e:
            await events.emit(
                FeatureReloadEvent(feature_name=feature_name, success=False, error=e)
            )
            await ctx.send(f"Error reloading feature '{feature_name}': {str(e)}")


async def setup(bot):
    await bot.add_cog(HotReloader(bot))
