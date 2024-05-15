import discord
from discord.ext import commands
import asyncio
import datetime
import re
import aiosqlite
import logging
import json
from discord.ui import Button, View
from backend.classes import Colors, Emojis
from collections import defaultdict
# Setup logging
logging.basicConfig(level=logging.INFO)



# RoleMembersView class
class RoleMembersView(View):
    def __init__(self, ctx, role, members, per_page=10):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.role = role
        self.members = members
        self.per_page = per_page
        self.current_page = 0
        self.total_pages = (len(members) - 1) // per_page + 1
        self.add_buttons()

    def add_buttons(self):
        if self.current_page > 0:
            prev_button = Button(label="Previous", style=discord.ButtonStyle.primary)
            prev_button.callback = self.previous_page
            self.add_item(prev_button)
        
        if self.current_page < self.total_pages - 1:
            next_button = Button(label="Next", style=discord.ButtonStyle.primary)
            next_button.callback = self.next_page
            self.add_item(next_button)
        
        close_button = Button(label="Close", style=discord.ButtonStyle.danger)
        close_button.callback = self.close
        self.add_item(close_button)

    async def previous_page(self, interaction: discord.Interaction):
        self.current_page -= 1
        await self.update_message(interaction)

    async def next_page(self, interaction: discord.Interaction):
        self.current_page += 1
        await self.update_message(interaction)

    async def close(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.message.delete()
        self.stop()

    async def update_message(self, interaction: discord.Interaction):
        self.clear_items()
        self.add_buttons()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    def create_embed(self):
        start = self.current_page * self.per_page
        end = start + self.per_page
        members_list = "\n".join([f"{i+1}. {member.display_name}" for i, member in enumerate(self.members[start:end], start=start)])
        embed = discord.Embed(title=f"Members in {self.role.name}", description=f"```{members_list}```", color=Colors.default)
        embed.set_footer(text=f"Page {self.current_page + 1}/{self.total_pages}")
        return embed


class Moderation(commands.Cog):
    """Cog for moderation commands."""

    def __init__(self, bot):
        self.bot = bot
        self.guild_mute_roles = {}  # This will store guild_id: mute_role_id pairs
        self.message_counts = defaultdict(lambda: defaultdict(int))
        self.message_limits = defaultdict(int)
        self.time_frame = 60  # Time frame in seconds
        self.reset_tasks = defaultdict(lambda: defaultdict(asyncio.Task))



# Helper functions
    async def _execute_query(self, query, params=None):
        async with self.bot.db.execute(query, params) as cursor:
            return await cursor.fetchall()

    async def _execute_commit(self):
        await self.bot.db.commit()

    async def create_embed(self, ctx, title, description, color):
        embed = discord.Embed(title=title, description=description, color=color)
        await ctx.send(embed=embed)

    async def schedule_unban(self, user: discord.Member, unban_time: datetime.datetime):
        await asyncio.sleep((unban_time - datetime.datetime.utcnow()).total_seconds())
        await user.guild.unban(user)

    async def send_warn_embed(self, ctx):
        """Send the warning embed for invalid input."""
        embed = discord.Embed(
            description=f"{Emojis.warning} {ctx.author.mention}: Please provide a member.",
            color=Colors.default
        )
        embed.set_author(name="Command: warn ,warnings , clearwarnings , clearwarns")
        embed.add_field(
            name="Syntax & Example",
            value="```Syntax: !warn (member) (reason)\nExample: !warn omtfiji Being mean\nExample: !warns @omtfiji\nExample: !clearwarns @omtfiji```"
        )
        await ctx.send(embed=embed)

    async def jail_user(self, ctx, member: discord.Member, reason: str):
        # Assuming you have the jail_log_channel_id stored in your database
        log_channel_id = await self.get_jail_log_channel_id(ctx.guild.id)
        log_channel = ctx.guild.get_channel(log_channel_id)

        embed = discord.Embed(title="Modlog Entry", color=discord.Color.blue())
        embed.add_field(name="Information", value=f"Case #XXX | Jailed\nUser: {member} ({member.id})\nModerator: {ctx.author} ({ctx.author.id})\nReason: {reason}\nToday at {datetime.datetime.utcnow().strftime('%H:%M %p')} UTC", inline=False)
        await log_channel.send(embed=embed)

        
    @staticmethod
    def get_color(color):
        return getattr(Colors, color.lower(), Colors.default)




# Ban Commands


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


#mute commands

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


#kick command

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member = None, *, reason: str = "No reason provided"):
        """Kick a member from the server."""
        if member is None:
            await self.create_embed(ctx, "Command: kick", "Kicks the mentioned user from the server.\n```Syntax: ,kick (user) (reason)\nExample: ,kick omtfiji Breaking rules```", self.get_color('default'))
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


