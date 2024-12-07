import discord
from discord import app_commands
from discord.ext import commands
from src.utils.logging import logger


class BlocklistFeature(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Blocklist feature initialized")

    @app_commands.command(name="blocklist")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def blocklist_root(self, interaction: discord.Interaction):
        """View blocklist management commands"""
        await interaction.response.send_message(
            "Use `/blocklist_add`, `/blocklist_remove`, or `/blocklist_list` to manage the blocklist.",
            ephemeral=True,
        )

    @app_commands.command(name="blocklist_add")
    @app_commands.describe(
        target_type="Type of target to block (user/channel/guild)",
        target_id="ID of the target to block",
    )
    @app_commands.choices(
        target_type=[
            app_commands.Choice(name="User", value="user"),
            app_commands.Choice(name="Channel", value="channel"),
            app_commands.Choice(name="Guild", value="guild"),
        ]
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def blocklist_add(
        self, interaction: discord.Interaction, target_type: str, target_id: str
    ):
        """Add a user, channel, or guild to the blocklist"""
        try:
            target_id = int(target_id)
        except ValueError:
            await interaction.response.send_message(
                "Invalid ID format. Please provide a valid numeric ID.", ephemeral=True
            )
            return

        setting_key = f"blocked_{target_type}s"
        current_setting = await self.bot.settings_repo.get_setting(
            key=setting_key, scope="global", category="blocklist"
        )

        blocked_ids = current_setting.value if current_setting else []
        if target_id not in blocked_ids:
            blocked_ids.append(target_id)
            await self.bot.settings_repo.set_setting(
                key=setting_key, value=blocked_ids, scope="global", category="blocklist"
            )
            await interaction.response.send_message(
                f"{target_type.capitalize()} {target_id} has been blocked.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"{target_type.capitalize()} {target_id} is already blocked.",
                ephemeral=True,
            )

    @app_commands.command(name="blocklist_remove")
    @app_commands.describe(
        target_type="Type of target to unblock (user/channel/guild)",
        target_id="ID of the target to unblock",
    )
    @app_commands.choices(
        target_type=[
            app_commands.Choice(name="User", value="user"),
            app_commands.Choice(name="Channel", value="channel"),
            app_commands.Choice(name="Guild", value="guild"),
        ]
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def blocklist_remove(
        self, interaction: discord.Interaction, target_type: str, target_id: str
    ):
        """Remove a user, channel, or guild from the blocklist"""
        try:
            target_id = int(target_id)
        except ValueError:
            await interaction.response.send_message(
                "Invalid ID format. Please provide a valid numeric ID.", ephemeral=True
            )
            return

        setting_key = f"blocked_{target_type}s"
        current_setting = await self.bot.settings_repo.get_setting(
            key=setting_key, scope="global", category="blocklist"
        )

        if current_setting and target_id in current_setting.value:
            blocked_ids = current_setting.value
            blocked_ids.remove(target_id)
            await self.bot.settings_repo.set_setting(
                key=setting_key, value=blocked_ids, scope="global", category="blocklist"
            )
            await interaction.response.send_message(
                f"{target_type.capitalize()} {target_id} has been unblocked.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"{target_type.capitalize()} {target_id} is not blocked.",
                ephemeral=True,
            )

    @app_commands.command(name="blocklist_list")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def blocklist_list(self, interaction: discord.Interaction):
        """List all blocked users, channels, and guilds"""
        blocked_users = await self.bot.settings_repo.get_setting(
            key="blocked_users", scope="global", category="blocklist"
        )
        blocked_channels = await self.bot.settings_repo.get_setting(
            key="blocked_channels", scope="global", category="blocklist"
        )
        blocked_guilds = await self.bot.settings_repo.get_setting(
            key="blocked_guilds", scope="global", category="blocklist"
        )

        embed = discord.Embed(title="Current Blocklist", color=discord.Color.blue())
        embed.add_field(
            name="Blocked Users",
            value=str(blocked_users.value if blocked_users else []),
            inline=False,
        )
        embed.add_field(
            name="Blocked Channels",
            value=str(blocked_channels.value if blocked_channels else []),
            inline=False,
        )
        embed.add_field(
            name="Blocked Guilds",
            value=str(blocked_guilds.value if blocked_guilds else []),
            inline=False,
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(BlocklistFeature(bot))
