from discord.ext import commands

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="test", description="This is a test command", slash_command=True)
    async def _test(self, ctx: commands.Context):
        if isinstance(ctx, commands.Context):
            # The command was invoked with a prefix
            await ctx.send("Hello, World!")
        else:
            # The command was invoked as a slash command
            await ctx.respond("Hello, World!")

async def setup(bot):
    await bot.add_cog(MyCog(bot))