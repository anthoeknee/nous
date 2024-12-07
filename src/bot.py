import discord
from discord.ext import commands
import asyncio
from src.config import conf
from src.utils.logging import logger
from src.feature_manager import FeatureManager
from src.storage.manager import StorageManager
from src.storage.interfaces import (
    StorageScope,
    StorageKey,
    StorageValue,
    StorageBackend,
)
import time

settings = conf()


class NousBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=settings.discord_command_prefix,
            intents=intents,
            owner_id=settings.discord_owner_id,
        )

        # Initialize storage manager
        self.storage = StorageManager(settings)
        self.state = None  # Will be initialized in setup_hook

    async def setup_hook(self):
        """Initialize bot services and load features"""
        logger.info("Initializing bot...")

        # Initialize storage
        try:
            await self.storage.initialize()
            # Use hybrid storage if available, fallback to database
            if StorageBackend.HYBRID in self.storage.storages:
                self.state = self.storage.get_storage(StorageBackend.HYBRID)
            else:
                self.state = self.storage.get_storage()
            logger.info("Storage system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize storage: {e}")
            raise

        # Initialize feature manager and load features
        self.feature_manager = FeatureManager(self)
        await self.feature_manager.load_all_features()

        # Initialize default settings
        await self._initialize_default_settings()

        # Store bot start time
        try:
            await self.state.set(
                StorageKey(
                    name="bot_start_time", scope=StorageScope.GLOBAL, namespace="system"
                ),
                StorageValue(value=time.time()),
            )
        except Exception as e:
            logger.error(f"Failed to store bot start time: {e}")

    async def _initialize_default_settings(self):
        """Initialize default settings including permissions and blocklist"""
        default_settings = {
            "permissions": {
                "manage_settings": False,
                "view_settings": True,
                "manage_permissions": False,
            },
            "blocklist": {
                "blocked_users": [],
                "blocked_channels": [],
                "blocked_guilds": [],
            },
        }

        for category, settings in default_settings.items():
            for key, default_value in settings.items():
                try:
                    storage_key = StorageKey(
                        name=key, scope=StorageScope.GLOBAL, namespace=category
                    )

                    # Only set if it doesn't exist
                    try:
                        await self.state.get(storage_key)
                    except KeyError:
                        await self.state.set(
                            storage_key, StorageValue(value=default_value)
                        )
                        logger.debug(f"Initialized default setting: {category}.{key}")
                except Exception as e:
                    logger.error(f"Failed to initialize setting {category}.{key}: {e}")

        # Set owner permissions
        if self.owner_id:
            owner_permissions = {
                "manage_settings": True,
                "view_settings": True,
                "manage_permissions": True,
            }

            for perm_name, allowed in owner_permissions.items():
                try:
                    await self.state.set(
                        StorageKey(
                            name=perm_name,
                            scope=StorageScope.USER,
                            scope_id=self.owner_id,
                            namespace="permissions",
                        ),
                        StorageValue(value=allowed, metadata={"priority": 100}),
                    )
                except Exception as e:
                    logger.error(f"Failed to set owner permission {perm_name}: {e}")

    async def check_blocklist(self, ctx: commands.Context) -> bool:
        """Check if the context is blocked"""
        try:
            blocked_data = await asyncio.gather(
                self.state.get(
                    StorageKey(
                        name="blocked_users",
                        scope=StorageScope.GLOBAL,
                        namespace="blocklist",
                    )
                ),
                self.state.get(
                    StorageKey(
                        name="blocked_channels",
                        scope=StorageScope.GLOBAL,
                        namespace="blocklist",
                    )
                ),
                self.state.get(
                    StorageKey(
                        name="blocked_guilds",
                        scope=StorageScope.GLOBAL,
                        namespace="blocklist",
                    )
                ),
            )

            blocked_users, blocked_channels, blocked_guilds = [
                d.value for d in blocked_data
            ]

            if ctx.author.id in blocked_users:
                return False
            if ctx.channel.id in blocked_channels:
                return False
            if ctx.guild and ctx.guild.id in blocked_guilds:
                return False

            return True
        except Exception as e:
            logger.error(f"Error checking blocklist: {e}")
            return True  # Allow by default if there's an error

    async def process_commands(self, message):
        if message.author.bot:
            return

        ctx = await self.get_context(message)
        try:
            if not await self.check_blocklist(ctx):
                return
            await self.invoke(ctx)
        except Exception as e:
            logger.error(f"Error processing command: {e}")

    async def close(self):
        """Cleanup when bot is shutting down"""
        try:
            await self.feature_manager.unload_all_features()
            # Store shutdown time
            if self.state:
                await self.state.set(
                    StorageKey(
                        name="bot_shutdown_time",
                        scope=StorageScope.GLOBAL,
                        namespace="system",
                    ),
                    StorageValue(value=time.time()),
                )
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        finally:
            await super().close()
