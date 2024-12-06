from discord.ext import commands
from src.utils.logging import logger
from src.config import settings
from .main import LLMHandler
from .events import EventHandler


class LLMFeature(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.llm_handler = LLMHandler(api_key=settings.groq_api_key)
        self.event_handler = EventHandler(bot)
        self.bot.llm_handler = self.llm_handler
        logger.info("LLM feature initialized")

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.event_handler.on_message(message)


async def setup(bot: commands.Bot):
    await bot.add_cog(LLMFeature(bot))
