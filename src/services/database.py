from typing import Optional, Type, TypeVar
from sqlalchemy.orm import Session
from src.services.base import BaseService
from src.database.manager import db
from src.database.models.base import BaseModel
from src.database.repositories.base import BaseRepository
from src.utils.logging import logger

T = TypeVar("T", bound=BaseModel)


class DatabaseService(BaseService):
    def __init__(self):
        self.db = db
        self._repositories = {}

    async def initialize(self) -> None:
        """Initialize database connection and create tables"""
        try:
            # Load all models and create tables
            self.db.load_all_models()
            self.db.create_all()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """Cleanup database connections"""
        # Currently, SQLAlchemy handles connection cleanup automatically
        # But we can add any additional cleanup logic here if needed
        pass

    def get_session(self) -> Session:
        """Get a database session"""
        return self.db.SessionLocal()

    def register_repository(self, name: str, repository: BaseRepository) -> None:
        """Register a repository"""
        if name in self._repositories:
            raise ValueError(f"Repository {name} already registered")
        self._repositories[name] = repository
        logger.info(f"Registered repository: {name}")

    def get_repository(self, name: str) -> BaseRepository:
        """Get a repository by name"""
        if name not in self._repositories:
            raise KeyError(f"Repository {name} not found")
        return self._repositories[name]

    async def execute_in_transaction(self, callback, *args, **kwargs):
        """Execute a callback within a database transaction"""
        with self.db.get_session() as session:
            try:
                result = await callback(session, *args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Transaction failed: {str(e)}")
                raise

    async def get_by_id(self, model: Type[T], id: int) -> Optional[T]:
        """Get a model instance by ID"""
        with self.db.get_session() as session:
            return session.query(model).filter_by(id=id).first()

    async def create(self, model: Type[T], **kwargs) -> T:
        """Create a new model instance"""
        with self.db.get_session() as session:
            instance = model(**kwargs)
            session.add(instance)
            session.commit()
            session.refresh(instance)
            return instance

    async def update(self, model: Type[T], id: int, **kwargs) -> Optional[T]:
        """Update a model instance"""
        with self.db.get_session() as session:
            instance = session.query(model).filter_by(id=id).first()
            if instance:
                for key, value in kwargs.items():
                    setattr(instance, key, value)
                session.commit()
                session.refresh(instance)
            return instance

    async def delete(self, model: Type[T], id: int) -> bool:
        """Delete a model instance"""
        with self.db.get_session() as session:
            instance = session.query(model).filter_by(id=id).first()
            if instance:
                session.delete(instance)
                session.commit()
                return True
            return False
