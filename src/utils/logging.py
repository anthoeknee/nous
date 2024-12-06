import logging
import sys
import colorlog
from src.config import conf

settings = conf()


def setup_logger(name: str = "bot") -> logging.Logger:
    """Configure and return a logger instance with colored output."""
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level))

    # Remove any existing handlers
    logger.handlers = []

    # Create colored formatter
    formatter = colorlog.ColoredFormatter(
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

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# Create a default logger instance
logger = setup_logger()
