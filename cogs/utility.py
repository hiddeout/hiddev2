import discord
from discord.ext import commands
import aiosqlite
import datetime
import humanize
from backend.classes import Colors, Emojis
from discord.utils import utcnow
class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = datetime.datetime.now(datetime.timezone.utc)  # Set start time when the cog is initialized

    async def cog_load(self):
        # Other initialization code here...
        pass

    async def cog_unload(self):
        # Cleanup code here...
        pass

    @commands.command(name="ping", description="Check bot latency")
    async def ping(self, ctx):
        # Get current time in UTC timezone
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Measure websocket latency
        ws_latency = (now - ctx.message.created_at).total_seconds() * 1000
        
        # Calculate rest latency (message round trip)
        rest_latency = round(self.bot.latency * 1000, 2)
        
        # Calculate uptime
        uptime = now - self.start_time
        uptime_days = uptime.days if uptime.days is not None else 0
    
        # Create the ping message with custom emojis
        ping_message = f"{Emojis.ping} {ctx.author.mention} **websocket** `{int(ws_latency)} ms` , rest `{rest_latency} ms` (since: `{uptime_days} days ago)`"
        
        # Create an embed with the ping message as description
        embed = discord.Embed(description=ping_message, color=Colors.green)
    
        # Send the embed
        await ctx.send(embed=embed)

    @commands.command(help="Set slowmode for the current channel", description="Moderation")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def slowmode(self, ctx, action: str = None, seconds: int = 2):  # Default value for seconds is 2
        if action is None:
            embed = discord.Embed(
                title="Command: Slowmode",
                description="Restricts members to sending one message per interval.\nSyntax & Example: ```Syntax: !slowmode <seconds> <channel>\nExample: !slowmode 10 #general```",
                color=Colors.default
            )
            await ctx.send(embed=embed)
            return
        
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("You do not have permission to manage channels.")
            return 
        
        if action.lower() == "on":
            try:
                await ctx.channel.edit(slowmode_delay=seconds)
                embed = discord.Embed(
                    description=f"{Emojis.check} {ctx.author.mention}: Set the **message delay** to `{seconds}s` in {ctx.channel.mention}",
                    color=Colors.green
                )
                await ctx.send(embed=embed)
            except discord.Forbidden:
                await ctx.send("I do not have permission to edit slowmode in this channel.")
            except discord.HTTPException as e:
                await ctx.send(f"An error occurred: {e}")

        elif action.lower() == "off":
            try:
                await ctx.channel.edit(slowmode_delay=0)
                embed = discord.Embed(
                    description=f"{Emojis.check} {ctx.author.mention}: Removed **Slowmode** in {ctx.channel.mention}",
                    color=Colors.green
                )
                await ctx.send(embed=embed)
            except discord.Forbidden:
                await ctx.send("I do not have permission to edit slowmode in this channel.")
            except discord.HTTPException as e:
                await ctx.send(f"An error occurred: {e}")

        else:
            await ctx.send("Invalid action. Use `on` or `off`.")
        
        # Reset the cooldown





    
        #  utility commands make one by one and test them
    
    
    @commands.command(name="userinfo", description="Displays information about a user.")
    async def userinfo(self, ctx, user: discord.Member = None):
        """Displays information about a user."""
        user = user or ctx.author
        
        # Format account creation date and join date
        account_created = user.created_at.strftime("%m/%d/%Y, %I:%M %p")
        account_created_ago = humanize.naturaltime(utcnow() - user.created_at)
        joined_at = user.joined_at.strftime("%m/%d/%Y, %I:%M %p")
        joined_at_ago = humanize.naturaltime(utcnow() - user.joined_at)
        
        # Get roles sorted by position
        roles = sorted(user.roles, key=lambda r: r.position, reverse=True)
        roles_str = ", ".join([role.mention for role in roles if role != ctx.guild.default_role])
        
        embed = discord.Embed(title=f"{user.name} ({user.id})", color=Colors.default)
        
        # Set thumbnail if user has a custom avatar
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        
        embed.add_field(name="**Dates**", value=f"**Created**: {account_created} ({account_created_ago})\n**Joined**: {joined_at} ({joined_at_ago})", inline=False)
        embed.add_field(name=f"**Roles ({len(roles) - 1})**", value=roles_str, inline=False)
        
        # Add footer with join position and mutual servers
        if user.bot:
            footer_text = "This user is a bot."
        else:
            try:
                join_position = sorted(ctx.guild.members, key=lambda m: m.joined_at).index(user) + 1
            except ValueError:
                join_position = "N/A"
            mutual_servers = sum(1 for guild in self.bot.guilds if user in guild.members)
            footer_text = f"Join position: {join_position} ∙ Mutual servers: {mutual_servers}"
        
        embed.set_footer(text=footer_text)


    @commands.command(name="guildbanner", description="Displays the banner of the guild.")
    async def guildbanner(self, ctx):
        """Displays the banner of the guild."""
        banner_url = ctx.guild.banner_url
        if banner_url:
            embed = discord.Embed(title=f"Banner of {ctx.guild.name}", color=discord.Color.blurple())
            embed.set_image(url=banner_url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("This guild does not have a banner.")


        
        await ctx.send(embed=embed)
    



    



class MyHelp(commands.MinimalHelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Help", color=Colors.default)
        for cog, commands in mapping.items():
            filtered = await self.filter_commands(commands, sort=True)
            if filtered:  # Check if filtered is not None
                command_signatures = [self.get_command_signature(c) for c in filtered]
                if command_signatures:
                    cog_name = getattr(cog, "qualified_name", "No Category")
                    embed.add_field(name=cog_name, value="\n".join(command_signatures), inline=False)  
                    
        channel = self.get_destination()
        await channel.send(embed=embed)


async def setup(bot: commands.Bot):
    bot.help_command = MyHelp()
    await bot.add_cog(Utility(bot))
