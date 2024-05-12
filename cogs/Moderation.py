import discord
from discord.ext import commands
import aiosqlite
import datetime
import asyncio
import typing
from backend.classes import Colors, Emojis

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    """ 
        -- warn commands --

     """
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
            embed = discord.Embed(description=f"{Emojis.check} {member.mention} has been warned for: {reason}", color=Colors.default)
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

    """ 
        -- Lock commands --

     """
    @commands.command(name="lock", description="Locks the mentioned channel or the current channel if not specified.")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        """Lock the mentioned channel or the current channel if not specified."""
        if channel is None:
            channel = ctx.channel

        try:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False)
            await self.send_success_embed(ctx, f"{channel.mention} has been locked.")
        except Exception as e:
            await self.send_error_embed(ctx, f"An error occurred while locking the channel: {e}")

    @commands.command(name="unlock", description="Unlocks the mentioned channel or the current channel if not specified.")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """Unlock the mentioned channel or the current channel if not specified."""
        if channel is None:
            channel = ctx.channel

        try:
            await channel.set_permissions(ctx.guild.default_role, send_messages=True)
            await self.send_success_embed(ctx, f"{channel.mention} has been unlocked.")
        except Exception as e:
            await self.send_error_embed(ctx, f"An error occurred while unlocking the channel: {e}")

    @commands.command(name="lockall", description="Locks all text channels in the server.")
    @commands.has_permissions(manage_channels=True)
    async def lock_all(self, ctx):
        """Lock all text channels in the server."""
        try:
            for channel in ctx.guild.text_channels:
                await channel.set_permissions(ctx.guild.default_role, send_messages=False)
            await self.send_success_embed(ctx, f"All text channels have been locked.")
        except Exception as e:
            await self.send_error_embed(ctx, f"An error occurred while locking all channels: {e}")

    @commands.command(name="unlockall", description="Unlocks all text channels in the server.")
    @commands.has_permissions(manage_channels=True)
    async def unlock_all(self, ctx):
        """Unlock all text channels in the server."""
        try:
            for channel in ctx.guild.text_channels:
                await channel.set_permissions(ctx.guild.default_role, send_messages=True)
            await self.send_success_embed(ctx, f"All text channels have been unlocked.")
        except Exception as e:
            await self.send_error_embed(ctx, f"An error occurred while unlocking all channels: {e}")


    """ 
        -- old moderation commands --

     """


    async def send_embed(self, ctx, description, color):
        """Helper function to send embeds with a consistent style."""
        embed = discord.Embed(description=description, color=color)
        await ctx.send(embed=embed)

    @commands.command(name="kick", help="Kick a member from the server", usage="[member] <reason>", description="Moderation")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, user: discord.Member = None, *, reason=None):
        """Kick a member from the server."""
        if user is None:
            embed = discord.Embed(
                title="Command: kick",
                description="Kicks the mentioned user from the guild.\nSyntax & Example: ```Syntax: ,kick (user) (reason)\nExample: ,kick omtfiji Reason```",
                color=Colors.default
            )
            await ctx.send(embed=embed)
            return
        
        if not reason:
            reason = f'Kicked by {ctx.author}'

        if ctx.author == ctx.guild.owner:
            pass
        elif user == ctx.author:
            return await ctx.send(f'You\'re unable to kick yourself')
        elif user.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send(f'You\'re unable to kick {user.mention} because they are above you in the role hierarchy')
        elif user.top_role >= ctx.guild.me.top_role:
            return await ctx.send(f'I cannot kick {user.mention} because their highest role is above or equal to my highest role')
        else:
            try:
                await user.kick(reason=reason)
                description = f"{Emojis.check} {ctx.author.mention} `{user}` has been kicked."
                embed = discord.Embed(description=description, color=Colors.green)
                await ctx.send(embed=embed)
            except discord.Forbidden:
                description = f"{Emojis.error} Failed to send a message to {user.mention} or kick them."
                embed = discord.Embed(description=description, color=Colors.red)
                await ctx.send(embed=embed)

    @commands.command(name="ban", help="Ban a member from the server", usage="[member] <time> <reason>", description="Moderation")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, user: discord.Member = None, time: str = None, *, reason=None):
        """Ban a member from the server."""
        if user is None:
            embed = discord.Embed(
                title="Command: ban",
                description="Bans the mentioned user from the guild.\nSyntax & Example: ```Syntax: ,ban (user) (time) (reason)\nExample: ,ban @omtfiji 1h Reason```",
                color=Colors.default
            )
            await ctx.send(embed=embed)
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
        else:
            try:
                await user.ban(reason=reason)
                description = f"{Emojis.check} {ctx.author.mention} `{user}` has been banned."
                embed = discord.Embed(description=description, color=Colors.green)
                await ctx.send(embed=embed)
                
                # If time is provided, schedule unban
                if time:
                    try:
                        time_value = int(time[:-1])
                        time_unit = time[-1]
                        if time_unit == 'h':
                            unban_time = datetime.datetime.utcnow() + datetime.timedelta(hours=time_value)
                        elif time_unit == 'd':
                            unban_time = datetime.datetime.utcnow() + datetime.timedelta(days=time_value)
                        elif time_unit == 'm':
                            unban_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=time_value)
                        else:
                            return await ctx.send("Invalid time unit. Use 'h' for hours, 'd' for days, or 'm' for minutes.")
                        
                        await self.schedule_unban(user, unban_time)
                    except ValueError:
                        return await ctx.send("Invalid time format. Use a number followed by 'h' for hours, 'd' for days, or 'm' for minutes.")
            except discord.Forbidden:
                description = f"{Emojis.wrong} Failed to send a message to {user.mention} or ban them."
                embed = discord.Embed(description=description, color=Colors.red)
                await ctx.send(embed=embed)

    async def schedule_unban(self, user: discord.Member, unban_time: datetime.datetime):
        await asyncio.sleep((unban_time - datetime.datetime.utcnow()).total_seconds())
        await user.guild.unban(user)

    @commands.command(name="unban", help="Unban a member from the server", usage="[member]", description="Moderation")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user: discord.User = None):
        """Unban a member from the server."""
        if user is None:
            embed = discord.Embed(
                title="Command: unban",
                description="Unbans the mentioned user from the guild.\nSyntax & Example: ```Syntax: ,unban (user)\nExample: ,unban @omtfiji```",
                color=Colors.default
            )
            await ctx.send(embed=embed)
            return
        
        try:
            await ctx.guild.unban(user)
            description = f"{Emojis.check} {ctx.author.mention} `{user}` has been unbanned."
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


    



        """ 
        -- role commands --

     """
    

    @commands.command(name="rolehoist", description="Changes the display of a role.")
    async def role_hoist(self, ctx, role: discord.Role):
        """Changes the display of a role."""
        try:
            await role.edit(hoist=not role.hoist)
            embed = discord.Embed(description=f"{Emojis.check} The hoist status of the role {role.name} has been toggled.", color=Colors.green)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(description=f"{Emojis.wrong} An error occurred: {e}", color=Colors.red)
            await ctx.send(embed=embed)

    @commands.command(name="roledelete", description="Deletes a role.")
    async def role_delete(self, ctx, role: discord.Role):
        """Deletes a role."""
        try:
            await role.delete()
            embed = discord.Embed(description=f"{Emojis.check} The role {role.name} has been deleted.", color=Colors.green)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(description=f"{Emojis.wrong} An error occurred: {e}", color=Colors.red)
            await ctx.send(embed=embed)

    @commands.command(name="rolecolor", description="Changes the color of a role.")
    async def role_color(self, ctx, role: discord.Role, color: discord.Color):
        """Changes the color of a role."""
        try:
            await role.edit(color=color)
            embed = discord.Embed(description=f"{Emojis.check} The color of the role {role.name} has been changed to {color}.", color=Colors.green)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(description=f"{Emojis.wrong} An error occurred: {e}", color=Colors.red)
            await ctx.send(embed=embed)

    @commands.command(name="rolementionable", description="Changes the mentionability of a role.")
    async def role_mentionable(self, ctx, role: discord.Role):
        """Changes the mentionability of a role."""
        try:
            await role.edit(mentionable=not role.mentionable)
            embed = discord.Embed(description=f"{Emojis.check} The mentionability of the role {role.name} has been toggled.", color=Colors.green)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(description=f"{Emojis.wrong} An error occurred: {e}", color=Colors.red)
            await ctx.send(embed=embed)

    @commands.command(name="rolerename", description="Renames a role.")
    async def role_rename(self, ctx, role: discord.Role, new_name: str):
        """Renames a role."""
        try:
            await role.edit(name=new_name)
            embed = discord.Embed(description=f"{Emojis.check} The role has been renamed to {new_name}.", color=Colors.green)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(description=f"{Emojis.wrong} An error occurred: {e}", color=Colors.red)
            await ctx.send(embed=embed)

    @commands.command(name="rolecreate", description="Creates a role.")
    async def role_create(self, ctx, *role_name):
        """Creates a role."""
        role_name = " ".join(role_name)
        try:
            role = await ctx.guild.create_role(name=role_name)
            embed = discord.Embed(description=f"{Emojis.check} The role {role.name} has been created.", color=Colors.green)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(description=f"{Emojis.wrong} An error occurred: {e}", color=Colors.red)
            await ctx.send(embed=embed)

    @commands.command(name="roleicon", description="Changes the icon of a role.")
    async def role_icon(self, ctx, role: discord.Role, icon_url: str):
        """Changes the icon of a role."""
        try:
            await role.edit(icon=icon_url)
            embed = discord.Embed(description=f"{Emojis.check} The icon of the role {role.name} has been changed.", color=Colors.green)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(description=f"{Emojis.wrong} An error occurred: {e}", color=Colors.red)
            await ctx.send(embed=embed)

    @commands.command(name="roleposition", description="Changes the position of a role.")
    async def role_position(self, ctx, role: discord.Role, position: int):
        """Changes the position of a role."""
        try:
            await role.edit(position=position)
            embed = discord.Embed(description=f"{Emojis.check} The position of the role {role.name} has been changed to {position}.", color=Colors.green)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(description=f"{Emojis.wrong} An error occurred: {e}", color=Colors.red)
            await ctx.send(embed=embed)

    async def send_error_embed(self, ctx, error_message):
        """Send an error embed with the provided message."""
        embed = discord.Embed(description=f"{Emojis.wrong} {error_message}", color=Colors.red)
        await ctx.send(embed=embed)


        """ 
        -- mute commands --

     """



    async def send_error_embed(self, ctx, error_message):
        """Send an error embed with the provided message."""
        embed = discord.Embed(description=f"{Emojis.wrong} {error_message}", color=Colors.red)
        await ctx.send(embed=embed)

    async def send_success_embed(self, ctx, success_message):
        """Send a success embed with the provided message."""
        embed = discord.Embed(description=f"{Emojis.check} {success_message}", color=Colors.green)
        await ctx.send(embed=embed)

    @commands.command(name="rmute", description="Remove a member's add reactions & use external emotes permission.")
    @commands.has_permissions(manage_roles=True)
    async def remove_mute(self, ctx, member: discord.Member):
        """Remove a member's add reactions & use external emotes permission."""
        try:
            # Remove permissions here
            await self.send_success_embed(ctx, f"{member.mention} has been removed from mute.")
        except Exception as e:
            await self.send_error_embed(ctx, f"An error occurred while removing mute for {member.mention}: {e}")

    @commands.command(name="runmute", description="Restores a member's add reactions & use external emotes permission.")
    @commands.has_permissions(manage_roles=True)
    async def restore_unmute(self, ctx, member: discord.Member):
        """Restores a member's add reactions & use external emotes permission."""
        try:
            # Restore permissions here
            await self.send_success_embed(ctx, f"{member.mention}'s mute has been restored.")
        except Exception as e:
            await self.send_error_embed(ctx, f"An error occurred while restoring mute for {member.mention}: {e}")

    @commands.command(name="imute", description="Remove a member's attach files & embed links permission.")
    @commands.has_permissions(manage_roles=True)
    async def image_mute(self, ctx, member: discord.Member):
        """Remove a member's attach files & embed links permission."""
        try:
            # Remove permissions here
            await self.send_success_embed(ctx, f"{member.mention} has been image muted.")
        except Exception as e:
            await self.send_error_embed(ctx, f"An error occurred while image muting {member.mention}: {e}")

    @commands.command(name="iunmute", description="Restores a member's attach files & embed links permission.")
    @commands.has_permissions(manage_roles=True)
    async def restore_image_unmute(self, ctx, member: discord.Member):
        """Restores a member's attach files & embed links permission."""
        try:
            # Restore permissions here
            await self.send_success_embed(ctx, f"{member.mention}'s image mute has been restored.")
        except Exception as e:
            await self.send_error_embed(ctx, f"An error occurred while restoring image mute for {member.mention}: {e}")

    @commands.command(name="mute", description="Mute a member.")
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, *, reason: str = None):
        """Mute a member."""
        try:
            # Mute member here
            if reason:
                await self.send_success_embed(ctx, f"{member.mention} has been muted for: {reason}")
            else:
                await self.send_success_embed(ctx, f"{member.mention} has been muted.")
        except Exception as e:
            await self.send_error_embed(ctx, f"An error occurred while muting {member.mention}: {e}")

    @commands.command(name="unmute", description="Unmutes a member.")
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        """Unmutes a member."""
        try:
            # Unmute member here
            await self.send_success_embed(ctx, f"{member.mention} has been unmuted.")
        except Exception as e:
            await self.send_error_embed(ctx, f"An error occurred while unmuting {member.mention}: {e}")

    @commands.command(name="setupmute", description="Setup the appropriate roles for muting members.")
    @commands.has_permissions(manage_roles=True)
    async def setup_mute(self, ctx):
        """Setup the appropriate roles for muting members."""
        try:
            # Create muted role
            muted_role = await ctx.guild.create_role(
                name="muted",
                permissions=discord.Permissions(
                    send_messages=False,
                    add_reactions=True,  # If you want to allow reactions
                    attach_files=False,
                    embed_links=False
                )
            )

            # Create imuted role
            imuted_role = await ctx.guild.create_role(
                name="imuted",
                permissions=discord.Permissions(
                    attach_files=False,
                    embed_links=False
                )
            )

            # Create rmuted role
            rmuted_role = await ctx.guild.create_role(
                name="rmuted",
                permissions=discord.Permissions(
                    attach_files=False,
                    embed_links=False
                )
            )

            await self.send_success_embed(ctx, "Mute setup completed.")
        except Exception as e:
            await self.send_error_embed(ctx, f"An error occurred while setting up mute: {e}")

    @commands.command(name="mutecommands", description="Display all commands related to muting.")
    async def mute_commands(self, ctx):
        """Display all commands related to muting."""
        embed = discord.Embed(
            title="Mute Commands",
            description="Here are the commands related to muting:",
            color=Colors.default
        )
        embed.add_field(name="Mute a Member", value="`!mute @user reason`", inline=False)
        embed.add_field(name="Unmute a Member", value="`!unmute @user`", inline=False)
        embed.add_field(name="Remove Mute", value="`!rmute @user`", inline=False)
        embed.add_field(name="Restore Mute", value="`!runmute @user`", inline=False)
        embed.add_field(name="Image Mute", value="`!imute @user`", inline=False)
        embed.add_field(name="Restore Image Mute", value="`!iunmute @user`", inline=False)
        await ctx.send(embed=embed)


        """ 
        -- timeout commands  --

     """



        
