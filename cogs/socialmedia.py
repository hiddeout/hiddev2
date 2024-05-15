import discord
from discord.ext import commands
import instaloader
import re
import aiohttp
import aiofiles
import os
import asyncio

class SocialMedia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loader = instaloader.Instaloader()

    @commands.command(name="insta")
    async def insta(self, ctx, *, url: str):
        # Regex to extract shortcode from URL
        match = re.search(r"instagram.com/(p|reel)/([^/]+)/", url)
        if not match:
            await ctx.send("Invalid Instagram URL provided.")
            return

        shortcode = match.group(2)
        retries = 3
        for attempt in range(retries):
            try:
                post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
                caption = post.caption if post.caption else "No caption provided."
                username = post.owner_username
                likes = post.likes
                comments = post.comments
                timestamp = post.date_utc.strftime("%Y-%m-%d %H:%M:%S")
                profile_pic_url = post.owner_profile.profile_pic_url

                embed = discord.Embed(description=f"[{caption}]({url})", color=0x1DA1F2)
                embed.set_author(name=username, icon_url=profile_pic_url)
                embed.add_field(name="Likes", value=f"❤️ {likes}", inline=True)
                embed.add_field(name="Comments", value=f"💬 {comments}", inline=True)
                embed.set_footer(text=f"❤️ {likes} 💬 {comments} • {username} • Posted on {timestamp}")

                # Check if the post is a video
                if post.is_video:
                    video_url = post.video_url
                    async with aiohttp.ClientSession() as session:
                        async with session.get(video_url) as response:
                            video_path = f"{shortcode}.mp4"
                            async with aiofiles.open(video_path, 'wb') as video_file:
                                await video_file.write(await response.read())
                    
                    await ctx.send(file=discord.File(video_path))
                    os.remove(video_path)
                else:
                    image_url = post.url
                    embed.set_image(url=image_url)

                await ctx.send(embed=embed)
                break  # Exit the retry loop if successful
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(2)  # Wait before retrying
                else:
                    await ctx.send(f"Failed to retrieve the Instagram post after {retries} attempts: {str(e)}")
            finally:
                # Close the Instaloader context
                self.loader.close()

async def setup(bot):
    await bot.add_cog(SocialMedia(bot))