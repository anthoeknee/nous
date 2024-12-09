import asyncio
import sys
from src.bot import NousBot
from src.config import conf
from src.utils.logging import logger
import discord

settings = conf()


async def main():
    """Main entry point for the bot"""
    try:
        logger.info("Starting Nexus Bot...")
        logger.info(f"Command prefix: {settings.discord_command_prefix}")

        bot = NousBot()

        try:
            async with bot:
                logger.info("Connecting to Discord...")
                await bot.start(settings.discord_token)
        except discord.LoginFailure:
            logger.critical("Failed to login to Discord. Please check your token.")
            return
        except discord.PrivilegedIntentsRequired:
            logger.critical(
                "Privileged intents are required but not enabled in the Discord Developer Portal."
            )
            return
        except Exception as e:
            logger.critical(f"Failed to connect to Discord: {str(e)}")
            return

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
