from discord.ext import commands
import discord
from typing import Optional, List
from src.utils.logging import logger
from datetime import datetime, timedelta
import asyncio


class SummaryFeature(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.llm_handler = bot.llm_handler
        logger.info("Summary feature initialized")

    async def fetch_messages(
        self,
        channel: discord.TextChannel,
        limit: Optional[int] = None,
        before: Optional[datetime] = None,
    ) -> List[discord.Message]:
        """Fetch messages from a channel with pagination support."""
        messages = []
        last_message = None
        fetch_limit = min(100, limit) if limit else 100

        while True:
            try:
                # Determine the before parameter for this batch
                before_param = None
                if before and not last_message:
                    # First iteration with datetime
                    discord_epoch = 1420070400000
                    timestamp = int(before.timestamp() * 1000 - discord_epoch) << 22
                    before_param = discord.Snowflake(timestamp)
                elif last_message:
                    # Use the ID of the last message for subsequent fetches
                    before_param = last_message

                # Fetch batch of messages
                batch = [
                    msg
                    async for msg in channel.history(
                        limit=fetch_limit, before=before_param
                    )
                ]

                if not batch:
                    break

                messages.extend(batch)
                last_message = batch[-1]

                # Check if we've reached the desired limit
                if limit and len(messages) >= limit:
                    messages = messages[:limit]
                    break

                # Add delay to respect rate limits
                await asyncio.sleep(0.5)

            except discord.HTTPException as e:
                logger.error(f"Error fetching messages: {e}")
                raise

        return messages

    def format_messages_for_summary(self, messages: List[discord.Message]) -> str:
        """Format messages for LLM processing."""
        formatted_messages = []
        for msg in messages:
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            formatted_messages.append(f"{timestamp} | {msg.author.name}: {msg.content}")

        return "\n".join(formatted_messages)

    @commands.hybrid_command(name="summarize")
    async def summarize(
        self,
        ctx: commands.Context,
        message_limit: Optional[int] = 100,
        hours: Optional[int] = None,
        detailed: bool = False,
    ):
        """
        Summarize recent messages in the channel.

        Parameters:
        -----------
        message_limit: Optional[int]
            Number of messages to summarize (default: 100)
        hours: Optional[int]
            Summarize messages from the last X hours
        detailed: bool
            If True, provide a more detailed summary
        """
        await ctx.defer()

        try:
            # Calculate time constraint if hours specified
            before = None
            if hours:
                before = datetime.utcnow() - timedelta(hours=hours)

            # Fetch messages
            channel_messages = await self.fetch_messages(
                ctx.channel, limit=message_limit, before=before
            )

            if not channel_messages:
                await ctx.send("No messages found in the specified timeframe.")
                return

            # Format messages for LLM
            formatted_content = self.format_messages_for_summary(channel_messages)

            # Modified LLM interaction
            style = "detailed" if detailed else "concise"
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant. Your task is to summarize Discord conversations clearly and concisely.",
                },
                {
                    "role": "user",
                    "content": f"""Please provide a {style} summary of the following Discord chat conversation.
                    Focus on key discussion points, decisions made, and important interactions.

                    Chat History:
                    {formatted_content}""",
                },
            ]

            # Use handle_message instead of chat_completion
            response = await self.llm_handler.handle_message(
                ctx.message, messages[-1]["content"]
            )

            # Create and send embed
            embed = discord.Embed(
                title="Chat Summary", description=response, color=discord.Color.blue()
            )
            embed.set_footer(text=f"Summarized {len(channel_messages)} messages")

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in summarize command: {e}")
            await ctx.send(f"An error occurred while generating the summary: {str(e)}")


async def setup(bot: commands.Bot):
    await bot.add_cog(SummaryFeature(bot))
