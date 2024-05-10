import discord
from discord.ext import commands
from aiohttp import ClientSession

class Owner(commands.Cog, name="owner"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="sync",
        help="Synchronizes the slash commands globally or for a specific guild.",
        description="Synchronizes the slash commands either across all guilds globally or within the current guild only."
    )
    @commands.is_owner()
    async def sync(self, ctx, scope: str):
        """
        Synchronizes the slash commands.
        """
        if scope == "global":
            await self.bot.tree.sync()
            embed = discord.Embed(
                description="Slash commands have been globally synchronized.",
                color=0xBEBEFE,
            )
            await ctx.send(embed=embed)
        elif scope == "guild":
            await self.bot.tree.sync(guild=ctx.guild)
            embed = discord.Embed(
                description="Slash commands have been synchronized in this guild.",
                color=0xBEBEFE,
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("The scope must be `global` or `guild`.")

    @commands.command(
        name="unsync",
        help="Unsynchronizes the slash commands globally or for a specific guild.",
        description="Clears and unsynchronizes the slash commands either from all guilds globally or from the current guild only."
    )
    @commands.is_owner()
    async def unsync(self, ctx, scope: str):
        """
        Unsynchronizes the slash commands.
        """
        if scope == "global":
            self.bot.tree.clear_commands(guild=None)
            await self.bot.tree.sync()
            await ctx.send("Slash commands have been globally unsynchronized.")
        elif scope == "guild":
            self.bot.tree.clear_commands(guild=ctx.guild)
            await self.bot.tree.sync(guild=ctx.guild)
            await ctx.send("Slash commands have been unsynchronized in this guild.")
        else:
            await ctx.send("The scope must be `global` or `guild`.")

    @commands.command(
        name="load",
        help="Loads a cog.",
        description="Dynamically loads a specified cog while the bot is running."
    )
    @commands.is_owner()
    async def load(self, ctx, cog: str):
        """
        Loads a cog.
        """
        try:
            await self.bot.load_extension(f"cogs.{cog}")
            await ctx.send(f"Successfully loaded the `{cog}` cog.")
        except Exception as e:
            await ctx.send(f"Could not load the `{cog}` cog. {e}")

    @commands.command(
        name="unload",
        help="Unloads a cog.",
        description="Dynamically unloads a specified cog while the bot is running."
    )
    @commands.is_owner()
    async def unload(self, ctx, cog: str):
        """
        Unloads a cog.
        """
        try:
            await self.bot.unload_extension(f"cogs.{cog}")
            await ctx.send(f"Successfully unloaded the `{cog}` cog.")
        except Exception as e:
            await ctx.send(f"Could not unload the `{cog}` cog. {e}")

    @commands.command(
        name="reload",
        help="Reloads a cog.",
        description="Dynamically reloads a specified cog to refresh its code during runtime."
    )
    @commands.is_owner()
    async def reload(self, ctx, cog: str):
        """
        Reloads a cog.
        """
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
            await ctx.send(f"Successfully reloaded the `{cog}` cog.")
        except Exception as e:
            await ctx.send(f"Could not reload the `{cog}` cog. {e}")

    @commands.command(
        name="shutdown",
        help="Shuts down the bot.",
        description="Safely shuts down the bot, ceasing all operations."
    )
    @commands.is_owner()
    async def shutdown(self, ctx):
        """
        Shuts down the bot.
        """
        await ctx.send("Shutting down. Bye! :wave:")
        await self.bot.close()

    @commands.command(
        name="botpfp",
        help="Changes the bot's profile picture to a provided image URL or an attached image.",
        description="Changes the bot's profile picture to the image URL provided, or an attached image from the message."
    )
    @commands.is_owner()
    async def change_bot_pfp(self, ctx, image: str = None):
        """
        Changes the bot's profile picture.
        """
        if not image and ctx.message.attachments:
            image = ctx.message.attachments[0].url
        elif not image:
            await ctx.send("Please provide an image URL or attach an image.")
            return

        async with ClientSession() as session:
            async with session.get(image) as response:
                if response.status != 200:
                    await ctx.send("Failed to fetch the image.")
                    return
                img = await response.read()

        try:
            await self.bot.user.edit(avatar=img)
            embed = discord.Embed(description=f"{self.bot.user.name}'s avatar changed successfully!", color=0xBEBEFE)
            embed.set_image(url=image)
            await ctx.send(embed=embed)
        except discord.HTTPException as e:
            await ctx.send(f"Failed to change avatar: {str(e)}")

async def setup(bot):
    await bot.add_cog(Owner(bot))
