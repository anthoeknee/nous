from discord import Message
from src.utils.providers import ProviderFactory
from .memory.short_term import ShortTermMemory
from src.utils.logging import logger
from typing import Optional, List
from .prompts.manager import PromptManager, PromptTemplate
import asyncio
from .prompts.templates.system_prompt import SYSTEM_PROMPT, get_member_count


class LLMHandler:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.memory = ShortTermMemory()
        self.prompt_manager = PromptManager()
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 3

        # Initialize default system prompt
        asyncio.create_task(self._init_default_prompt())

    async def _init_default_prompt(self):
        # Add the system prompt's custom functions
        self.prompt_manager.add_function("get_member_count", get_member_count)

        # Save the system prompt
        await self.prompt_manager.save_prompt("system", SYSTEM_PROMPT)

    async def _ensure_provider(self):
        """Create a new provider instance for each request"""
        try:
            logger.info("Creating new Groq provider")
            return ProviderFactory.create_provider("groq", self.api_key)
        except Exception as e:
            logger.error(f"Provider connection error: {str(e)}")
            self._reconnect_attempts += 1
            if self._reconnect_attempts >= self._max_reconnect_attempts:
                raise Exception("Failed to connect after multiple attempts")
            return None

    async def handle_message(
        self,
        message: Message,
        content: str,
        image_attachments: Optional[List[bytes]] = None,
    ):
        """Handle an incoming message that requires an LLM response."""
        try:
            # Extensive logging for image attachments
            logger.info("Handle Message - Image Attachments:")
            if image_attachments:
                logger.info(f"Number of image attachments: {len(image_attachments)}")
                for i, img in enumerate(image_attachments):
                    logger.info(f"Image {i}:")
                    logger.info(f"  Type: {type(img)}")
                    logger.info(f"  Length: {len(img)} bytes")
            else:
                logger.info("No image attachments received")

            # Reset reconnect attempts
            self._reconnect_attempts = 0

            while self._reconnect_attempts < self._max_reconnect_attempts:
                provider = None
                try:
                    # Create a new provider for each attempt
                    provider = await self._ensure_provider()
                    if not provider:
                        await message.reply(
                            "Attempting to reconnect, please try again in a moment."
                        )
                        return

                    logger.info(f"Processing message in channel {message.channel.id}")

                    # Get conversation history
                    conversation_history = await self.memory.get_context(
                        str(message.channel.id)
                    )

                    # Prepare system prompt with context
                    system_prompt = await self.prompt_manager.render_prompt(
                        "system",
                        variables={
                            "channel_specific": f"Channel: #{message.channel.name}"
                            if message.guild
                            else "DM Channel",
                            "guild_name": message.guild.name
                            if message.guild
                            else "Direct Message",
                        },
                        context={"message": message},
                    )

                    # Prepare messages for the LLM
                    messages = [
                        {
                            "role": "system",
                            "content": system_prompt
                            or "You are a helpful AI assistant.",
                        }
                    ]

                    # Add conversation history
                    for msg in conversation_history:
                        messages.append(msg)

                    # Add current message
                    messages.append({"role": "user", "content": content})

                    logger.info("Sending request to Groq API")
                    # Get response from LLM with multimodal support
                    response = await provider.chat_completion(
                        messages=messages,
                        temperature=0.7,
                        multimodal_input=image_attachments,
                        model="llama-3.3-70b-versatile",  # Specific vision model
                    )

                    # Extract the response content
                    assistant_message = response["choices"][0]["message"]

                    logger.info("Successfully processed message")
                    # Store the interaction in memory
                    await self.memory.add_message(
                        str(message.channel.id), {"role": "user", "content": content}
                    )
                    await self.memory.add_message(
                        str(message.channel.id), assistant_message
                    )

                    # Send the response
                    await message.reply(assistant_message["content"])

                    # Break the retry loop on successful completion
                    break

                except Exception as inner_e:
                    self._reconnect_attempts += 1
                    logger.warning(
                        f"Attempt {self._reconnect_attempts} failed: {str(inner_e)}"
                    )

                    # If this was the last attempt, re-raise the exception
                    if self._reconnect_attempts >= self._max_reconnect_attempts:
                        raise

                finally:
                    # Ensure provider is closed in each iteration
                    if provider:
                        try:
                            await provider.close()
                        except Exception as close_e:
                            logger.error(f"Error closing provider: {close_e}")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in handle_message: {error_msg}")
            await message.reply(f"Sorry, I encountered an error: {error_msg}")