#nicknames command

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





# Jail command - ADD TIME ARGUMENT

    @commands.command(
        name="jail", help="Jail a member", usage="[member] [reason]", description="Moderation"
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def jail(self, ctx: commands.Context, member: discord.Member, *, reason="no reason provided"):
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("You do not have permission to manage channels.")
            return
    
        # Check if the jail setup is complete
        jail_setup = await self._execute_query("SELECT * FROM setme WHERE guild_id = ?", (ctx.guild.id,))
        if not jail_setup:
            await ctx.send(embed=discord.Embed(color=self.get_color('yellow'), description=f"{Emojis.warning} {ctx.author.mention} use `setme` command before using jail"))
            return
    
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner.id:
            embed = discord.Embed(
                color=self.get_color('yellow'),
                description=f"{Emojis.warning} {ctx.author.mention}: you cannot jail {member.mention} because they have a higher or equal role."
            )
            await ctx.send(embed=embed)
            return
    
        already_jailed = await self._execute_query("SELECT * FROM jail WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id))
        if already_jailed:
            await ctx.send(embed=discord.Embed(color=self.get_color('yellow'), description=f"{Emojis.warning} {ctx.author.mention}: {member.mention} is already jailed"))
            return
    
        roles_to_remove = [role for role in member.roles if not role.managed and not role.is_default()]
        roles_json = json.dumps([role.id for role in roles_to_remove])
    
        await self._execute_query("INSERT INTO jail (guild_id, user_id, roles) VALUES (?, ?, ?)", (ctx.guild.id, member.id, roles_json))
        await self._execute_commit()
    
        for role in roles_to_remove:
            try:
                await member.remove_roles(role)
            except Exception as e:
                logging.error(f"Failed to remove role {role.name}: {str(e)}")
    
        jail_role_id = jail_setup[0][1]  # Corrected to fetch the role ID correctly
        jail_role = ctx.guild.get_role(jail_role_id)
        if jail_role:
            try:
                await member.add_roles(jail_role, reason=f"jailed by {ctx.author} - {reason}")
                success_embed = discord.Embed(color=self.get_color('green'), description=f"{Emojis.check} {member.mention} has been jailed - {reason}")
                await ctx.send(embed=success_embed)
    
                # Send to jail-log channel
                log_channel_id = jail_setup[0][3]  # Assuming the log_channel_id is the fourth element
                log_channel = ctx.guild.get_channel(log_channel_id)
                if log_channel:
                    log_embed = discord.Embed(title="Modlog Entry", color=discord.Color.blue())
                    log_embed.add_field(name="Information", value=f"Case #XXX | Jailed\nUser: {member} ({member.id})\nModerator: {ctx.author} ({ctx.author.id})\nReason: {reason}\nToday at {datetime.datetime.utcnow().strftime('%H:%M %p')} UTC", inline=False)
                    await log_channel.send(embed=log_embed)
            except Exception as e:
                await ctx.send(embed=discord.Embed(color=self.get_color('red'), description=f"{ctx.author.mention} there was a problem jailing {member.mention}: {str(e)}"))
        else:
            logging.error("Jail role not found")
            await ctx.send("Jail role not found. Please check the configuration.")
            

# Unjail command

    @commands.command(name="unjail")
    @commands.has_permissions(manage_channels=True)
    async def unjail(self, ctx, *, member_str: str):
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("You do not have permission to manage channels.")
            return
    
        # Convert the member input into a Member object
        try:
            member = await commands.MemberConverter().convert(ctx, member_str)
        except commands.MemberNotFound:
            await ctx.send(f"Member '{member_str}' not found.")
            return
    
        # Check if the member is jailed
        jailed_data = await self._execute_query("SELECT roles FROM jail WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id))
        if not jailed_data:
            await ctx.send(embed=discord.Embed(color=self.get_color('yellow'), description=f"{Emojis.warning} {ctx.author.mention}: {member.mention} is not currently jailed."))
            return
    
        # Parse the roles JSON from the database
        original_roles_ids = json.loads(jailed_data[0][0])
        original_roles = [ctx.guild.get_role(role_id) for role_id in original_roles_ids if ctx.guild.get_role(role_id)]
    
        # Remove the jail role
        jail_setup = await self._execute_query("SELECT role_id FROM setme WHERE guild_id = ?", (ctx.guild.id,))
        if jail_setup:
            jail_role = ctx.guild.get_role(jail_setup[0][0])
            if jail_role in member.roles:
                await member.remove_roles(jail_role)
    
        # Restore original roles
        try:
            await member.add_roles(*original_roles, reason="unjailing")
            success_embed = discord.Embed(color=self.get_color('green'), description=f"{Emojis.check} {member.mention} has been unjailed and their original roles restored.")
            await ctx.send(embed=success_embed)
    
            # Send to jail-log channel
            log_channel_id = await self._execute_query("SELECT log_channel_id FROM setme WHERE guild_id = ?", (ctx.guild.id,))
            if log_channel_id:
                log_channel = ctx.guild.get_channel(log_channel_id[0][0])
                if log_channel:
                    log_embed = discord.Embed(title="Modlog Entry", color=discord.Color.blue())
                    log_embed.add_field(name="Information", value=f"Case #XXX | Unjailed\nUser: {member} ({member.id})\nModerator: {ctx.author} ({ctx.author.id})\nToday at {datetime.datetime.utcnow().strftime('%H:%M %p')} UTC", inline=False)
                    await log_channel.send(embed=log_embed)
        except Exception as e:
            await ctx.send(embed=discord.Embed(color=self.get_color('red'), description=f"Failed to restore roles to {member.mention}: {str(e)}"))
    
        # Remove the jail record from the database
        await self._execute_query("DELETE FROM jail WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id))
        await self._execute_commit()


# Setme and unsetme commands


    @commands.command(help="set the jail module", description="config")
    @commands.cooldown(1, 6, commands.BucketType.guild)
    async def setme(self, ctx: commands.Context):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have administrator permissions.")
            return
    
        await ctx.message.channel.typing()
        async with ctx.bot.db.cursor() as cursor:
            await cursor.execute("SELECT * FROM setme WHERE guild_id = ?", (ctx.guild.id,))
            res = await cursor.fetchone()
            if res is not None:
                return await ctx.send(embed=discord.Embed(color=Colors.yellow, description=f"{Emojis.warning} {ctx.author.mention}: Jail is already set"))
    
            # Create the jail role
            role = await ctx.guild.create_role(name="jail", color=0xff0000)
    
            # Create the jail channel with specific permissions
            overwrites_jail = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                role: discord.PermissionOverwrite(read_messages=True)
            }
            jail_channel = await ctx.guild.create_text_channel('jail', overwrites=overwrites_jail)
    
            # Create the jail-log channel
            overwrites_log = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                role: discord.PermissionOverwrite(read_messages=False)  # Jail role should not see this channel
            }
            jail_log_channel = await ctx.guild.create_text_channel('jail-log', overwrites=overwrites_log)
    
            # Apply role permissions to all other channels
            for channel in ctx.guild.channels:
                if isinstance(channel, discord.TextChannel):
                    await channel.set_permissions(role, read_messages=False, read_message_history=False)
                elif isinstance(channel, discord.VoiceChannel):
                    await channel.set_permissions(role, connect=False)
    
            # Save the role and channel ID to the database
            await cursor.execute("INSERT INTO setme (channel_id, role_id, guild_id, log_channel_id) VALUES (?, ?, ?, ?)", (jail_channel.id, role.id, ctx.guild.id, jail_log_channel.id))
            await ctx.bot.db.commit()
            embed = discord.Embed(color=Colors.green, description=f"{Emojis.check} {ctx.author.mention} jail set")
            await ctx.send(embed=embed)
    
    
    @commands.command()
    @commands.cooldown(1, 6, commands.BucketType.guild)
    async def unsetme(self, ctx: commands.Context):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have administrator permissions.")
            return

        async with ctx.bot.db.cursor() as cursor:
            await cursor.execute("SELECT * FROM setme WHERE guild_id = ?", (ctx.guild.id,))
            check = await cursor.fetchone()
            if check is None:
                em = discord.Embed(color=Colors.yellow, description=f"{Emojis.warning} {ctx.author.mention}: jail module is not set")
                await ctx.send(embed=em)
                return

            button1 = Button(label="Yes", style=discord.ButtonStyle.green)
            button2 = Button(label="No", style=discord.ButtonStyle.red)
            embed = discord.Embed(color=Colors.default, description=f"{ctx.author.mention} are you sure you want to clear the jail module?")

            async def button1_callback(interaction: discord.Interaction):
                if interaction.user != ctx.author:
                    emb = discord.Embed(color=Colors.red, description=f"{Emojis.wrong} {interaction.user.mention}: this is not your message")
                    await interaction.response.send_message(embed=emb, ephemeral=True)
                    return
                async with ctx.bot.db.cursor() as cursor:
                    await cursor.execute("SELECT * FROM setme WHERE guild_id = ?", (ctx.guild.id,))
                    check = await cursor.fetchone()
                    channel_id = check[0]
                    role_id = check[1]
                    log_channel_id = check[3]  # Assuming log_channel_id is the fourth column in your setme table

                    channel = ctx.guild.get_channel(channel_id)
                    role = ctx.guild.get_role(role_id)
                    log_channel = ctx.guild.get_channel(log_channel_id)

                    try:
                        if role:
                            await role.delete()
                        if channel:
                            await channel.delete()
                        if log_channel:
                            await log_channel.delete()
                    except Exception as e:
                        await interaction.response.send_message(f"Failed to delete jail setup: {e}", ephemeral=True)
                        return

                    await cursor.execute("DELETE FROM setme WHERE guild_id = ?", (ctx.guild.id,))
                    await ctx.bot.db.commit()
                    embed = discord.Embed(color=Colors.green, description=f"{Emojis.check} {ctx.author.mention}: jail module has been cleared")
                    await interaction.response.edit_message(embed=embed, view=None)

            button1.callback = button1_callback

            async def button2_callback(interaction: discord.Interaction):
                if interaction.user != ctx.author:
                    emb = discord.Embed(color=Colors.red, description=f"{Emojis.wrong} {interaction.user.mention}: this is not your message")
                    await interaction.response.send_message(embed=emb, ephemeral=True)
                    return

                embed = discord.Embed(color=Colors.green, description=f"{Emojis.check} {ctx.author.mention}: you have changed your mind")
                await interaction.response.edit_message(embed=embed, view=None)

            button2.callback = button2_callback

            view = View()
            view.add_item(button1)
            view.add_item(button2)
            await ctx.send(embed=embed, view=view)


#warn command


    @commands.command(name="warn", description="Warns the mentioned user and saves the warning to the database.", usage="<member> <reason>")
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member = None, *, reason: str = None):
        """Warn a member and save the warning to the database."""
        if member is None:
            await self.send_warn_embed(ctx)
            return

        if reason is None:
            embed = discord.Embed(
                description=f"{Emojis.warning} {ctx.author.mention}: Please provide a reason.",
                color=Colors.default
            )
            embed.set_author(name="Command: warn ,warnings")
            embed.add_field(
                name="Syntax & Example",
                value="```Syntax: !warn (member) (reason)\nExample: !warn omtfiji Being mean\nExample: !warns @omtfiji\nExample: !clearwarns @omtfiji```"
            )
            await ctx.send(embed=embed)
            return

        try:
            # Save warning to the database
            async with aiosqlite.connect('database/database.db') as db:
                await db.execute("INSERT INTO warnings (guild_id, user_id, moderator_id, reason) VALUES (?, ?, ?, ?)",
                                 (str(ctx.guild.id), str(member.id), str(ctx.author.id), reason))
                await db.commit()

            # Send warning message within the guild if bot cannot send a direct message
            if not member.dm_channel:
                await member.create_dm()
            try:
                await member.dm_channel.send(f"You have been warned in {ctx.guild.name} for the following reason: `{reason}`")
            except discord.Forbidden:
                pass  # Do nothing if cannot send a direct message

            # Confirmation message with embed
            embed = discord.Embed(description=f"{Emojis.check} {member.mention} has been warned for: {reason}", color=Colors.green)
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"Error warning member: {e}")
            embed = discord.Embed(description=f"{Emojis.wrong} An error occurred while warning the member.", color=Colors.red)
            await ctx.send(embed=embed)

    @commands.command(name="warnings", aliases=["warns"], description="Lists all warnings for the mentioned user.")
    @commands.has_permissions(manage_messages=True)
    async def warnings(self, ctx, member: discord.Member = None):
        """List all warnings for a member."""
        if member is None:
            await self.send_warn_embed(ctx)
            return

        try:
            async with aiosqlite.connect('database/database.db') as db:
                async with db.execute("SELECT reason FROM warnings WHERE guild_id = ? AND user_id = ?",
                                      (str(ctx.guild.id), str(member.id))) as cursor:
                    warnings = await cursor.fetchall()

            if warnings:
                # Extract reasons from tuples and format them as strings with block quote formatting
                formatted_warnings = [f"> {reason[0]}" for reason in warnings]
                warning_list = "\n".join(formatted_warnings)
                embed = discord.Embed(description=f"**Warnings for {member.display_name}:**\n{warning_list}", color=Colors.default)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description=f"{Emojis.warning} No warnings found for `{member.display_name}`.", color=Colors.yellow)
                await ctx.send(embed=embed)
        except Exception as e:
            print(f"Error fetching warnings: {e}")
            await ctx.send("An error occurred while fetching warnings.")

    @commands.command(name="clearwarnings", aliases=["clearwarns"], description="Clears all warnings for the mentioned user.")
    @commands.has_permissions(manage_messages=True)
    async def clear_warnings(self, ctx, member: discord.Member = None):
        """Clear all warnings for a member."""
        if member is None:
            embed = discord.Embed(description=f"{Emojis.warning} {ctx.author.mention}: Please provide a user", color=Colors.red)
            await ctx.send(embed=embed)
            return
        
        try:
            async with aiosqlite.connect('database/database.db') as db:
                await db.execute("DELETE FROM warnings WHERE guild_id = ? AND user_id = ?",
                                 (str(ctx.guild.id), str(member.id)))
                await db.commit()
            
            embed = discord.Embed(description=f"{Emojis.check} Warnings cleared for {member.display_name}.", color=Colors.green)
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"Error clearing warnings: {e}")
            await ctx.send("An error occurred while clearing warnings.")

    async def send_error_embed(self, ctx, error_message):
        """Send an error embed with the provided message."""
        embed = discord.Embed(description=f"{Emojis.wrong} {error_message}", color=Colors.red)
        await ctx.send(embed=embed)

    async def send_success_embed(self, ctx, success_message):
        """Send a success embed with the provided message."""
        embed = discord.Embed(description=f"{Emojis.check} {success_message}", color=Colors.green)
        await ctx.send(embed=embed)



