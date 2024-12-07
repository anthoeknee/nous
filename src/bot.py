import discord
from discord.ext import commands
from src.config import conf
from src.database.manager import db
from src.utils.logging import logger
from src.events import events, ErrorEvent
from src.feature_manager import FeatureManager
from src.database.repositories.settings import SettingRepository
from src.database.repositories.permissions import PermissionRepository

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
        self.providers = {}
        # Initialize repositories
        self.settings_repo = SettingRepository()
        self.permissions_repo = PermissionRepository()

    async def setup_hook(self):
        """Initialize bot services and load cogs"""
        logger.info("Initializing services...")

        # Initialize providers
        try:
            from src.utils.providers import ProviderFactory

            # Initialize OpenAI provider
            self.providers["openai"] = ProviderFactory.create_provider(
                "openai", api_key=settings.openai_api_key, identifier="default"
            )

            # Initialize Groq provider
            self.providers["groq"] = ProviderFactory.create_provider(
                "groq", api_key=settings.groq_api_key, identifier="default"
            )

            logger.info("AI providers initialized")
        except Exception as e:
            logger.error(f"Provider initialization failed: {str(e)}")
            raise

        # Initialize database
        try:
            # Load and create all database tables
            self.db.create_all()
            logger.info("Database initialized")

            # Initialize default permissions if needed
            await self._initialize_default_permissions()
            logger.info("Default permissions initialized")
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise

        # Initialize feature manager and load features
        self.feature_manager = FeatureManager(self)
        await self.feature_manager.load_all_features()

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
        # Close provider connections
        for provider in self.providers.values():
            await provider.close()

        # Call parent close method
        await super().close()
