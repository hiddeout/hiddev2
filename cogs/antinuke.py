import discord
from discord.ext import commands

class Antinuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=["an"], invoke_without_command=True)
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def antinuke(self, ctx): 
        embed = discord.Embed(color=discord.Color.default(), title="group command: antinuke", description="protect your server against nukes and raids")
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.add_field(name="commands", value=">>> antinuke settings - returns stats of server's antinuke\nantinuke vanity - toggle anti vanity change module\nantinuke ban - toggle anti ban module\nantinuke kick - toggle anti kick module\nantinuke channel - toggle anti channel delete antinuke\nantinuke roledelete - toggle anti role delete module\nantinuke roleupdate - toggle anti role update module", inline=False)
        embed.add_field(name="punishments", value=">>> ban - bans the unauthorized member after an action\nkick - kicks the unauthorized member after an action\nstrip - removes all staff roles from the unauthorized member after an action", inline=False)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text="aliases: an")
        await ctx.reply(embed=embed, mention_author=False)
    
    @antinuke.command(help="returns stats of server's antinuke", description="antinuke")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def settings(self, ctx): 
        # Your antinuke settings command implementation

    @antinuke.command(help="toggle anti vanity update module", description="antinuke", usage="[subcommand] [punishment]", brief="antinuke vanity set - sets anti vanity update module\nantinuke vanity unset - unsets anti vanity update module")     
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def vanity(self, ctx: commands.Context, option=None, punishment=None):
        # Your antinuke vanity command implementation

    @antinuke.command(help="toggle anti ban module", description="antinuke", usage="[subcommand] [punishment]", brief="antinuke ban set - sets anti ban module\nantinuke ban unset - unsets anti ban module")     
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def ban(self, ctx: commands.Context, option=None, punishment=None):
        # Your antinuke ban command implementation

    @antinuke.command(help="toggle anti kick module", description="antinuke", usage="[subcommand] [punishment]", brief="antinuke kick set - sets anti kick module\nantinuke kick unset - unsets anti kick module")     
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def kick(self, ctx: commands.Context, option=None, punishment=None):
        # Your antinuke kick command implementation

    @antinuke.command(help="toggle anti channel delete module", description="antinuke", usage="[subcommand] [punishment]", brief="antinuke channel set - sets anti channel delete module\nantinuke channel unset - unsets anti channel delete module")     
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def channel(self, ctx: commands.Context, option=None, punishment=None):
        # Your antinuke channel command implementation
   
    @antinuke.command(help="toggle anti role delete module", description="antinuke", usage="[subcommand] [punishment]", brief="antinuke role set - sets anti role delete module\nantinuke role unset - unsets anti role delete module")     
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def roledelete(self, ctx: commands.Context, option=None, punishment=None):
        # Your antinuke roledelete command implementation

    @antinuke.command(help="toggle anti role update module", description="antinuke", usage="[subcommand] [punishment]", brief="antinuke role set - sets anti role update module\nantinuke role unset - unsets anti role update module")     
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def roleupdate(self, ctx: commands.Context, option=None, punishment=None):
        # Your antinuke roleupdate command implementation

        async def setup(bot):
            bot.add_cog(Antinuke(bot))
