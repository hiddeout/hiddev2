import platform
import random
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

class General(commands.Cog, name="general"):
    def __init__(self, bot):
        self.bot = bot
        self.context_menu_user = app_commands.ContextMenu(
            name="Grab ID", callback=self.grab_id
        )
        self.bot.tree.add_command(self.context_menu_user)
        self.context_menu_message = app_commands.ContextMenu(
            name="Remove spoilers", callback=self.remove_spoilers
        )
        self.bot.tree.add_command(self.context_menu_message)

    async def grab_id(self, interaction: discord.Interaction, user: discord.User) -> None:
        embed = discord.Embed(
            description=f"The ID of {user.mention} is `{user.id}`.",
            color=0xBEBEFE,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def remove_spoilers(self, interaction: discord.Interaction, message: discord.Message) -> None:
        spoiler_free_content = message.content.replace("||", "")
        embed = discord.Embed(
            title="Message without spoilers",
            description=spoiler_free_content,
            color=0xBEBEFE,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)





async def setup(bot):
    await bot.add_cog(General(bot))
