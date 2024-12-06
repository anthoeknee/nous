from discord.ext import commands
from src.utils.logging import logger


class ExampleFeature(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("Example feature initialized")

    @commands.command(name="hello")
    async def hello(self, ctx: commands.Context):
        await ctx.send("Hello from the example feature!")


async def setup(bot: commands.Bot):
    await bot.add_cog(ExampleFeature(bot))
