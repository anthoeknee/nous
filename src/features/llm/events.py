from discord import Message
import logging

logger = logging.getLogger(__name__)


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

        # Detailed logging for attachments
        logger.info(f"Total attachments: {len(message.attachments)}")
        for i, attachment in enumerate(message.attachments):
            logger.info(f"Attachment {i}:")
            logger.info(f"  Filename: {attachment.filename}")
            logger.info(f"  Content Type: {attachment.content_type}")
            logger.info(f"  Size: {attachment.size} bytes")
            logger.info(f"  URL: {attachment.url}")

        # Collect image attachments with error handling
        image_attachments = []
        for attachment in message.attachments:
            try:
                if attachment.content_type.startswith("image/"):
                    image_bytes = await attachment.read()
                    logger.info(f"Successfully read image: {attachment.filename}")
                    logger.info(f"Image bytes length: {len(image_bytes)}")
                    image_attachments.append(image_bytes)
            except Exception as e:
                logger.error(
                    f"Error reading attachment {attachment.filename}: {str(e)}"
                )

        # If there are images or text content, process the message
        if content or image_attachments:
            await self.bot.llm_handler.handle_message(
                message, content, image_attachments
            )
