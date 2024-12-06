import base64
import httpx
from typing import Any, Dict, List, Optional, Union
from .base import BaseProvider


class GroqProvider(BaseProvider):
    def __init__(
        self,
        api_key: str,
        identifier: str = "default",
        base_url: str = "https://api.groq.com/openai/v1",
    ):
        super().__init__(identifier)
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=self.base_url, headers={"Authorization": f"Bearer {self.api_key}"}
        )

    @staticmethod
    def encode_image(image_path: str) -> str:
        """Encode a local image file to base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def prepare_image_message(
        self, image_input: Union[str, Dict[str, str]]
    ) -> Dict[str, Any]:
        """Prepare image message content based on input type."""
        if isinstance(image_input, str):
            # If input is a local file path, encode it
            if image_input.startswith(("http://", "https://")):
                return {"type": "image_url", "image_url": {"url": image_input}}
            else:
                base64_image = self.encode_image(image_input)
                return {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                }
        return image_input  # Already formatted image dict

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str = "llama-3.2-11b-vision-preview",
        temperature: float = 1.0,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a chat completion with Groq's API, supporting vision capabilities.

        Args:
            messages: List of message dictionaries. For vision, content should be a list of
                     text and image components
            model: Model ID to use (default: llama-3.2-11b-vision-preview)
            temperature: Sampling temperature (0-2)
            tools: Optional list of tools/functions the model can use
            tool_choice: Controls which tool is called by the model
            **kwargs: Additional parameters to pass to the API
        """
        # Process messages to handle image inputs
        processed_messages = []
        for message in messages:
            if isinstance(message["content"], list):
                # Process each content item in the list
                processed_content = []
                for item in message["content"]:
                    if isinstance(item, dict) and item.get("type") == "image_url":
                        processed_content.append(
                            self.prepare_image_message(item["image_url"]["url"])
                        )
                    else:
                        processed_content.append(item)
                processed_message = {**message, "content": processed_content}
            else:
                processed_message = message
            processed_messages.append(processed_message)

        payload = {
            "model": model,
            "messages": processed_messages,
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

    async def close(self):
        """Close the HTTP client session."""
        await self.client.aclose()
