import asyncio
import sys
from src.bot import NexusBot
from src.config import conf
from src.utils.logging import logger

settings = conf()


async def main():
    """Main entry point for the bot"""
    try:
        logger.info("Starting Nexus Bot...")
        logger.info(f"Command prefix: {settings.discord_command_prefix}")

        bot = NexusBot()
        async with bot:
            await bot.start(settings.discord_token)

    except Exception as e:
        logger.critical(f"Failed to start bot: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown by user")
        sys.exit(0)
    except Exception as e:
        logger.critical("Unexpected error occurred", exc_info=e)
        sys.exit(1)
