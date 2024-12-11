import discord
from discord.ext import commands
import logging
from pathlib import Path
from typing import Optional

from .config import settings
from .feature_loader import FeatureLoader
from .storage.manager import storage
from .providers.llm import ProviderFactory

logger = logging.getLogger("discord_bot")


class Bot(commands.Bot):
    def __init__(self):
        # Initialize with intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=settings.discord_command_prefix,
            intents=intents,
            owner_id=settings.discord_owner_id,
        )

        # Initialize components
        self.feature_loader = FeatureLoader(self)
        self.storage = storage

        # Initialize LLM providers
        self.llm_providers = {
            "openai": ProviderFactory.create_provider(
                "openai", settings.openai_api_key
            ),
            "groq": ProviderFactory.create_provider("groq", settings.groq_api_key),
            "google": ProviderFactory.create_provider(
                "google", settings.google_api_key
            ),
        }

    async def setup_hook(self) -> None:
        """Called when the bot is starting up"""
        try:
            # Initialize storage
            await self.storage.initialize()

            # Load all features
            await self.feature_loader.load_all_features()

            logger.info("Bot setup completed successfully")

        except Exception as e:
            logger.error(f"Error during bot setup: {str(e)}")
            raise

    async def close(self) -> None:
        """Called when the bot is shutting down"""
        try:
            # Close storage connections
            await self.storage.close()

            # Close LLM provider connections
            for provider in self.llm_providers.values():
                await provider.close()

            await super().close()
            logger.info("Bot shutdown completed successfully")

        except Exception as e:
            logger.error(f"Error during bot shutdown: {str(e)}")
            raise

    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f"Logged in as {self.user.name} ({self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")

    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Global error handler for commands"""
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
            return

        logger.error(f"Command error in {ctx.command}: {str(error)}")
        await ctx.send(f"An error occurred: {str(error)}")
