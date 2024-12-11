from typing import Optional
from .base import BaseProvider
from .groq import GroqProvider
from .openai import OpenAIProvider
from .google import GoogleProvider


class ProviderFactory:
    @classmethod
    def create_provider(
        cls,
        provider_name: str,
        api_key: str,
        identifier: str = "default",
        base_url: Optional[str] = None,
        **kwargs,
    ) -> BaseProvider:
        """
        Create a new provider instance based on the provider name.

        Args:
            provider_name: Name of the provider (e.g., 'groq', 'openai')
            api_key: API key for the provider
            identifier: Optional identifier for the provider instance
            base_url: Optional custom base URL for the provider
            **kwargs: Additional provider-specific arguments

        Returns:
            An instance of the specified provider

        Raises:
            ValueError: If an unsupported provider is specified
        """
        # Normalize provider name to lowercase for case-insensitive matching
        provider_name = provider_name.lower()

        # Create provider instances based on name
        if provider_name == "groq":
            return GroqProvider(
                api_key=api_key,
                identifier=identifier,
                base_url=base_url or "https://api.groq.com/openai/v1",
            )
        elif provider_name == "openai":
            return OpenAIProvider(
                api_key=api_key,
                identifier=identifier,
                base_url=base_url or "https://api.openai.com/v1",
                organization=kwargs.get("organization"),
            )
        elif provider_name == "google":
            return GoogleProvider(
                api_key=api_key,
                identifier=identifier,
                base_url=base_url or "https://generativelanguage.googleapis.com/v1beta",
            )
        else:
            # Update supported providers list
            supported_providers = ["groq", "openai", "google"]
            raise ValueError(
                f"Unsupported provider: {provider_name}. "
                f"Supported providers are: {', '.join(supported_providers)}"
            )

    @classmethod
    def get_supported_providers(cls) -> list:
        """
        Return a list of supported provider names.

        Returns:
            List of supported provider names
        """
        return ["groq", "openai", "google"]
