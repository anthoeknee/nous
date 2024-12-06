from discord import Message
from src.utils.providers import ProviderFactory
from .memory.short_term import ShortTermMemory


class LLMHandler:
    def __init__(self, api_key: str):
        self.provider = ProviderFactory.create_provider("groq", api_key)
        self.memory = ShortTermMemory()

    async def handle_message(self, message: Message, content: str):
        """Handle an incoming message that requires an LLM response."""
        # Get conversation context
        context = self.memory.get_context(str(message.channel.id))

        # Prepare messages for the LLM
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant in a Discord chat. Be concise and friendly in your responses.",
            }
        ]

        # Add context messages
        for ctx_msg in context:
            messages.append(ctx_msg)

        # Add the current message
        messages.append({"role": "user", "content": content})

        try:
            # Get response from LLM
            response = await self.provider.chat_completion(
                messages=messages, temperature=0.7
            )

            # Extract the response content
            assistant_message = response["choices"][0]["message"]

            # Store the interaction in memory
            self.memory.add_message(
                str(message.channel.id), {"role": "user", "content": content}
            )
            self.memory.add_message(str(message.channel.id), assistant_message)

            # Send the response
            await message.reply(assistant_message["content"])

        except Exception as e:
            await message.reply(f"Sorry, I encountered an error: {str(e)}")
