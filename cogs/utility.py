import discord
from discord.ext import commands
import datetime
import pytz
from typing import Union
from backend.classes import Colors, Emojis


def format_timedelta(td: datetime.timedelta) -> str:
    seconds = td.total_seconds()
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    uptime_str = f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes and {seconds:.1f} seconds"
    return uptime_str

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

    @commands.command(name="userinfo", aliases=["ui"], description="Displays information about a user.")
    async def userinfo(self, ctx, user: Union[discord.Member, discord.User] = None):
        """Displays information about a user."""
        user = user or ctx.author
        
        def format_time_ago(past_time):
            time_diff = datetime.datetime.now(pytz.utc) - past_time
        
            if time_diff.days >= 365:
                years = time_diff.days // 365
                return f"{years} {'year' if years == 1 else 'years'} ago"
            elif time_diff.days >= 1:
                return f"{time_diff.days} {'day' if time_diff.days == 1 else 'days'} ago"
            elif time_diff.seconds >= 3600:
                hours = time_diff.seconds // 3600
                return f"{hours} {'hour' if hours == 1 else 'hours'} ago"
            elif time_diff.seconds >= 60:
                minutes = time_diff.seconds // 60
                return f"{minutes} {'minute' if minutes == 1 else 'minutes'} ago"
            else:
                return "Just now"
        
        embed = discord.Embed(title=f"{user.name} ({user.id})", color=Colors.default)
        
        # Set thumbnail if user has a custom avatar
        if isinstance(user, discord.User) and user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        elif isinstance(user, discord.Member) and user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        
        if isinstance(user, discord.Member) and user.guild:
            # Get joined date if user is in a guild
            local_timezone = pytz.timezone('US/Eastern')  # Change 'US/Eastern' to your preferred timezone
            joined_at = user.joined_at.strftime("%m/%d/%Y, %I:%M %p")
            joined_at_local = user.joined_at.astimezone(local_timezone)
            joined_at_ago = format_time_ago(joined_at_local)
            embed.add_field(name="**Dates**", value=f"**Created**: {user.created_at.strftime('%m/%d/%Y, %I:%M %p')} (\u200b{format_time_ago(user.created_at)})\n**Joined**: {joined_at} (\u200b{joined_at_ago})", inline=False)
            
            # Get roles sorted by position if user is in a guild
            roles = sorted(user.roles, key=lambda r: r.position, reverse=True)
            roles_str = ", ".join([role.mention for role in roles if role != ctx.guild.default_role])
            if roles_str:
                embed.add_field(name=f"**Roles ({len(roles) - 1})**", value=roles_str, inline=False)
        else:
            # Format account creation date
            account_created = user.created_at.strftime("%m/%d/%Y, %I:%M %p")
            
            # Convert UTC time to local time
            local_timezone = pytz.timezone('US/Eastern')  # Change 'US/Eastern' to your preferred timezone
            account_created_local = user.created_at.astimezone(local_timezone)
            
            # Calculate time since account creation
            account_created_ago = format_time_ago(account_created_local)
            
            # Create a separate embed for users not in the server
            embed = discord.Embed(title=f"{user.name} ({user.id})", color=Colors.default)
            embed.add_field(name="**Dates**", value=f"**Created**: {account_created} (\u200b{account_created_ago})", inline=False)
            
            # Set thumbnail if user not in server
            if user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
    
        if isinstance(user, discord.Member) and user.guild:
            embed.set_footer(text="User in this server.")
        else:
            embed.set_footer(text="User not in this server.")
    
        await ctx.send(embed=embed)
    
class MyHelp(commands.MinimalHelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Help", color=Colors.default)
        for cog, commands in mapping.items():
            if cog and cog.qualified_name == "Owner":  # Skip the Owner cog
                continue
            
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
