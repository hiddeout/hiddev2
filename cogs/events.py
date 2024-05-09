import discord
import datetime
from discord.ext import commands
from backend.classes import Colors, Emojis

class Events(commands.Cog, name="events"):
    def __init__(self, bot):
        self.bot = bot          

    @commands.Cog.listener()
    async def on_ready(self):
        message = self.bot.get_channel(1238211693415497789)
        embed = discord.Embed(color=Colors.default, title=f"**restarted**", description=f"> placeholder online - back online")
        embed.set_footer(text="connected to discord API")    
        await message.send(embed=embed)

    # Include other event handlers and methods as necessary

async def setup(bot):
    await bot.add_cog(Events(bot))

# Make sure to define the bot and other necessary parts of your application
