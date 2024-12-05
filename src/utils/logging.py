import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from src.config import conf

settings = conf()


def setup_logger(name: str = "bot") -> logging.Logger:
    """Configure and return a logger instance."""
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level))

    # Create formatters
    formatter = logging.Formatter(settings.log_format)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create file handler
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(exist_ok=True)
    file_handler = RotatingFileHandler(
        log_dir / settings.log_file,
        maxBytes=10_000_000,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Create a default logger instance
logger = setup_logger()