# Forcenickname commands

    async def send_error_embed(self, ctx, error_message):
        """Send an error embed with the provided message."""
        embed = discord.Embed(description=f"{Emojis.wrong} {error_message}", color=Colors.red)
        await ctx.send(embed=embed)
    
    async def send_success_embed(self, ctx, success_message):
        """Send a success embed with the provided message."""
        embed = discord.Embed(description=f"{Emojis.check} {success_message}", color=Colors.green)
        await ctx.send(embed=embed)
    
    @commands.command(name="forcenickname", description="Forcefully set the nickname of a member.")
    @commands.has_permissions(manage_nicknames=True)
    async def force_nickname(self, ctx, member: typing.Optional[discord.Member] = None, *, new_nickname: typing.Optional[str] = None):
        """Forcefully set the nickname of a member."""
        if member is None:
            await ctx.send(embed=discord.Embed(description=f"{Emojis.warning} {ctx.author.mention}: Please provide a member.", color=Colors.red))
            return
        
        if new_nickname is None:
            await ctx.send(embed=discord.Embed(description=f"{Emojis.warning} {ctx.author.mention}: Please provide a new nickname.", color=Colors.red))
            return
    
        try:
            await member.edit(nick=new_nickname)
            await self.save_forced_nickname(ctx.guild.id, member.id, new_nickname)
            await self.send_success_embed(ctx, f"The nickname of {member.mention} has been set to: {new_nickname}")
        except Exception as e:
            await self.send_error_embed(ctx, f"An error occurred while setting the nickname of {member.mention}: {e}")
                
    async def save_forced_nickname(self, guild_id, member_id, nickname):
        """Save the forced nickname to the database."""
        try:
            async with aiosqlite.connect('database/database.db') as db:
                await db.execute("INSERT OR REPLACE INTO forced_nicknames (guild_id, member_id, nickname) VALUES (?, ?, ?)",
                                 (str(guild_id), str(member_id), nickname))
                await db.commit()
        except Exception as e:
            print(f"Error saving forced nickname: {e}")
    
    @commands.command(name="forcenicknamelist", description="View a list of all forced nicknames.")
    async def force_nickname_list(self, ctx):
        """View a list of all forced nicknames."""
        try:
            forced_nicknames = await self.get_forced_nicknames(ctx.guild.id)
            if forced_nicknames:
                # If there are forced nicknames, create an embed to display them
                embed = discord.Embed(
                    title="Forced Nickname List",
                    color=Colors.default
                )
                for member_id, nickname in forced_nicknames.items():
                    member = ctx.guild.get_member(int(member_id))
                    if member:
                        embed.add_field(name=f"{member.display_name}", value=f"```Original Name: {member.display_name}\n> {nickname}```", inline=False)
                    else:
                        # If the member is not found in the guild, display their username instead
                        user = await self.bot.fetch_user(int(member_id))
                        embed.add_field(name=f"Username: {user.name}", value=f"> {nickname}", inline=False)
                await ctx.send(embed=embed)
            else:
                await self.send_success_embed(ctx, "No forced nicknames found.")
        except Exception as e:
            await self.send_error_embed(ctx, f"An error occurred while fetching the forced nicknames: {e}")
                
    async def get_forced_nicknames(self, guild_id):
        """Fetch forced nicknames from the database."""
        try:
            async with aiosqlite.connect('database/database.db') as db:
                async with db.execute("SELECT member_id, nickname FROM forced_nicknames WHERE guild_id = ?",
                                      (str(guild_id),)) as cursor:
                    forced_nicknames = await cursor.fetchall()
            return {str(member_id): nickname for member_id, nickname in forced_nicknames}
        except Exception as e:
            print(f"Error fetching forced nicknames: {e}")
            return {}
    
    # Restorenickname commands
    
    @commands.command(name="restorenick", description="Restore the nickname of a member.")
    @commands.has_permissions(manage_nicknames=True)
    async def restore_nickname(self, ctx, member: discord.Member):
        """Restore the nickname of a member."""
        if member is None:
            await ctx.send(embed=discord.Embed(description=f"{Emojis.warning} {ctx.author.mention}: Please provide a member.", color=Colors.red))
            return
    
        try:
            await member.edit(nick=None)
            await self.send_success_embed(ctx, f"The nickname of {member.mention} has been restored.")
        except Exception as e:
            await self.send_error_embed(ctx, f"An error occurred while restoring the nickname of {member.mention}: {e}")
    
    @commands.command(name="restorenickall", description="Restore the nickname of all members.")
    @commands.has_permissions(manage_nicknames=True)
    async def restore_nickname_all(self, ctx):
        """Restore the nickname of all members."""
        try:
            for member in ctx.guild.members:
                await member.edit(nick=None)
            await self.send_success_embed(ctx, "All nicknames have been restored.")
        except Exception as e:
            await self.send_error_embed(ctx, f"An error occurred while restoring all nicknames: {e}")
    
    @commands.command(name="rename", description="Assigns the mentioned user a new nickname in the guild.")
    @commands.has_permissions(manage_nicknames=True)
    async def rename(self, ctx, member: discord.Member, *, new_nickname: str):
        """Assigns the mentioned user a new nickname in the guild."""
        try:
            await member.edit(nick=new_nickname)
            embed = discord.Embed(description=f"{Emojis.check} Nickname of {member.mention} has been set to: {new_nickname}", color=Colors.green)
            await ctx.send(embed=embed)
        except Exception as e:
            await self.send_error_embed(ctx, f"{Emojis.wrong} An error occurred while setting the nickname of {member.mention}: {e}")




     # Restorenickname commands

    async def send_error_embed(self, ctx, error_message):
        """Send an error embed with the provided message."""
        embed = discord.Embed(description=f"{Emojis.wrong} {error_message}", color=discord.Color.red())
        await ctx.send(embed=embed)

    async def send_success_embed(self, ctx, success_message):
        """Send a success embed with the provided message."""
        embed = discord.Embed(description=f"{Emojis.check} {success_message}", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command(name="purge", description="Deletes the specified amount of messages from the current channel.")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, target: discord.Member = None, limit: int = None):
        """Deletes the specified amount of messages from the current channel."""
        if limit is None:
            await ctx.send(embed=discord.Embed(title="Command: purge",
                                               description="Deletes the specified amount of messages from the current channel\nSyntax & Example: ```Syntax: ,purge (amount)\nExample: ,purge omtfiji 30```",
                                               color=discord.Color.default()))
            return

        if target is None:
            def check(m):
                return True
        else:
            def check(m):
                return m.author == target

        try:
            await ctx.channel.purge(limit=limit + 1, check=check)
            await self.send_success_embed(ctx, f"{limit} messages have been purged.")
        except discord.Forbidden:
            await self.send_error_embed(ctx, "I don't have permission to delete messages.")
        except discord.HTTPException as e:
            await self.send_error_embed(ctx, f"An error occurred: {e}")

    @commands.command(name="purgebots", description="Purge messages from bots in chat.")
    @commands.has_permissions(manage_messages=True)
    async def purge_bots(self, ctx, limit: int = None):
        """Purge messages from bots in chat."""
        if limit is None:
            await ctx.send(embed=discord.Embed(title="Command: purgebots",
                                               description="Purge messages from bots in chat\nSyntax & Example: ```Syntax: ,purgebots (amount)\nExample: ,purgebots 30```",
                                               color=discord.Color.default()))
            return

        try:
            def is_bot(m):
                return m.author.bot
            await ctx.channel.purge(limit=limit + 1, check=is_bot)
            await self.send_success_embed(ctx, f"{limit} bot messages have been purged.")
        except discord.Forbidden:
            await self.send_error_embed(ctx, "I don't have permission to delete messages.")
        except discord.HTTPException as e:
            await self.send_error_embed(ctx, f"An error occurred: {e}")




        """ 
          --

     """







    
async def setup(bot):
    await bot.add_cog(Moderation(bot))
