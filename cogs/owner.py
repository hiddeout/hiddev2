import discord
from discord.ext import commands
import time  # Import the time module for uptime calculation
from backend.classes import Colors, Emojis
from aiohttp import ClientSession

# Define the Owner cog
class Owner(commands.Cog, name="Owner"):
    def __init__(self, bot):
        self.bot = bot

    # Define your commands within the Owner cog

    @commands.command(help="invite the bot in your server", aliases=["inv"], description="info")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def invite(self, ctx):
        button = discord.ui.Button(label="invite", style=discord.ButtonStyle.url, url=discord.utils.oauth_url(client_id=self.bot.user.id, permissions=discord.Permissions.all()))
        button2 = discord.ui.Button(label="support", style=discord.ButtonStyle.url, url="https://discord.gg/3C4dwpv5")
        view = discord.ui.View()
        view.add_item(button)
        view.add_item(button2)
        await ctx.reply(view=view, mention_author=False)

# Setup function to add cogs to the bot


async def setup(bot):
    await bot.add_cog(Owner(bot))
