import discord
from discord.ext import commands
import asyncio
import datetime
import re
import aiosqlite
import logging
from backend.classes import Colors, Emojis

# Setup logging
logging.basicConfig(level=logging.INFO)


class Moderation(commands.Cog):
    """Cog for moderation commands."""

    def __init__(self, bot):
        self.bot = bot
        self.guild_mute_roles = {}  # This will store guild_id: mute_role_id pairs


    async def create_embed(self, ctx, title, description, color):
        embed = discord.Embed(title=title, description=description, color=color)
        await ctx.send(embed=embed)

    async def schedule_unban(self, user: discord.Member, unban_time: datetime.datetime):
        await asyncio.sleep((unban_time - datetime.datetime.utcnow()).total_seconds())
        await user.guild.unban(user)

    @staticmethod
    def get_color(color):
        return getattr(Colors, color.lower(), Colors.default)

    @commands.command(name="ban", help="Ban a member from the server", usage="[member] <time> <reason>",)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, user: discord.Member = None, time: str = None, *, reason=None):
        """Ban a member from the server."""
        if user is None:
            await self.create_embed(ctx, "Command: ban", "Bans the mentioned user from the guild.\n```Syntax: ,ban (user) (time) (reason)\nExample: ,ban omtfiji 1h Reason```", self.get_color('default'))
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
            embed = discord.Embed(description=description, color=self.get_color('green'))
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
            embed = discord.Embed(description=description, color=self.get_color('red'))
            await ctx.send(embed=embed)

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user: discord.User = None):
        """Unban a member from the server."""
        if user is None:
            await self.create_embed(ctx, "Command: unban", "Unbans the mentioned user from the guild.\n```Syntax: ,unban (user)\nExample: ,unban omtfiji```", self.get_color('default'))
            return

        try:
            await ctx.guild.unban(user)
            description = f"{Emojis.check} `{user}` has been unbanned."
            embed = discord.Embed(description=description, color=self.get_color('green'))
            await ctx.send(embed=embed)
        except discord.NotFound:
            description = f"{Emojis.wrong} `{user}` is not banned from the server."
            embed = discord.Embed(description=description, color=self.get_color('red'))
            await ctx.send(embed=embed)
        except discord.Forbidden:
            description = f"{Emojis.wrong} Failed to unban `{user}`."
            embed = discord.Embed(description=description, color=self.get_color('red'))
            await ctx.send(embed=embed)

    @commands.command(name="massunban")
    @commands.has_permissions(ban_members=True)
    async def massunban(self, ctx):
        """Unban all users from the server."""
        total_unbanned = 0
        async for ban_entry in ctx.guild.bans():
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
            color=self.get_color('green'),
            description=f"{Emojis.check} Successfully unbanned {total_unbanned} users."
        )
        await ctx.send(embed=embed)



    @commands.command(name="setmuterole")
    @commands.has_permissions(manage_roles=True)
    async def set_mute_role(self, ctx, role: discord.Role):
        """Set a custom mute role for the server."""
        self.guild_mute_roles[ctx.guild.id] = role.id  # Store the role ID in the dictionary
        embed = discord.Embed(
            color=self.get_color('green'),  # Assuming you have a method to get colors, adjust as necessary
            description=f"{Emojis.check} Successfully binded the muted role as: {role.mention}"
        )
        await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        # Here you would typically save this to a database or a file
        # Here you would typically save this to a database or a file



    @commands.command(name="mute")
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member = None, duration: str = "0", *, reason: str = "No reason provided"):
        """Mute a member in the server."""
        if member is None:
            await self.create_embed(ctx, "Command: mute", "Mutes the mentioned user in the server for a specified duration.\n```Syntax: ,mute (user) (duration) (reason)\nExample: ,mute omtfiji 10m Spamming```", self.get_color('default'))
            return
    
        mute_role_id = self.guild_mute_roles.get(ctx.guild.id)
        mute_role = ctx.guild.get_role(mute_role_id) if mute_role_id else discord.utils.get(ctx.guild.roles, name="Muted")
    
        if not mute_role:
            mute_role = await ctx.guild.create_role(name="Muted")
            self.guild_mute_roles[ctx.guild.id] = mute_role.id  # Update the dictionary
    
        await member.add_roles(mute_role)
        duration_display = "`permanently`" if duration == "0" else duration
        mute_embed = discord.Embed(description=f"{Emojis.check} {member.mention} has been muted for {duration_display}. Reason: {reason}", color=self.get_color('green'))
        await ctx.send(embed=mute_embed)
        
        @commands.command(name="unmute")
        @commands.has_permissions(manage_roles=True)
        async def unmute(self, ctx, member: discord.Member = None):
            """Unmute a member in the server."""
            if member is None:
                await self.create_embed(ctx, "Command: unmute", "Unmutes the mentioned user in the server.\n```Syntax: ,unmute (user)\nExample: ,unmute omtfiji```", self.get_color('default'))
                return
        
            mute_role_id = self.guild_mute_roles.get(ctx.guild.id)
            mute_role = ctx.guild.get_role(mute_role_id) if mute_role_id else discord.utils.get(ctx.guild.roles, name="Muted")
        
            if mute_role and mute_role in member.roles:
                await member.remove_roles(mute_role)
                embed = discord.Embed(description=f"{Emojis.check} {member.display_name} has been unmuted.", color=self.get_color('green'))
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description=f"{Emojis.wrong} {member.display_name} is not muted.", color=self.get_color('red'))
                await ctx.send(embed=embed)
    @commands.command(name="unmute")
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member = None):
        """Unmute a member in the server."""



    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member = None, *, reason: str = "No reason provided"):
        """Kick a member from the server."""
        if member is None:
            await self.create_embed(ctx, "Command: kick", "Kicks the mentioned user from the server.\n```Syntax: ,kick (user) [reason]\nExample: ,kick omtfiji Breaking rules```", self.get_color('default'))
            return

        if ctx.author == member:
            return await ctx.send(f"{Emojis.wrong} You cannot kick yourself.")

        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send(f"{Emojis.wrong} You cannot kick this member due to role hierarchy.")

        try:
            await member.kick(reason=reason)
            description = f"{Emojis.check} {member.display_name} has been kicked. Reason: {reason}"
            embed = discord.Embed(description=description, color=self.get_color('green'))
            await ctx.send(embed=embed)
        except discord.Forbidden:
            description = f"{Emojis.wrong} I do not have permission to kick."
            embed = discord.Embed(description=description, color=self.get_color('red'))
            await ctx.send(embed=embed)
        except Exception as e:
            logging.error(f"Error kicking member: {e}")
            description = f"{Emojis.wrong} An unexpected error occurred."
            embed = discord.Embed(description=description, color=self.get_color('red'))
            await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None, *, reason="No reason provided"):
        """Lock a specified channel or the current channel if no channel is specified."""
        if channel is None:
            channel = ctx.channel  # Default to the current channel if none is specified

        await channel.set_permissions(ctx.guild.default_role, send_messages=False, reason=reason)
        embed = discord.Embed(
            color=self.get_color('green')  # Adjust the color to match your bot's theme
        )
        embed.description = f"{Emojis.check} {ctx.guild.me.mention}: {channel.mention} is now locked down for @everyone."
        await ctx.send(embed=embed)

    @lock.command(name="all")
    async def lock_all(self, ctx, *, reason="No reason provided"):
        """Lock all channels in the guild."""
        for channel in ctx.guild.text_channels:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False, reason=reason)
        embed = discord.Embed(
            color=self.get_color('green')  # Adjust the color to match your bot's theme
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
            color=self.get_color('green')  # Adjust the color to match your bot's theme
        )
        embed.description = f"{Emojis.check} {ctx.guild.me.mention}: {channel.mention} has been unlocked for @everyone."
        await ctx.send(embed=embed)

    @unlock.command(name="all")
    async def unlock_all(self, ctx, *, reason="No reason provided"):
        """Unlock all channels in the guild."""
        for channel in ctx.guild.text_channels:
            await channel.set_permissions(ctx.guild.default_role, send_messages=True, reason=reason)
        embed = discord.Embed(
            color=self.get_color('green')  # Adjust the color to match your bot's theme
        )
        embed.description = f"{Emojis.check} {ctx.guild.me.mention} All channels have been unlocked for @everyone."
        await ctx.send(embed=embed)



    @commands.command(name="nickname")
    @commands.has_permissions(manage_nicknames=True)
    async def nickname(self, ctx, *, args=None):
        """Change a user's nickname."""
        if args is None:
            await self.create_embed(
                ctx,
                "Command: nickname",
                "Assigns the mentioned user a new nickname in the guild.\n"
                "```Syntax: ,nickname @user (new nickname)\nExample: ,nickname omtfiji fiji```",
                Colors.default  # Using the Colors class
            )
            return

        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            await ctx.send("Please provide both a user and a new nickname.")
            return

        member = ctx.guild.get_member_named(parts[0])
        if member is None:
            member = await commands.MemberConverter().convert(ctx, parts[0])

        new_nickname = parts[1]

        try:
            await member.edit(nick=new_nickname)
            embed = discord.Embed(
                color=Colors.green,
                description=f"{Emojis.check} Nickname for {member.mention} has been changed to {new_nickname}."
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                color=Colors.red,
                description=f"{Emojis.wrong} I do not have permission to change this user's nickname."
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                color=Colors.red,
                description=f"{Emojis.wrong} An error occurred: {str(e)}"
            )
            await ctx.send(embed=embed)



    @commands.command(name="forcenickname")
    @commands.has_permissions(manage_nicknames=True)
    async def forcenickname(self, ctx, member: discord.Member, *, enforced_nickname: str):
        try:
            await member.edit(nick=enforced_nickname)
            embed = discord.Embed(
                color=self.get_color('green'),
                description=f"{Emojis.check} Enforced nickname for {member.display_name} to be {enforced_nickname}."
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                color=self.get_color('red'),
                description=f"{Emojis.wrong} I do not have permission to change this user's nickname."
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                color=self.get_color('red'),
                description=f"{Emojis.wrong} An error occurred: {str(e)}"
            )
            await ctx.send(embed=embed)







async def setup(bot):
    await bot.add_cog(Moderation(bot))
