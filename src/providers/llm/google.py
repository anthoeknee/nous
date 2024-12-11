import google.generativeai as genai
from typing import Any, Dict, List, Optional, Union, BinaryIO
from .base import BaseProvider
import logging
from io import BytesIO
import magic
import time
import asyncio
from google.generativeai.types import HarmCategory, HarmBlockThreshold

logger = logging.getLogger(__name__)


class GoogleProvider(BaseProvider):
    def __init__(
        self,
        api_key: str,
        identifier: str = "default",
        base_url: str = "https://generativelanguage.googleapis.com/v1",
    ):
        super().__init__(identifier)
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-exp-1206")
        self.vision_model = genai.GenerativeModel("gemini-exp-1206")

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str = "gemini-exp-1206",
        temperature: float = 0.9,
        max_tokens: Optional[int] = None,
        multimodal_input: Optional[List[Union[str, bytes, BinaryIO]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate chat completion using Gemini."""
        try:
            # Get the last user message
            last_user_message = next(
                (msg["content"] for msg in reversed(messages) if msg["role"] == "user"),
                "",
            )

            # Prepare content parts
            content_parts = [last_user_message]

            # Handle multimodal input
            if multimodal_input:
                logger.info(f"Processing {len(multimodal_input)} files")
                for file_data in multimodal_input:
                    try:
                        # Create file-like object from bytes
                        file_obj = BytesIO(file_data)

                        # Try to detect MIME type
                        mime_type = magic.from_buffer(file_data, mime=True)
                        logger.info(f"Detected MIME type: {mime_type}")

                        # Upload the file with retries
                        max_retries = 3
                        retry_delay = 2
                        for attempt in range(max_retries):
                            try:
                                uploaded_file = genai.upload_file(
                                    file_obj, mime_type=mime_type
                                )
                                logger.info(f"File uploaded: {uploaded_file.name}")
                                break
                            except Exception as upload_error:
                                if attempt == max_retries - 1:
                                    raise upload_error
                                logger.warning(
                                    f"Upload attempt {attempt + 1} failed, retrying..."
                                )
                                await asyncio.sleep(retry_delay * (attempt + 1))
                                file_obj.seek(0)  # Reset file pointer for retry

                        # Handle processing state for certain file types
                        if mime_type in ["video/mp4", "application/pdf"]:
                            processing_timeout = 60  # 60 seconds timeout
                            start_time = time.time()
                            while uploaded_file.state.name == "PROCESSING":
                                if time.time() - start_time > processing_timeout:
                                    raise TimeoutError("File processing timeout")
                                logger.info("Processing file...")
                                await asyncio.sleep(5)
                                uploaded_file = genai.get_file(uploaded_file.name)

                        content_parts.append(uploaded_file)
                        logger.info("File processed successfully")

                    except Exception as e:
                        logger.error(f"Error processing file: {str(e)}")
                        logger.exception("Full traceback:")
                        # Don't continue with the request if file processing failed
                        raise

            # Generate content with retries
            max_retries = 3
            retry_delay = 2
            last_error = None

            for attempt in range(max_retries):
                try:
                    generation_config = genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens if max_tokens else None,
                    )

                    # Use vision model if there are files, otherwise use text model
                    model_to_use = self.vision_model if multimodal_input else self.model

                    # Set safety settings to block none, excluding unsupported categories
                    safety_settings = {
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
                    }

                    # Generate the response
                    response = model_to_use.generate_content(
                        content_parts,
                        generation_config=generation_config,
                        safety_settings=safety_settings,
                    )

                    # Convert the response to the expected format
                    return {
                        "candidates": [
                            {"content": {"parts": [{"text": response.text}]}}
                        ]
                    }

                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                        await asyncio.sleep(retry_delay * (attempt + 1))
                        continue
                    else:
                        raise last_error

        except Exception as e:
            logger.error(f"Error in chat_completion: {str(e)}")
            logger.exception("Full traceback:")
            raise

    async def close(self):
        """No need to close anything with the official library."""
        pass
