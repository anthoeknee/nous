from discord.ext import commands
from discord import Message, TextChannel
import re
from typing import List
from src.utils.logging import logger
from src.utils.providers import ProviderFactory
from src.config import settings


class SummaryFeature(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.max_chunk_size = 4000  # Safe limit for Groq
        self.min_messages = 5  # Minimum messages needed for summary
        self.api_key = settings.groq_api_key
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 3
        logger.info("Summary feature initialized")

    async def _ensure_provider(self):
        """Create a new provider instance for each request"""
        try:
            logger.info("Creating new Groq provider for summary")
            return ProviderFactory.create_provider("groq", self.api_key)
        except Exception as e:
            logger.error(f"Provider connection error: {str(e)}")
            self._reconnect_attempts += 1
            if self._reconnect_attempts >= self._max_reconnect_attempts:
                raise Exception("Failed to connect after multiple attempts")
            return None

    @commands.command(name="summarize")
    async def summarize(self, ctx: commands.Context, message_count: int = 50):
        """Summarize recent messages in the channel"""
        if message_count < self.min_messages:
            await ctx.send(
                f"Please request at least {self.min_messages} messages to summarize."
            )
            return

        async with ctx.typing():
            messages = await self._fetch_messages(ctx.channel, message_count)
            if not messages:
                await ctx.send("No messages found to summarize.")
                return

            chunks = self._prepare_messages(messages)
            summary = await self._generate_summary(chunks)
            await ctx.send(summary)

    async def _fetch_messages(self, channel: TextChannel, limit: int) -> List[Message]:
        """Fetch messages from the channel"""
        try:
            messages = []
            async for msg in channel.history(limit=limit):
                if (
                    not msg.author.bot and msg.content.strip()
                ):  # Skip bot messages and empty content
                    messages.append(msg)
            return messages[::-1]  # Reverse to get chronological order
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return []

    def _prepare_messages(self, messages: List[Message]) -> List[str]:
        """Prepare messages for summarization"""
        chunks = []
        current_chunk = []
        current_length = 0

        for msg in messages:
            # Format: Username: Message
            formatted_msg = f"{msg.author.display_name}: {msg.content}\n"
            msg_length = len(formatted_msg)

            if current_length + msg_length > self.max_chunk_size:
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                current_chunk = [formatted_msg]
                current_length = msg_length
            else:
                current_chunk.append(formatted_msg)
                current_length += msg_length

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    async def _generate_summary(self, chunks: List[str]) -> str:
        """Generate summary using Groq"""
        self._reconnect_attempts = 0

        while self._reconnect_attempts < self._max_reconnect_attempts:
            provider = None
            try:
                provider = await self._ensure_provider()
                if not provider:
                    return "Failed to connect to AI provider, please try again."

                # First, get individual summaries for each chunk
                chunk_summaries = []
                for chunk in chunks:
                    messages = [
                        {
                            "role": "system",
                            "content": "You are a concise summarizer. Create a brief, bullet-point summary of the key points in this conversation.",
                        },
                        {
                            "role": "user",
                            "content": f"Summarize this conversation:\n{chunk}",
                        },
                    ]

                    response = await provider.chat_completion(
                        messages=messages,
                        temperature=0.7,
                        model="llama-3.3-70b-versatile",
                    )

                    chunk_summaries.append(response["choices"][0]["message"]["content"])

                # If we have multiple chunks, create a final summary
                if len(chunk_summaries) > 1:
                    final_messages = [
                        {
                            "role": "system",
                            "content": "Create a cohesive, bullet-point summary combining these conversation summaries.",
                        },
                        {
                            "role": "user",
                            "content": f"Combine these summaries:\n{''.join(chunk_summaries)}",
                        },
                    ]

                    final_response = await provider.chat_completion(
                        messages=final_messages,
                        temperature=0.7,
                        model="llama-3.3-70b-versatile",
                    )

                    return final_response["choices"][0]["message"]["content"]

                return chunk_summaries[0]

            except Exception as e:
                self._reconnect_attempts += 1
                logger.warning(f"Attempt {self._reconnect_attempts} failed: {str(e)}")
                if self._reconnect_attempts >= self._max_reconnect_attempts:
                    raise
            finally:
                if provider:
                    try:
                        await provider.close()
                    except Exception as close_e:
                        logger.error(f"Error closing provider: {close_e}")

        return "Failed to generate summary after multiple attempts."


async def setup(bot: commands.Bot):
    await bot.add_cog(SummaryFeature(bot))
