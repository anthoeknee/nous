import discord
from discord.ext import commands
from src.config import conf
from src.database.manager import db
from src.utils.logging import logger
from src.events import events, ErrorEvent
from src.feature_manager import FeatureManager
from src.database.repositories.settings import SettingRepository
from src.database.repositories.permissions import PermissionRepository
from src.services.manager import ServiceManager
from src.services.ai_provider import AIProviderService
from src.services.database import DatabaseService

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

        self.db = db
        self.services = ServiceManager()

        # Initialize repositories
        self.settings_repo = SettingRepository()
        self.permissions_repo = PermissionRepository()

    async def setup_hook(self):
        """Initialize bot services and load cogs"""
        logger.info("Initializing services...")

        # Initialize services
        try:
            # Register database service
            self.services.register("database", DatabaseService())

            # Register AI provider service
            self.services.register("ai_provider", AIProviderService())

            # Initialize all services
            await self.services.initialize_all()

            # Register repositories with database service
            db_service = self.services.get("database", DatabaseService)
            db_service.register_repository("settings", self.settings_repo)
            db_service.register_repository("permissions", self.permissions_repo)

        except Exception as e:
            logger.error(f"Service initialization failed: {str(e)}")
            raise

        # Initialize feature manager and load features
        self.feature_manager = FeatureManager(self)
        await self.feature_manager.load_all_features()

        # Initialize default blocklist settings
        await self._initialize_blocklist_settings()

    async def _initialize_default_permissions(self):
        """Initialize default permissions for the bot"""
        try:
            # Set up default global permissions
            default_permissions = {
                "manage_settings": False,  # Default to false for regular users
                "view_settings": True,  # Allow viewing settings by default
                "manage_permissions": False,  # Restrict permission management
            }

            # Set default permissions
            for perm_name, allowed in default_permissions.items():
                existing_perm = await self.permissions_repo.get_permission(
                    name=perm_name, scope="global"
                )
                if not existing_perm:
                    await self.permissions_repo.set_permission(
                        name=perm_name, allowed=allowed, scope="global", priority=0
                    )

            # Set owner permissions
            owner_permissions = {
                "manage_settings": True,
                "view_settings": True,
                "manage_permissions": True,
            }

            for perm_name, allowed in owner_permissions.items():
                await self.permissions_repo.set_permission(
                    name=perm_name,
                    allowed=allowed,
                    scope="user",
                    scope_id=self.owner_id,
                    priority=100,  # Highest priority for owner
                )

        except Exception as e:
            logger.error(f"Error initializing default permissions: {str(e)}")
            raise

    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f"Logged in as {self.user.name}")
        logger.info(f"Serving {len(self.guilds)} guilds")

        activity = (
            discord.Game(name=settings.discord_activity)
            if settings.discord_activity
            else None
        )
        await self.change_presence(
            status=discord.Status(settings.discord_status), activity=activity
        )

    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            return

        logger.error(f"Command error: {str(error)}")
        await events.emit(
            ErrorEvent(
                error=error,
                context={"command": ctx.command.name if ctx.command else None},
            )
        )

        error_message = "An error occurred while executing the command."
        if isinstance(error, commands.UserInputError):
            error_message = str(error)

        await ctx.send(error_message)

    async def close(self):
        """Cleanup when bot is shutting down"""
        # Cleanup services
        await self.services.cleanup_all()

        # Call parent close method
        await super().close()

    async def _initialize_blocklist_settings(self):
        """Initialize default blocklist settings"""
        default_blocklist_settings = {
            "blocked_users": [],  # List of user IDs
            "blocked_channels": [],  # List of channel IDs
            "blocked_guilds": [],  # List of guild IDs
        }

        for key, default_value in default_blocklist_settings.items():
            setting = await self.settings_repo.get_setting(
                key=key, scope="global", category="blocklist"
            )
            if not setting:
                await self.settings_repo.set_setting(
                    key=key, value=default_value, scope="global", category="blocklist"
                )

    async def check_blocklist(self, ctx: commands.Context) -> bool:
        """Check if the context is blocked"""
        # Get blocklist settings
        blocked_users = await self.settings_repo.get_setting(
            key="blocked_users", scope="global", category="blocklist"
        )
        blocked_channels = await self.settings_repo.get_setting(
            key="blocked_channels", scope="global", category="blocklist"
        )
        blocked_guilds = await self.settings_repo.get_setting(
            key="blocked_guilds", scope="global", category="blocklist"
        )

        # Check if user, channel or guild is blocked
        if blocked_users and ctx.author.id in blocked_users.value:
            return False
        if blocked_channels and ctx.channel.id in blocked_channels.value:
            return False
        if blocked_guilds and ctx.guild and ctx.guild.id in blocked_guilds.value:
            return False

        return True

    async def process_commands(self, message):
        """Override to add blocklist check"""
        if message.author.bot:
            return

        ctx = await self.get_context(message)

        # Check if context is blocked before processing command
        if not await self.check_blocklist(ctx):
            return

        await self.invoke(ctx)
