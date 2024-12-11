from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool

# Import your models and config
from src.storage.models.base import Base
from src.config import settings

config = context.config
target_metadata = Base.metadata

# Modify the direct URL to force IPv4 and use the correct host
db_url = settings.database_direct_url
if "supabase.co" in db_url:
    # Replace the host with the IPv4 pooler host
    db_url = db_url.replace(
        "db.tgzhoarwrhtremwyoqmw.supabase.co", "aws-0-us-east-1.pooler.supabase.com"
    )

# Escape % for ConfigParser
db_url = db_url.replace("%", "%%")
config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
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
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = config.get_main_option("sqlalchemy.url")

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
