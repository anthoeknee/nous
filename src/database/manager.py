from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from typing import Generator, Any
import importlib
import pkgutil
from pathlib import Path
from src.events import events, DatabaseEvent
from src.config import Settings
from alembic import command
from alembic.config import Config

Base = declarative_base()

settings = Settings()


class DatabaseManager:
    def __init__(self, db_url: str = settings.database_url):
        self.engine = create_engine(
            db_url,
            echo=settings.database_echo,
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self.alembic_cfg = Config()
        migrations_path = Path(__file__).parent.parent.parent / "migrations"
        self.alembic_cfg.set_main_option("script_location", str(migrations_path))
        self.alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    def load_all_models(self) -> None:
        """Dynamically import all models from the models directory"""
        models_path = Path(__file__).parent / "models"
        for module_info in pkgutil.iter_modules([str(models_path)]):
            if not module_info.name.startswith("_"):
                importlib.import_module(f"src.database.models.{module_info.name}")

    def create_all(self) -> None:
        """Create tables only if they don't exist"""
        self.load_all_models()
        Base.metadata.create_all(bind=self.engine, checkfirst=True)

    @contextmanager
    def get_session(self) -> Generator[Session, Any, None]:
        """Get a database session"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def emit_db_event(
        self,
        operation: str,
        model: str,
        data: dict,
        success: bool,
        error: Exception = None,
    ) -> None:
        """Emit a database event"""
        event = DatabaseEvent(
            operation=operation, model=model, data=data, success=success, error=error
        )
        await events.emit(event)


# Global database instance
db = DatabaseManager()
