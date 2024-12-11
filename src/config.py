from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus
import logging

logger = logging.getLogger("discord_bot")


class Settings(BaseSettings):
    # Discord Configuration
    discord_token: str
    discord_secret: str
    discord_owner_id: int
    discord_command_prefix: str

    # AI Provider Configurations
    xai_api_key: str
    openai_api_key: str
    groq_api_key: str
    cohere_api_key: str
    fal_api_key: str
    google_api_key: str

    # Database Configuration
    database_session_url: str
    database_transaction_url: str
    database_direct_url: str
    use_connection_pooling: bool = True

    # Pooling Configuration
    database_pool_size: int = 20
    database_max_overflow: int = 0  # Disabled when using Supabase pooler
    database_pool_timeout: int = 30
    database_pool_pre_ping: bool = True
    database_pool_recycle: int = 300

    # Redis Configuration
    redis_host: str
    redis_port: int
    redis_password: str
    redis_conversation_ttl: int

    # Logging Configuration
    log_level: str = "INFO"
    log_dir: str = "logs"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    def __init__(self, **kwargs):
        try:
            super().__init__(**kwargs)
            logger.debug("Configuration loaded successfully")
        except Exception as e:
            logger.critical(f"Failed to load configuration: {str(e)}")
            raise

    @property
    def active_database_url(self) -> str:
        """Returns the appropriate database URL based on pooling configuration"""
        if self.use_connection_pooling:
            return self.database_transaction_url  # Use transaction pooler URL
        return self.database_direct_url  # Use direct connection

    @property
    def pooling_kwargs(self) -> dict:
        """Returns SQLAlchemy pooling configuration"""
        if self.use_connection_pooling:
            return {
                "pool_size": self.database_pool_size,
                "max_overflow": self.database_max_overflow,
                "pool_timeout": self.database_pool_timeout,
                "pool_pre_ping": self.database_pool_pre_ping,
                "pool_recycle": self.database_pool_recycle,
            }
        return {}  # No pooling for direct connection


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached instance of the settings.
    Use this function to get settings throughout your application.
    """
    try:
        return Settings()
    except Exception as e:
        logger.critical(
            "Failed to initialize settings. Please check your .env file and environment variables."
        )
        raise


# Create a global instance for easy access
settings = get_settings()

# Usage example:
# from src.config import settings
# print(settings.discord_token)
