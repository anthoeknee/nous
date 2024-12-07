from abc import ABC, abstractmethod
from typing import Any


class BaseService(ABC):
    """Base class for all services"""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup service resources"""
        pass

    async def __aenter__(self) -> Any:
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.cleanup()
