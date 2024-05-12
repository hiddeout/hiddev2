import discord
from discord.ext import commands
import datetime
import pytz
import aiosqlite
from typing import Union
from backend.classes import Colors, Emojis
from discord.ui import View, Select

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


class InvalidPrefixError(commands.CommandError):
    """Raised when an invalid prefix is provided."""

    def __init__(self):
        super().__init__("Invalid prefix provided")

async def setup(bot):
    bot.db = await aiosqlite.connect('database/database.db')  # Setup DB connection

@commands.Cog.listener()
async def on_command_error(ctx, error):
    if isinstance(error, InvalidPrefixError):
        embed = discord.Embed(description=f"{Emojis.warning} {ctx.author.mention}: Please provide a valid **prefix**.", color=Colors.yellow)
        await ctx.send(embed=embed)
        
    
class HelpSelect(Select):
    def __init__(self, placeholder: str, options: list):
        super().__init__(placeholder=placeholder, options=options)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title=self.values[0], description="", color=Colors.default)
        for command in self.view.commands[self.values[0]]:
            embed.description += f"**{command.name}**: {command.description}\n"
        # Keep the view active by not passing view=None
        await interaction.response.edit_message(content=None, embed=embed, view=self.view)

class HelpView(View):
    def __init__(self, commands):
        super().__init__()
        self.commands = commands
        options = [
            discord.SelectOption(label=cog, description="Click to see commands in this category")
            for cog in commands
        ]
        self.add_item(HelpSelect(placeholder="Choose a category to display your help command!", options=options))

class MyHelp(commands.MinimalHelpCommand):
    async def send_bot_help(self, mapping):
        commands_by_cog = {}
        for cog, commands in mapping.items():
            if cog and cog.qualified_name == "Owner":  # Skip the Owner cog
                continue
            filtered = await self.filter_commands(commands, sort=True)
            if filtered:
                cog_name = getattr(cog, "qualified_name", "No Category")
                commands_by_cog[cog_name] = filtered

        view = HelpView(commands_by_cog)
        embed = discord.Embed(title="Help", description="Choose a category to display your help command!", color=Colors.default)
        channel = self.get_destination()
        await channel.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    bot.help_command = MyHelp()
    await bot.add_cog(Utility(bot))
