from typing import Optional, Dict
from .base import BaseProvider
from .groq import GroqProvider
from .openai import OpenAIProvider


class ProviderFactory:
    _instances: Dict[str, BaseProvider] = {}

    @classmethod
    def create_provider(
        cls,
        provider_name: str,
        api_key: str,
        identifier: str = "default",
        base_url: Optional[str] = None,
        **kwargs,
    ) -> BaseProvider:
        # Create a unique key for the instance
        instance_key = f"{provider_name}_{identifier}"

        # Return existing instance if it exists
        if instance_key in cls._instances:
            return cls._instances[instance_key]

        # Create new instance
        if provider_name.lower() == "groq":
            provider = GroqProvider(
                api_key=api_key,
                identifier=identifier,
                base_url=base_url or "https://api.groq.com/openai/v1",
            )
        elif provider_name.lower() == "openai":
            provider = OpenAIProvider(
                api_key=api_key,
                identifier=identifier,
                base_url=base_url or "https://api.openai.com/v1",
                organization=kwargs.get("organization"),
            )
        else:
            raise ValueError(f"Unsupported provider: {provider_name}")

        # Store and return the new instance
        cls._instances[instance_key] = provider
        return provider

    @classmethod
    def get_provider(
        cls, provider_name: str, identifier: str = "default"
    ) -> Optional[BaseProvider]:
        """Retrieve an existing provider instance by name and identifier."""
        instance_key = f"{provider_name}_{identifier}"
        return cls._instances.get(instance_key)

    @classmethod
    def list_providers(cls) -> Dict[str, str]:
        """List all active provider instances and their identifiers."""
        return {key: provider.identifier for key, provider in cls._instances.items()}

    @classmethod
    def remove_provider(cls, provider_name: str, identifier: str = "default") -> bool:
        """Remove a provider instance from the factory."""
        instance_key = f"{provider_name}_{identifier}"
        if instance_key in cls._instances:
            del cls._instances[instance_key]
            return True
        return False
