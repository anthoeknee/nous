from typing import Dict
from src.services.base import BaseService
from src.utils.providers import ProviderFactory
from src.config import conf

settings = conf()


class AIProviderService(BaseService):
    def __init__(self):
        self.providers: Dict[str, any] = {}

    async def initialize(self) -> None:
        """Initialize AI providers"""
        # Initialize OpenAI provider
        self.providers["openai"] = ProviderFactory.create_provider(
            "openai", api_key=settings.openai_api_key, identifier="default"
        )

        # Initialize Groq provider
        self.providers["groq"] = ProviderFactory.create_provider(
            "groq", api_key=settings.groq_api_key, identifier="default"
        )

    async def cleanup(self) -> None:
        """Cleanup provider connections"""
        for provider in self.providers.values():
            await provider.close()

    def get_provider(self, name: str) -> any:
        """Get a provider by name"""
        if name not in self.providers:
            raise KeyError(f"Provider {name} not found")
        return self.providers[name]
