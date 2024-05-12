import discord
from discord.ext import commands
import datetime
from backend.classes import Colors, Emojis

# Function to format timedelta into a human-readable string
def format_timedelta(td: datetime.timedelta) -> str:
    seconds = td.total_seconds()
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    uptime_str = f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes and {seconds:.1f} seconds"
    return uptime_str

class Owner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = datetime.datetime.now(datetime.timezone.utc)  # Set start time when the cog is initialized

    async def cog_load(self):
        # Other initialization code here...
        pass

    async def cog_unload(self):
        # Cleanup code here...
        pass

    @commands.command(
        name="load",
        description="Load a cog",
    )
    async def load(self, context: commands.Context, cog: str) -> None:
        """
        The bot will load the given cog.

        :param context: The hybrid command context.
        :param cog: The name of the cog to load.
        """
        try:
            await self.bot.load_extension(f"cogs.{cog}")
        except Exception as e:
            embed = discord.Embed(
                description=f"{Emojis.warning}Error: {e}",
                color=Colors.yellow
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"{Emojis.warning}The cog {cog} has been successfully loaded!",
            color=Colors.yellow
        )
        await context.send(embed=embed)

    @commands.command(
        name="unload",
        description="Unload a cog",
    )
    async def unload(self, context: commands.Context, cog: str) -> None:
        """
        The bot will unload the given cog.

        :param context: The hybrid command context.
        :param cog: The name of the cog to unload.
        """
        try:
            await self.bot.unload_extension(f"cogs.{cog}")
        except Exception as e:
            embed = discord.Embed(
                description=f"{Emojis.warning}Error: {e}",
                color=Colors.yellow
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"{Emojis.warning}The cog {cog} has been successfully unloaded!",
            color=Colors.yellow
        )
        await context.send(embed=embed)

    @commands.command(
        name="reload",
        description="Reload a cog",
    )
    async def reload(self, context: commands.Context, cog: str) -> None:
        """
        The bot will reload the given cog.

        :param context: The hybrid command context.
        :param cog: The name of the cog to reload.
        """
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
        except Exception as e:
            embed = discord.Embed(
                description=f"{Emojis.warning}Error: {e}",
                color=Colors.yellow
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"{Emojis.warning}The cog {cog} has been successfully reloaded!",
            color=Colors.yellow
        )
        await context.send(embed=embed)
    
    @commands.command(
        name="reloadall",
        description="Reload all cogs except for this one."
    )
    async def reloadall(self, ctx):
        reloaded_cogs = []
        for extension in list(self.bot.extensions):
            if extension != "cogs.Owner":  # Exclude the cog containing this command
                try:
                    await self.bot.reload_extension(extension)  # Await the reload_extension coroutine
                    reloaded_cogs.append(extension)
                except Exception as e:
                    await ctx.send(f"Failed to reload {extension}: {e}")
        
        reloaded_cogs_str = "\n".join(f"`{cog}`" for cog in reloaded_cogs)
        embed = discord.Embed(
            description=f"{Emojis.warning}Reloaded cogs:\n{reloaded_cogs_str}",
            color=Colors.yellow
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="uptime",
        description="Check how long the bot has been running."
    )
    async def uptime(self, ctx):
        # Calculate the current time
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Calculate the uptime
        uptime = now - self.start_time
        
        # Format the uptime into a human-readable string
        uptime_str = format_timedelta(uptime)
        
        # Create an embed to display the uptime
        embed = discord.Embed(
            description=f"⏰ **{self.bot.user.name}** has been up for: {uptime_str}",
            color=Colors.default
        )
        
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Owner(bot))
