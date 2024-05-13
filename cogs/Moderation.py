import discord
from discord.ext import commands
import asyncio
import datetime
import logging
from backend.classes import Colors, Emojis
# Setup logging
logging.basicConfig(level=logging.INFO)

class Moderation(commands.Cog):
    """Cog for moderation commands."""
    def __init__(self, bot):
        self.bot = bot

    async def create_embed(self, ctx, title, description, color):
        embed = discord.Embed(title=title, description=description, color=color)
        await ctx.send(embed=embed)

    async def schedule_unban(self, user: discord.Member, unban_time: datetime.datetime):
        await asyncio.sleep((unban_time - datetime.datetime.utcnow()).total_seconds())
        await user.guild.unban(user)

    @commands.command(name="ban", help="Ban a member from the server", usage="[member] <time> <reason>", description="Moderation")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, user: discord.Member = None, time: str = None, *, reason=None):
        """Ban a member from the server."""
        if user is None:
            await self.create_embed(ctx, "Command: ban", "Bans the mentioned user from the guild.\nSyntax & Example: ```Syntax: ,ban (user) (time) (reason)\nExample: ,ban @omtfiji 1h Reason```", discord.Color.default())
            return
        
        if not reason:
            reason = f'Banned by {ctx.author} / No reason provided'

        if ctx.author == ctx.guild.owner:
            pass
        elif user == ctx.author:
            return await ctx.send(f'You\'re unable to ban yourself')
        elif user.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send(f'You\'re unable to ban {user.mention} because they are above you in the role hierarchy')
        elif user.top_role >= ctx.guild.me.top_role:
            return await ctx.send(f'I cannot ban {user.mention} because their highest role is above or equal to my highest role')
        
        try:
            await user.ban(reason=reason)
            description = f"{Emojis.check} {ctx.author.mention} `{user}` has been banned."
            embed = discord.Embed(description=description, color=Colors.green)
            await ctx.send(embed=embed)
                
            # If time is provided, schedule unban
            if time:
                time_units = {'h': 'hours', 'd': 'days', 'm': 'minutes'}
                time_value, time_unit = int(time[:-1]), time[-1]
                if time_unit in time_units:
                    unban_time = datetime.datetime.utcnow() + datetime.timedelta(**{time_units[time_unit]: time_value})
                    await self.schedule_unban(user, unban_time)
                else:
                    return await ctx.send("Invalid time unit. Use 'h' for hours, 'd' for days, or 'm' for minutes.")
        except discord.Forbidden:
            description = f"{Emojis.wrong} Failed to send a message to {user.mention} or ban them."
            embed = discord.Embed(description=description, color=Colors.red)
            await ctx.send(embed=embed)

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user: discord.User = None):
        """Unban a member from the server."""
        if user is None:
            await self.create_embed(ctx, "Command: unban", "Unbans the mentioned user from the guild.\nSyntax & Example: ```Syntax: ,unban (user)\nExample: ,unban @user```", discord.Color.default())
            return
    
        try:
            await ctx.guild.unban(user)
            description = f"{Emojis.check} `{user}` has been unbanned."
            embed = discord.Embed(description=description, color=Colors.green)
            await ctx.send(embed=embed)
        except discord.NotFound:
            description = f"{Emojis.wrong} `{user}` is not banned from the server."
            embed = discord.Embed(description=description, color=Colors.red)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            description = f"{Emojis.wrong} Failed to unban `{user}`."
            embed = discord.Embed(description=description, color=Colors.red)
            await ctx.send(embed=embed)


    @commands.command(name="massunban")
    @commands.has_permissions(ban_members=True)
    async def massunban(self, ctx):
        """Unban all users from the server."""
        ban_list = await ctx.guild.bans()
        total_unbanned = 0
        for ban_entry in ban_list:
            user = ban_entry.user
            try:
                await ctx.guild.unban(user)
                total_unbanned += 1
            except discord.Forbidden:
                await ctx.send(f"Failed to unban {user.name}#{user.discriminator}.")
                continue
            except Exception as e:
                await ctx.send(f"An error occurred: {str(e)}")
                continue
    
        embed = discord.Embed(
            color=discord.Color.green(),
            description=f"{Emojis.check} Successfully unbanned {total_unbanned} users."
        )
        await ctx.send(embed=embed)


    @commands.command(name="mute")
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member = None, duration: int = None, *, reason: str = "No reason provided"):
        """Mute a member in the server."""
        if member is None or duration is None:
            await self.create_embed(ctx, "Command: mute", "Mutes the mentioned user in the server for a specified duration.\nSyntax & Example: ```Syntax: ,mute (user) (duration in minutes) [reason]\nExample: ,mute @user 10 Spamming```", discord.Color.default())
            return
    
        if ctx.author == member:
            return await ctx.send(f"{Emojis.wrong} You cannot mute yourself.")
    
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send(f"{Emojis.wrong} You cannot mute this member due to role hierarchy.")
    
        try:
            mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
            if not mute_role:
                mute_role = await ctx.guild.create_role(name="Muted")
            await member.add_roles(mute_role)
            await ctx.send(embed=discord.Embed(description=f"{Emojis.check} {member.display_name} has been muted for {duration} minutes. Reason: {reason}", color=discord.Color.green()))
            await asyncio.sleep(duration * 60)  # Converts minutes to seconds
            await member.remove_roles(mute_role)
            await ctx.send(f"{Emojis.check} {member.display_name} has been unmuted.")
        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(description=f"{Emojis.wrong} I do not have permission to mute.", color=discord.Color.red()))
        except Exception as e:
            logging.error(f"Error muting member: {e}")
            await ctx.send(embed=discord.Embed(description=f"{Emojis.wrong} An unexpected error occurred.", color=discord.Color.red()))

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member = None, *, reason: str = "No reason provided"):
        """Kick a member from the server."""
        if member is None:
            await self.create_embed(ctx, "Command: kick", "Kicks the mentioned user from the server.\nSyntax & Example: ```Syntax: ,kick (user) [reason]\nExample: ,kick @user Breaking rules```", discord.Color.default())
            return
    
        if ctx.author == member:
            return await ctx.send(f"{Emojis.wrong} You cannot kick yourself.")
    
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send(f"{Emojis.wrong} You cannot kick this member due to role hierarchy.")
    
        try:
            await member.kick(reason=reason)
            description = f"{Emojis.check} {member.display_name} has been kicked. Reason: {reason}"
            embed = discord.Embed(description=description, color=Colors.green)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            description = f"{Emojis.wrong} I do not have permission to kick."
            embed = discord.Embed(description=description, color=Colors.red)
            await ctx.send(embed=embed)
        except Exception as e:
            logging.error(f"Error kicking member: {e}")
            description = f"{Emojis.wrong} An unexpected error occurred."
            embed = discord.Embed(description=description, color=Colors.red)
            await ctx.send(embed=embed)
   
    @commands.group(invoke_without_command=True)
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None, *, reason="No reason provided"):
        """Lock a specified channel or the current channel if no channel is specified."""
        if channel is None:
            channel = ctx.channel  # Default to the current channel if none is specified
    
        await channel.set_permissions(ctx.guild.default_role, send_messages=False, reason=reason)
        embed = discord.Embed(
            color=discord.Color.green()  # Adjust the color to match your bot's theme
        )
        embed.description = f"{Emojis.check} {ctx.guild.me.mention}: {channel.mention} is now locked down for @everyone."
        await ctx.send(embed=embed)
    
    @lock.command(name="all")
    async def lock_all(self, ctx, *, reason="No reason provided"):
        """Lock all channels in the guild."""
        for channel in ctx.guild.text_channels:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False, reason=reason)
        embed = discord.Embed(
            color=discord.Color.green()  # Adjust the color to match your bot's theme
        )
        embed.description = f"{Emojis.check} {ctx.guild.me.mention} All channels have been locked down for @everyone."
        await ctx.send(embed=embed)
    
    @commands.group(invoke_without_command=True)
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None, *, reason="No reason provided"):
        """Unlock a specified channel or the current channel if no channel is specified."""
        if channel is None:
            channel = ctx.channel  # Default to the current channel if none is specified
    
        await channel.set_permissions(ctx.guild.default_role, send_messages=True, reason=reason)
        embed = discord.Embed(
            color=discord.Color.green()  # Adjust the color to match your bot's theme
        )
        embed.description = f"{Emojis.check} {ctx.guild.me.mention}: {channel.mention} has been unlocked for @everyone."
        await ctx.send(embed=embed)
    
    @unlock.command(name="all")
    async def unlock_all(self, ctx, *, reason="No reason provided"):
        """Unlock all channels in the guild."""
        for channel in ctx.guild.text_channels:
            await channel.set_permissions(ctx.guild.default_role, send_messages=True, reason=reason)
        embed = discord.Embed(
            color=discord.Color.green()  # Adjust the color to match your bot's theme
        )
        embed.description = f"{Emojis.check} {ctx.guild.me.mention} All channels have been unlocked for @everyone."
        await ctx.send(embed=embed)
    



async def setup(bot):
    await bot.add_cog(Moderation(bot))