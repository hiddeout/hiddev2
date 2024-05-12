import discord
from discord.ext import commands
import aiosqlite
from backend.classes import Colors, Emojis

class Prefix(commands.Cog, name="prefix"):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="prefix", invoke_without_command=True, description="Configure the server prefix for hidde.", usage="[set/delete]")
    async def prefix_group(self, ctx):
        """Configure the server prefix for hidde."""
        # Generate the list of aliases for the prefix_group command
        aliases_prefix_group = ', '.join(alias for alias in self.prefix_group.aliases)
        
        embed = discord.Embed(
            title="Command: prefix",
            description=f"Configure the server prefix for hidde.\nSyntax & Example: ```Syntax: !prefix set (prefix)\nExample:!prefix delete\nAliases: {aliases_prefix_group}```",
            color=Colors.default
        )
        await ctx.send(embed=embed)

    @prefix_group.command(name="set", description="Set a custom command prefix for this server.", usage="[prefix]", aliases=["s"])
    @commands.has_permissions(manage_guild=True)
    async def set_prefix(self, ctx, *, prefix: str = None):
        """Set a custom command prefix for this server."""
        if prefix is None:
            embed = discord.Embed(
                description=f"{Emojis.warning} {ctx.author.mention}: Please provide a valid **prefix**.",
                color=Colors.yellow
            )
            await ctx.send(embed=embed)
            return
    
        try:
            await self.bot.db.execute("INSERT OR REPLACE INTO guild_prefixes (guild_id, prefix) VALUES (?, ?)", (str(ctx.guild.id), prefix))
            await self.bot.db.commit()
            embed = discord.Embed(description=f"{Emojis.check} Prefix set to: `{prefix}`", color=Colors.green)
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"Error setting prefix: {e}")  # Log any errors
            embed = discord.Embed(description=f"{Emojis.wrong} Failed to set prefix due to an error.", color=Colors.red)
            await ctx.send(embed=embed)
    
    @prefix_group.command(name="delete", description="Delete the custom command prefix for this server.", aliases=["remove", "del", "d"])
    @commands.has_permissions(manage_guild=True)
    async def delete_prefix(self, ctx):
        """Delete the custom command prefix for this server."""
        try:
            await self.bot.db.execute("DELETE FROM guild_prefixes WHERE guild_id = ?", (str(ctx.guild.id),))
            await self.bot.db.commit()
            embed = discord.Embed(description=f"{Emojis.check} Prefix deleted. Default prefix is restored.", color=Colors.green)
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"Error deleting prefix: {e}")  # Log any errors
            embed = discord.Embed(description=f"{Emojis.wrong} Failed to delete prefix due to an error.", color=Colors.red)
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Send the current prefix when the bot is mentioned."""
        if self.bot.user.mentioned_in(message):
            prefix = await self.get_prefix(message.guild)
            await message.channel.send(f"My prefix here is `{prefix}`")

    async def get_prefix(self, guild):
        """Fetch the current prefix for the guild."""
        async with self.bot.db.execute("SELECT prefix FROM guild_prefixes WHERE guild_id = ?", (str(guild.id),)) as cursor:
            prefix = await cursor.fetchone()
            prefix_value = prefix[0] if prefix else "!"  # Default prefix if not set
            return prefix_value

    @commands.command(name="px", aliases=["serverprefix", "guildprefix", "gp"])
    async def prefix_alias(self, ctx):
        """Alias commands for setting prefix."""
        # Generate the list of aliases for the prefix_alias command
        aliases_prefix_alias = ', '.join(alias for alias in self.prefix_alias.aliases())
        embed = discord.Embed(
            title="Command: prefix",
            description=f"Configure the server prefix for hidde.\nSyntax & Example: ```Syntax: !prefix set (prefix)\nExample:!prefix delete```\nAliases: {aliases_prefix_alias}",
            color=Colors.default
        )
        await ctx.send(embed=embed)

class InvalidPrefixError(commands.CommandError):
    """Raised when an invalid prefix is provided."""

    def __init__(self):
        super().__init__("Invalid prefix provided")

async def setup(bot):
    bot.db = await aiosqlite.connect('database/database.db')  # Setup DB connection
    await bot.add_cog(Prefix(bot))

@commands.Cog.listener()
async def on_command_error(ctx, error):
    if isinstance(error, InvalidPrefixError):
        embed = discord.Embed(description=f"{Emojis.warning} {ctx.author.mention}: Please provide a valid **prefix**.", color=Colors.yellow)
        await ctx.send(embed=embed)
