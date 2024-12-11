import asyncio
import sys
from pathlib import Path

from src.bot import Bot
from src.config import settings
from src.utils.logging import logger

# Add this debug section
logger.debug("Environment Check:")
logger.debug(f"Database Session URL: {settings.database_session_url[:10]}...")
logger.debug(f"Database Transaction URL: {settings.database_transaction_url[:10]}...")
logger.debug(f"Database Direct URL: {settings.database_direct_url[:10]}...")
logger.debug(f"Use Connection Pooling: {settings.use_connection_pooling}")


async def main():
    try:
        # Create and start the bot
        bot = Bot()

        logger.info("Starting bot...")
        await bot.start(settings.discord_token)

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        logger.exception("Full traceback:")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)
