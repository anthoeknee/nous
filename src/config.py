from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Discord Configuration
    discord_token: str
    discord_owner_id: int
    discord_command_prefix: str = "n!"
    discord_guild_ids: Optional[str] = None
    discord_status: str = "online"
    discord_activity: Optional[str] = None

    # Database Configuration
    database_url: str
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_timeout: int = 30
    database_echo: bool = False

    # Redis Configuration
    redis_enabled: bool = False
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    redis_ttl: int = 3600

    # Logging Configuration
    log_level: str = "INFO"
    log_dir: str = "logs"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: str = "bot.log"

    # API Keys
    xai_api_key: str
    openai_api_key: str
    groq_api_key: str
    cohere_api_key: str
    fal_api_key: str

    # Supabase Configuration
    supabase_url: str
    supabase_key: str
    supabase_password: str
    supabase_service_role_secret: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


class _Settings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = Settings()
        return cls._instance


# Create a global settings instance
settings = _Settings()


# Make it easier to import settings
def conf() -> Settings:
    return settings
