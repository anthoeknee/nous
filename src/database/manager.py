from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from typing import Generator, Any
from src.events import events, DatabaseEvent
from src.config import Settings

Base = declarative_base()

settings = Settings()


class DatabaseManager:
    def __init__(self, db_url: str = settings.database_url):
        self.engine = create_engine(
            db_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            echo=settings.database_echo,
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def create_all(self) -> None:
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)

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
