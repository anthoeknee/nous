from discord.ext import commands
from discord import app_commands
from src.utils.logging import logger
from src.storage.repositories.settings import SettingRepository
from src.storage.repositories.permissions import PermissionRepository
from src.utils.permissions import has_permission
from typing import Optional


class SettingsFeature(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings_repo = SettingRepository()
        self.permissions_repo = PermissionRepository()
        logger.info("Settings feature initialized")

    @commands.hybrid_group(name="settings")
    @app_commands.default_permissions(administrator=True)
    async def settings(self, ctx: commands.Context):
        """Manage bot settings"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Please specify a settings subcommand.")

    @settings.command(name="set")
    @app_commands.describe(
        key="The setting key to modify",
        value="The new value",
        scope="The scope of the setting (global/guild/channel/user/role)",
        scope_id="The ID for the scope (if not global)",
        category="The category of the setting (owner/general)",
    )
    async def set_setting(
        self,
        ctx: commands.Context,
        key: str,
        value: str,
        scope: str = "global",
        scope_id: Optional[int] = None,
        category: str = "general",
    ):
        """Set a bot setting"""
        # Check permissions
        if category == "owner" and ctx.author.id != self.bot.owner_id:
            await ctx.send("Only the bot owner can modify owner settings!")
            return

        if not await has_permission(ctx, "manage_settings"):
            await ctx.send("You don't have permission to manage settings!")
            return

        try:
            await self.settings_repo.set_setting(
                key=key, value=value, scope=scope, scope_id=scope_id, category=category
            )
            await ctx.send(f"Setting `{key}` updated successfully!")
        except Exception as e:
            await ctx.send(f"Error updating setting: {str(e)}")

    @settings.command(name="get")
    async def get_setting(
        self,
        ctx: commands.Context,
        key: str,
        scope: str = "global",
        scope_id: Optional[int] = None,
    ):
        """Get a bot setting"""
        try:
            setting = await self.settings_repo.get_setting(key, scope, scope_id)
            if setting:
                await ctx.send(f"Setting `{key}`: `{setting.value}`")
            else:
                await ctx.send(f"Setting `{key}` not found.")
        except Exception as e:
            await ctx.send(f"Error retrieving setting: {str(e)}")

    @settings.command(name="list")
    async def list_settings(
        self,
        ctx: commands.Context,
        scope: str = "global",
        scope_id: Optional[int] = None,
    ):
        """List all settings for the given scope"""
        try:
            settings = await self.settings_repo.get_settings(scope, scope_id)
            if not settings:
                await ctx.send("No settings found.")
                return

            # Format settings list
            settings_list = "\n".join(
                f"`{s.key}` = `{s.value}` ({s.category})" for s in settings
            )
            await ctx.send(f"Settings:\n{settings_list}")
        except Exception as e:
            await ctx.send(f"Error listing settings: {str(e)}")


async def setup(bot: commands.Bot):
    await bot.add_cog(SettingsFeature(bot))
