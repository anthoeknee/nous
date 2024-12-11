import logging
import sys
from pathlib import Path
import colorlog
from src.config import settings


def setup_logger(name: str = "discord_bot") -> logging.Logger:
    """
    Configure and return a logger instance with both console and file handlers.
    Creates a new log file for each bot run.

    Args:
        name (str): Name of the logger instance

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Prevent adding handlers multiple times
    if logger.handlers:
        return logger

    # Color scheme for different log levels
    color_scheme = {
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    }

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s[%(asctime)s] %(levelname)-8s %(name)s: %(message)s%(reset)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors=color_scheme,
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    try:
        log_dir = Path(settings.log_dir)
        log_dir.mkdir(exist_ok=True)

        # Create new log file for current session
        file_handler = logging.FileHandler(
            filename=log_dir / "discord_bot.log",
            encoding="utf-8",
            mode="w",  # 'w' mode creates a new file each time
        )
        file_formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        logger.info("=== New Bot Session Started ===")
    except Exception as e:
        logger.error(f"Failed to setup file logging: {e}")

    return logger


# Create a global logger instance
logger = setup_logger()

# Usage example:
# from src.utils.logging import logger
# logger.info("Bot is starting...")
# logger.error("An error occurred", exc_info=True)
