import discord
import datetime
from discord.ext import commands
from backend.classes import Colors, Emojis

async def noperms(self, ctx, permission):
    e = discord.Embed(color=Colors.yellow, description=f"> {Emojis.warning} {ctx.author.mention}: you are missing permission `{permission}`")
    await sendmsg(self, ctx, None, e, None, None, None)


async def sendmsg(self, ctx, content, embed, view, file, allowed_mentions): 
    if ctx.guild is None: return
    try:
       await ctx.reply(content=content, embed=embed, view=view, file=file, allowed_mentions=allowed_mentions, mention_author=False)
    except:
        await ctx.send(content=content, embed=embed, view=view, file=file, allowed_mentions=allowed_mentions) 

class Events(commands.Cog, name="events"):
    def __init__(self, bot):
        self.bot = bot          

    @commands.Cog.listener()
    async def on_ready(self):
        message = self.bot.get_channel(1229643685981978664)
        embed = discord.Embed(color=Colors.default, title=f"**restarted**", description=f"> placeholder online - back online")
        embed.set_footer(text="connected to discord API")    
        await message.send(embed=embed)


def blacklist(): 
 async def predicate(ctx): 
   if ctx.guild is None:
     return False
   async with ctx.bot.db.cursor() as cursor:
    await cursor.execute("SELECT * FROM nodata WHERE user = {}".format(ctx.author.id))
    check = await cursor.fetchone()
    if check is not None: 
     await ctx.reply(embed=discord.Embed(color=Colors.default, description=f"{ctx.author.mention}: you're blacklisted. [join support](https://discord.gg/abort) to be unblacklisted."), mention_author=False)
    return check is None
 return commands.check(predicate)



    # Include other event handlers and methods as necessary


async def setup(bot):
    await bot.add_cog(Events(bot))

# Make sure to define the bot and other necessary parts of your application
