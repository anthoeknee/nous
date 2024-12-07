from typing import Dict, Type, TypeVar
from src.services.base import BaseService
from src.utils.logging import logger

T = TypeVar("T", bound=BaseService)


class ServiceManager:
    def __init__(self):
        self._services: Dict[str, BaseService] = {}

    def register(self, name: str, service: BaseService) -> None:
        """Register a new service"""
        if name in self._services:
            raise ValueError(f"Service {name} already registered")
        self._services[name] = service
        logger.info(f"Registered service: {name}")

    def get(self, name: str, service_type: Type[T] = BaseService) -> T:
        """Get a service by name"""
        service = self._services.get(name)
        if not service:
            raise KeyError(f"Service {name} not found")
        if not isinstance(service, service_type):
            raise TypeError(f"Service {name} is not of type {service_type.__name__}")
        return service

    async def initialize_all(self) -> None:
        """Initialize all registered services"""
        for name, service in self._services.items():
            try:
                await service.initialize()
                logger.info(f"Initialized service: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize service {name}: {str(e)}")
                raise

    async def cleanup_all(self) -> None:
        """Cleanup all registered services"""
        for name, service in self._services.items():
            try:
                await service.cleanup()
                logger.info(f"Cleaned up service: {name}")
            except Exception as e:
                logger.error(f"Failed to cleanup service {name}: {str(e)}")
