import discord
from discord.ext import commands
from aiohttp import ClientSession
from discord import Embed

class Dev(commands.Cog, name="Dev"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="botpfp",
        description="Changes bot's profile picture."
    )
    async def change_bot_pfp(self, ctx, image: str = None):
        """
        Changes the bot's profile picture to the image URL provided, or an attached image.
        """
        # Check if the image URL is provided; if not, check for attachments.
        if not image and ctx.message.attachments:
            image = ctx.message.attachments[0].url
        elif not image:
            await ctx.reply("Please provide an image URL or attach an image.")
            return

        # Fetch the image data using aiohttp
        async with ClientSession() as session:
            async with session.get(image) as response:
                if response.status != 200:
                    await ctx.reply("Failed to fetch the image.")
                    return
                img = await response.read()

        # Update the bot's avatar
        try:
            await self.bot.user.edit(avatar=img)
            embed = Embed(description=f"{self.bot.user.name}'s avatar changed successfully!")
            embed.set_image(url=image)
            await ctx.reply(embed=embed)
        except discord.HTTPException as e:
            await ctx.reply(f"Failed to change avatar: {str(e)}")
        pass
async def setup(bot):
    await bot.add_cog(Dev(bot))
