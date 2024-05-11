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










        """  help command is not working
    @commands.hybrid_command(name="help", description="List all commands the bot has loaded.")
    async def help(self, context: Context):
        prefix = self.bot.config["prefix"]
        embed = discord.Embed(title="Help", description="List of available commands:", color=0xBEBEFE)
        
        for cog_name in self.bot.cogs:
            if cog_name.lower() == "events":
                continue
            if cog_name.lower() == "owner" and not (await self.bot.is_owner(context.author)):
                continue

            cog = self.bot.get_cog(cog_name)
            if cog is None:
                continue
            commands = cog.get_commands()
            command_list = [f"{prefix}{cmd.name} - {cmd.description.partition('\n')[0]}" for cmd in commands if cmd.description]
            if command_list:
                embed.add_field(name=cog_name.capitalize(), value="```" + "\n".join(command_list) + "```", inline=False)

        await context.send(embed=embed)

"""


    @commands.hybrid_command(name="serverinfo2", description="get the bot prefix.")
    async def serverinfo(self, context: Context):
        roles = [role.name for role in context.guild.roles if not role.is_default()]
        embed = discord.Embed(title="Server Information", description=f"{context.guild.name}", color=0xBEBEFE)
        embed.add_field(name="Server ID", value=context.guild.id)
        embed.add_field(name="Member Count", value=context.guild.member_count)
        embed.add_field(name="Roles", value=", ".join(roles) if roles else "No roles", inline=False)
        await context.send(embed=embed)
        
async def setup(bot):
    await bot.add_cog(General(bot))
