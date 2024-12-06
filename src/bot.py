import discord
from discord.ext import commands
from src.config import conf
from src.database.manager import db
from src.utils.logging import logger
from src.events import events, ErrorEvent
from src.feature_manager import FeatureManager

settings = conf()


class NexusBot(commands.Bot):
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

    async def setup_hook(self):
        """Initialize bot services and load cogs"""
        logger.info("Initializing services...")

        # Initialize database
        try:
            # Load and create all database tables
            self.db.create_all()
            logger.info("Database initialized")
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise

        # Initialize feature manager and load features
        self.feature_manager = FeatureManager(self)
        await self.feature_manager.load_all_features()

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
