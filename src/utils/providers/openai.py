import httpx
from typing import Any, Dict, List, Optional, Union
from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    def __init__(
        self,
        api_key: str,
        identifier: str = "default",
        base_url: str = "https://api.openai.com/v1",
        organization: Optional[str] = None,
    ):
        super().__init__(identifier)
        self.api_key = api_key
        self.base_url = base_url

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if organization:
            headers["OpenAI-Organization"] = organization

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
        )

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str = "gpt-4-turbo-preview",
        temperature: float = 1.0,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            **kwargs,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice or "auto"

        async with self.client as client:
            response = await client.post("/chat/completions", json=payload)
            response.raise_for_status()
            return response.json()

    async def create_embeddings(
        self,
        input: Union[str, List[str]],
        model: str = "text-embedding-3-small",
        encoding_format: str = "float",
        **kwargs,
    ) -> Dict[str, Any]:
        """Create embeddings for the provided text(s)."""
        payload = {
            "input": input,
            "model": model,
            "encoding_format": encoding_format,
            **kwargs,
        }

        async with self.client as client:
            response = await client.post("/embeddings", json=payload)
            response.raise_for_status()
            return response.json()

    async def close(self):
        """Close the HTTP client session."""
        await self.client.aclose()
