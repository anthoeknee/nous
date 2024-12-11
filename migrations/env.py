from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool

# Import your models and config
from src.storage.models.base import Base
from src.config import settings

config = context.config
target_metadata = Base.metadata

# Get the appropriate URL for migrations (use direct URL)
db_url = settings.database_direct_url

# For migrations, we need to use psycopg2 (not asyncpg)
if db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)

# Modify the URL for Supabase pgbouncer if needed
if "supabase.co" in db_url:
    db_url = db_url.replace(
        "db.tgzhoarwrhtremwyoqmw.supabase.com", "aws-0-us-east-1.pooler.supabase.com"
    )

# Escape % for ConfigParser
db_url = db_url.replace("%", "%%")
config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = config.get_main_option("sqlalchemy.url")

    # Create the engine without the statement cache settings
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
