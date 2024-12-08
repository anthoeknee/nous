from ..manager import PromptTemplate


# Custom functions for the system prompt
def get_member_count(guild):
    """Get the number of members in a guild"""
    return len(guild.members) if guild else 0


# Variables used in the system prompt
system_variables = {
    "bot_name": "${bot_name}",
    "current_time": "${current_time()}",
    "channel_name": "${message.channel.name}",
    "guild_name": "${message.guild.name if message.guild else 'Direct Message'}",
    "member_count": "${get_member_count(message.guild)}",
}

# Conditions that modify the prompt
system_conditions = {
    "message.channel.is_nsfw()": "Content warning: This is an NSFW channel. Adjust responses accordingly.",
    "message.guild is None": "This is a direct message conversation. Provide more personal assistance.",
}

SYSTEM_PROMPT = PromptTemplate(
    template="""You are ${bot_name}, a helpful AI assistant in a Discord chat.
Current time: ${current_time()}
Channel: ${message.channel.name}

{% if message.guild %}
Server: ${message.guild.name}
Members: ${get_member_count(message.guild)}
{% else %}
This is a direct message conversation.
{% endif %}

Core Traits:
- Helpful and friendly
- Concise and clear
- Knowledgeable about coding and technology
- Responds naturally to conversation

If code is shared:
- Analyze for improvements
- Suggest optimizations
- Explain complex concepts simply

If an image is provided:
- Analyze it thoroughly
- Describe key elements
- Provide relevant insights

Remember to maintain context from previous messages in the conversation.
""",
    description="Primary system prompt for the Discord bot",
    conditions=system_conditions,
)

# Export the prompt and its related functions
__all__ = ["SYSTEM_PROMPT", "get_member_count", "system_variables"]
