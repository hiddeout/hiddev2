import discord
from discord.ext import commands
import aiosqlite
from backend.classes import Colors, Emojis

class Prefix(commands.Cog, name="prefix"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="setprefix",
        description="Sets a custom command prefix for this server.",
        usage="setprefix <prefix>"
    )
    @commands.has_permissions(manage_guild=True)
    async def setprefix(self, context: commands.Context, *, prefix: str):
        """Sets a custom command prefix for the server."""
        try:
            await self.bot.db.execute("INSERT OR REPLACE INTO guild_prefixes (guild_id, prefix) VALUES (?, ?)", (str(context.guild.id), prefix))
            await self.bot.db.commit()
            embed = discord.Embed(description=f"{Emojis.check} Prefix set to: `{prefix}`", color=Colors.green)
            await context.send(embed=embed)
        except Exception as e:
            print(f"Error setting prefix: {e}")  # Log any errors
            embed = discord.Embed(description=f"{Emojis.wrong} Failed to set prefix due to an error.", color=Colors.red)
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="getprefix",
        description="Gets the current command prefix for this server."
    )
    async def getprefix(self, context: commands.Context):
        """Gets the current command prefix for the server."""
        try:
            async with self.bot.db.execute("SELECT prefix FROM guild_prefixes WHERE guild_id = ?", (str(context.guild.id),)) as cursor:
                prefix = await cursor.fetchone()
                if prefix:
                    embed = discord.Embed(description=f"{Emojis.check} The current prefix is: `{prefix[0]}`", color=Colors.gold)
                else:
                    embed = discord.Embed(description=f"{Emojis.warning} No custom prefix set. Default is `!`.", color=Colors.yellow)
            await context.send(embed=embed)
        except Exception as e:
            print(f"Failed to fetch prefix: {str(e)}")
            embed = discord.Embed(description=f"{Emojis.wrong} Failed to retrieve prefix due to an error.", color=Colors.red)
            await context.send(embed=embed)

async def setup(bot):
    bot.db = await aiosqlite.connect('database/database.db')  # Setup DB connection
    await bot.add_cog(Prefix(bot))
