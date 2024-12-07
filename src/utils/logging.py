import logging
import sys
import os
import colorlog
from pathlib import Path
from src.config import conf

settings = conf()

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)
log_file = logs_dir / "latest.log"

def setup_logger(name: str = "bot") -> logging.Logger:
    """Configure and return a logger instance with colored output and file logging."""
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level))

    # Remove any existing handlers
    logger.handlers = []

    # Create colored formatter for console
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s %(levelname)-8s%(reset)s %(blue)s%(name)s%(reset)s: %(message)s",
        datefmt="%H:%M:%S",
        reset=True,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )

    # Create file formatter (without colors)
    file_formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Create file handler (mode='w' to clear file on each run)
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


# Create a default logger instance
logger = setup_logger()
