from discord import Message


class EventHandler:
    def __init__(self, bot):
        self.bot = bot

    async def should_respond(self, message: Message) -> bool:
        """Determine if the bot should respond to a message."""
        # Don't respond to our own messages
        if message.author == self.bot.user:
            return False

        # Respond to DMs
        if message.guild is None:
            return True

        # Respond if the bot is mentioned
        if self.bot.user.mentioned_in(message):
            return True

        # Respond if the message is a reply to one of our messages
        if message.reference and message.reference.resolved:
            referenced_msg = message.reference.resolved
            if referenced_msg.author == self.bot.user:
                return True

        return False

    async def on_message(self, message: Message):
        """Handle incoming messages."""
        if not await self.should_respond(message):
            return

        # Remove bot mention from the message content
        content = message.content
        if self.bot.user.mentioned_in(message):
            content = content.replace(f"<@{self.bot.user.id}>", "").strip()

        await self.bot.llm_handler.handle_message(message, content)