#role commands


    @commands.group(name="role", invoke_without_command=True, case_insensitive=True)
    async def role_group(self, ctx):
        """Group for role-related commands."""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Command: role",
                description="Modify a member's roles",
                color=Colors.default)
            embed.add_field(
                name="Syntax & Example",
                value=(
                    "```Syntax: !role (subcommand) (arguments)\n"
                    "Example: !role create NewRole\n"
                    "Example: !role rename @OldRole NewRole\n"
                    "Example: !role delete @RoleToDelete\n"
                    "Example: !role display @Role\n"
                    "Example: !role color @Role #FF5733\n"
                    "Example: !role mentionable @Role\n"
                    "Example: !role icon Role (icon_url)\n"
                    "Example: !role position @Role (position)\n"
                    "Example: !role add @Member @Role\n"
                    "Example: !role remove @Member @Role```"
                ),
                inline=False
            )
            await ctx.send(embed=embed)
    
    @role_group.command(name="create", description="Creates a role.", case_insensitive=True)
    async def role_create(self, ctx, *role_name):
        """Creates a role."""
        role_name = " ".join(role_name)
        try:
            role = await ctx.guild.create_role(name=role_name)
            embed = discord.Embed(description=f"{Emojis.check} The role {role.name} has been created.", color=Colors.green)
            await ctx.send(embed=embed)
        except Exception as e:
            await self.send_error_embed(ctx, str(e))
    
    @role_group.command(name="rename", description="Renames a role.", case_insensitive=True)
    async def role_rename(self, ctx, role: discord.Role, new_name: str):
        """Renames a role."""
        try:
            await role.edit(name=new_name)
            embed = discord.Embed(description=f"{Emojis.check} The role has been renamed to {new_name}.", color=Colors.green)
            await ctx.send(embed=embed)
        except Exception as e:
            await self.send_error_embed(ctx, str(e))
    
    @role_group.command(name="delete", description="Deletes a role.", case_insensitive=True)
    async def role_delete(self, ctx, role: discord.Role):
        """Deletes a role."""
        try:
            await role.delete()
            embed = discord.Embed(description=f"{Emojis.check} The role {role.name} has been deleted.", color=Colors.green)
            await ctx.send(embed=embed)
        except Exception as e:
            await self.send_error_embed(ctx, str(e))
    
    @role_group.command(name="add", description="Adds a role to a member.", case_insensitive=True)
    async def role_add(self, ctx, member: discord.Member, role: discord.Role):
        """Adds a role to a member."""
        try:
            if role in member.roles:
                embed = discord.Embed(description=f"{Emojis.warning} {member.display_name} already has the role {role.name}.", color=Colors.yellow)
                await ctx.send(embed=embed)
            else:
                await member.add_roles(role)
                embed = discord.Embed(description=f"{Emojis.check} {role.name} has been added to {member.display_name}.", color=Colors.green)
                await ctx.send(embed=embed)
        except Exception as e:
            await self.send_error_embed(ctx, str(e))
    
    @role_group.command(name="remove", description="Removes a role from a member.", case_insensitive=True)
    async def role_remove(self, ctx, member: discord.Member, role: discord.Role):
        """Removes a role from a member."""
        try:
            if role not in member.roles:
                embed = discord.Embed(description=f"{Emojis.warning} {member.display_name} does not have the role {role.name}.", color=Colors.yellow)
                await ctx.send(embed=embed)
            else:
                await member.remove_roles(role)
                embed = discord.Embed(description=f"{Emojis.check} {role.name} has been removed from {member.display_name}.", color=Colors.green)
                await ctx.send(embed=embed)
        except Exception as e:
            await self.send_error_embed(ctx, str(e))
    
    @role_group.command(name="color", description="Changes the color of a role.", case_insensitive=True)
    async def role_color(self, ctx, role: discord.Role, color: discord.Color):
        """Changes the color of a role."""
        try:
            await role.edit(color=color)
            embed = discord.Embed(description=f"{Emojis.check} The color of the role {role.name} has been changed to {color}.", color=Colors.green)
            await ctx.send(embed=embed)
        except Exception as e:
            await self.send_error_embed(ctx, str(e))
    
    @role_group.command(name="mentionable", description="Changes the mentionability of a role.", case_insensitive=True)
    async def role_mentionable(self, ctx, role: discord.Role):
        """Changes the mentionability of a role."""
        try:
            await role.edit(mentionable=not role.mentionable)
            embed = discord.Embed(description=f"{Emojis.check} The mentionability of the role {role.name} has been toggled.", color=Colors.green)
            await ctx.send(embed=embed)
        except Exception as e:
            await self.send_error_embed(ctx, str(e))
    
    @role_group.command(name="icon", description="Changes the icon of a role.", case_insensitive=True)
    async def role_icon(self, ctx, role: discord.Role, icon_url: str):
        """Changes the icon of a role."""
        try:
            await role.edit(icon=icon_url)
            embed = discord.Embed(description=f"{Emojis.check} The icon of the role {role.name} has been changed.", color=Colors.green)
            await ctx.send(embed=embed)
        except Exception as e:
            await self.send_error_embed(ctx, str(e))
    
    @role_group.command(name="position", description="Changes the position of a role.", case_insensitive=True)
    async def role_position(self, ctx, role: discord.Role, position: int):
        """Changes the position of a role."""
        try:
            await role.edit(position=position)
            embed = discord.Embed(description=f"{Emojis.check} The position of the role {role.name} has been changed to {position}.", color=Colors.green)
            await ctx.send(embed=embed)
        except Exception as e:
            await self.send_error_embed(ctx, str(e))
    
    async def send_error_embed(self, ctx, error_message):
        """Send an error embed with the provided message."""
        embed = discord.Embed(description=f"{Emojis.wrong} {error_message}", color=Colors.red)
        await ctx.send(embed=embed)


    @commands.command(name="inrole", description="Lists all members in the specified role.")
    async def inrole(self, ctx, *, role_name: str):
        """Lists all members in a role."""
        role_name = role_name.lower()
        role = discord.utils.find(lambda r: r.name.lower() == role_name, ctx.guild.roles)
        
        if role is None:
            embed = discord.Embed(description=f"{Emojis.warning} An error occurred: Role \"{role_name}\" not found.", color=Colors.red)
            await ctx.send(embed=embed)
            return

        members = [member for member in ctx.guild.members if role in member.roles]
        if not members:
            embed = discord.Embed(description=f"{Emojis.warning} No members found in the role {role.name}.", color=Colors.red)
            await ctx.send(embed=embed)
            return

        view = RoleMembersView(ctx, role, members)
        embed = view.create_embed()
        view.message = await ctx.send(embed=embed, view=view)

    async def send_error_embed(self, ctx, error_message):
        """Send an error embed with the provided message."""
        embed = discord.Embed(description=f"{Emojis.wrong} {error_message}", color=Colors.red)
        await ctx.send(embed=embed)



