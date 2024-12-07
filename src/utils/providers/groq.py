import base64
import httpx
from typing import Any, Dict, List, Optional, Union, BinaryIO
from .base import BaseProvider
import logging
import json

logger = logging.getLogger(__name__)


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

    def prepare_multimodal_content(
        self,
        content: Union[str, List[Dict[str, Any]]],
        multimodal_input: Optional[List[Union[str, bytes]]] = None,
        model: str = "llama-3.3-70b-versatile",
    ) -> Union[str, List[Dict[str, Any]]]:
        """
        Prepare multimodal content, ensuring compatibility with Groq's API.
        """
        # Extremely verbose logging
        logger.info("=" * 50)
        logger.info("MULTIMODAL CONTENT PREPARATION")
        logger.info("=" * 50)

        # Validate inputs
        if multimodal_input is None:
            logger.warning("No multimodal input provided")
            return content if isinstance(content, str) else content[0]["text"]

        # Validate each image
        valid_images = []
        for i, img in enumerate(multimodal_input):
            try:
                # Validate image is bytes and has content
                if not isinstance(img, bytes):
                    logger.error(f"Image {i} is not bytes type: {type(img)}")
                    continue

                if len(img) == 0:
                    logger.error(f"Image {i} is empty")
                    continue

                # Attempt base64 encoding
                try:
                    base64_image = base64.b64encode(img).decode("utf-8")
                    valid_images.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        }
                    )
                    logger.info(f"Successfully processed image {i}")
                except Exception as encode_err:
                    logger.error(
                        f"Base64 encoding failed for image {i}: {str(encode_err)}"
                    )

            except Exception as e:
                logger.error(f"Error processing image {i}: {str(e)}")

        # Prepare base content
        if isinstance(content, str):
            base_content = [{"type": "text", "text": content}]
        elif isinstance(content, list):
            base_content = content
        else:
            base_content = [{"type": "text", "text": str(content)}]

        # Combine base content with images
        multimodal_content = base_content + valid_images

        logger.info("Final multimodal content structure:")
        logger.info(f"  Base content items: {len(base_content)}")
        logger.info(f"  Image items: {len(valid_images)}")
        logger.info(f"  Total items: {len(multimodal_content)}")

        # Return multimodal content for vision models
        return multimodal_content

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        multimodal_input: Optional[List[Union[str, bytes]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a chat completion with Groq's API, supporting multimodal input.
        """
        try:
            # Log input details with more verbosity
            logger.info("Chat Completion Request:")
            logger.info(f"Model: {model}")
            logger.info(f"Number of messages: {len(messages)}")
            logger.info(
                f"Multimodal input count: {len(multimodal_input) if multimodal_input else 0}"
            )

            # Modify the last message to support multimodal content
            if messages and multimodal_input:
                last_message = messages[-1]
                last_message["content"] = self.prepare_multimodal_content(
                    last_message.get("content", ""), multimodal_input, model=model
                )

                # Log the modified content in detail
                logger.info("Modified message content:")
                logger.info(json.dumps(last_message["content"], indent=2))

            # Prepare payload with exact API specification
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }

            # Add optional parameters
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens

            # Add any additional kwargs
            payload.update(kwargs)

            # Log full payload
            logger.info("Full API Payload:")
            logger.info(json.dumps(payload, indent=2))

            async with self.client as client:
                response = await client.post(
                    "/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                # Log raw response
                logger.info("Raw API Response:")
                logger.info(response.text)

                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            logger.error(f"Response content: {http_err.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in chat_completion: {str(e)}")
            raise

    async def close(self):
        """Close the HTTP client session."""
        await self.client.aclose()

    async def transcribe(
        self,
        file: Union[str, BinaryIO],
        model: str = "whisper-large-v3-turbo",
        prompt: Optional[str] = None,
        response_format: str = "json",
        language: Optional[str] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text using Groq's Whisper models.

        Args:
            file: Path to audio file or file-like object
            model: Whisper model to use
            prompt: Optional context or spelling guidance
            response_format: Response format (json, text, srt, etc.)
            language: Optional ISO language code
            temperature: Sampling temperature
        """
        data = {}
        files = {}

        # Handle file input
        if isinstance(file, str):
            files["file"] = ("audio.mp3", open(file, "rb"))
        else:
            files["file"] = ("audio.mp3", file)

        # Add optional parameters
        data["model"] = model
        if prompt:
            data["prompt"] = prompt
        if response_format:
            data["response_format"] = response_format
        if language:
            data["language"] = language
        if temperature is not None:
            data["temperature"] = temperature

        async with self.client as client:
            response = await client.post(
                "/audio/transcriptions", data=data, files=files
            )
            response.raise_for_status()
            return response.json()

    async def translate(
        self,
        file: Union[str, BinaryIO],
        model: str = "whisper-large-v3",
        prompt: Optional[str] = None,
        response_format: str = "json",
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Translate audio directly to English text using Groq's Whisper models.

        Args:
            file: Path to audio file or file-like object
            model: Whisper model to use
            prompt: Optional context or spelling guidance
            response_format: Response format (json, text, srt, etc.)
            temperature: Sampling temperature
        """
        data = {}
        files = {}

        # Handle file input
        if isinstance(file, str):
            files["file"] = ("audio.mp3", open(file, "rb"))
        else:
            files["file"] = ("audio.mp3", file)

        # Add optional parameters
        data["model"] = model
        if prompt:
            data["prompt"] = prompt
        if response_format:
            data["response_format"] = response_format
        if temperature is not None:
            data["temperature"] = temperature

        async with self.client as client:
            response = await client.post("/audio/translations", data=data, files=files)
            response.raise_for_status()
            return response.json()

    async def moderate(
        self,
        input: Union[str, List[str]],
        model: str = "llama-guard-3-8b",
    ) -> Dict[str, Any]:
        """
        Check content against Groq's moderation model (llama-guard).
        The model automatically detects 14 harmful categories (S1-S14).

        Args:
            input: String or list of strings to moderate
            model: Model to use for moderation (default: llama-guard-3-8b)

        Returns:
            Dict containing moderation results
        """
        try:
            # Convert single string to list for consistent handling
            if isinstance(input, str):
                input = [input]

            # Prepare messages for each input string
            messages = [{"role": "user", "content": text} for text in input]

            # Use chat completion with llama-guard model
            response = await self.chat_completion(
                messages=messages,
                model=model,
                temperature=0.0,  # Use deterministic output for moderation
            )

            return response

        except Exception as e:
            logger.error(f"Error in moderation: {str(e)}")
            raise