# Slowmode command - soon to be added




#message limit command


    @commands.command(name="setlimit", description="Sets the message limit for a specific channel.")
    @commands.has_permissions(manage_messages=True)
    async def setlimit(self, ctx, channel: discord.TextChannel, limit: int):
        """Sets the message limit for a specific channel."""
        self.message_limits[channel.id] = limit
        # Ensure message counts are reset when setting a new limit
        self.message_counts[channel.id] = defaultdict(int)
        embed = discord.Embed(description=f"{Emojis.check} Set message limit of {limit} messages per person for {channel.mention}.", color=Colors.green)
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
    
        channel_id = message.channel.id
        user_id = message.author.id
    
        # Increment message count
        self.message_counts[channel_id][user_id] += 1
    
        # Check if the user has exceeded the limit
        if channel_id in self.message_limits and self.message_counts[channel_id][user_id] > self.message_limits[channel_id]:
            await message.delete()
            embed = discord.Embed(description=f"{Emojis.warning} {message.author.mention}, you have exceeded the message limit for this channel.", color=Colors.red)
            await message.channel.send(embed=embed, delete_after=5)
        else:
            # Reset message count after the time frame
            if user_id not in self.reset_tasks[channel_id]:
                self.reset_tasks[channel_id][user_id] = self.bot.loop.create_task(self.reset_message_count(channel_id, user_id))
    
    async def reset_message_count(self, channel_id, user_id):
        await asyncio.sleep(self.time_frame)
        self.message_counts[channel_id][user_id] = 0
        del self.reset_tasks[channel_id][user_id]

    @commands.command(name="resetlimit", description="Resets the message limit for a specific channel.")
    @commands.has_permissions(manage_messages=True)
    async def resetlimit(self, ctx, channel: discord.TextChannel):
        """Resets the message limit and message counts for a specific channel."""
        if channel.id in self.message_limits:
            del self.message_limits[channel.id]  # Remove the limit for the channel
        # Reset message counts for all users in this channel
        self.message_counts[channel.id] = defaultdict(int)
        # Cancel and remove any reset tasks for this channel
        if channel.id in self.reset_tasks:
            for task in self.reset_tasks[channel.id].values():
                task.cancel()
            del self.reset_tasks[channel.id]
        embed = discord.Embed(description=f"{Emojis.check} Reset message limit and counts for {channel.mention}.", color=Colors.green)
        await ctx.send(embed=embed)




async def setup(bot):
    await bot.add_cog(Moderation(bot))
