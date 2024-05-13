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

# Setup logging
logging.basicConfig(level=logging.INFO)


class Moderation(commands.Cog):
    """Cog for moderation commands."""

    def __init__(self, bot):
        self.bot = bot
        self.guild_mute_roles = {}  # This will store guild_id: mute_role_id pairs

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




    @commands.command(
        name="jail", help="Jail a member", usage="[member]", description="Moderation"
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    # Add any additional decorators as needed
    async def jail(self, ctx: commands.Context, member: discord.Member = None, *, reason=None):
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("You do not have permission to manage channels.")
            return

        if member is None:
            await ctx.send("Please specify a member to jail.")
            return

        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner.id:
            embed = discord.Embed(
                color=Colors.yellow,
                description=f"{Emojis.warning} {ctx.author.mention}: you can't jail {member.mention}",
            )
            await ctx.send(embed=embed)
            return

        check = await self._execute_query(
            "SELECT * FROM setme WHERE guild_id = ?", (ctx.guild.id,)
        )
        if not check:
            em = discord.Embed(
                color=Colors.yellow,
                description=f"{Emojis.warning} {ctx.author.mention} use `setme` command before using jail",
            )
            await ctx.send(embed=em)
            return

        check = await self._execute_query(
            "SELECT * FROM jail WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id)
        )
        if check:
            em = discord.Embed(
                color=Colors.yellow,
                description=f"{Emojis.warning} {ctx.author.mention}: {member.mention} is jailed already",
            )
            await ctx.send(embed=em)
            return

        if reason is None:
            reason = "no reason provided"

        roles = [role.id for role in member.roles if role.managed == False and role.is_default() == False]

        sql_as_text = json.dumps(roles)
        await self._execute_query(
            "INSERT INTO jail (guild_id, user_id, roles) VALUES (?, ?, ?)", (ctx.guild.id, member.id, sql_as_text)
        )
        await self._execute_commit()

        for role in member.roles:
            if not role.managed:
                try:
                    await member.remove_roles(role)
                except Exception as e:
                    logging.error(f"Failed to remove role {role.name}: {str(e)}")

        role_id = check[1]
        jail_role = ctx.guild.get_role(role_id)
        if jail_role:
            try:
                await member.add_roles(jail_role, reason=f"jailed by {ctx.author} - {reason}")
                success = discord.Embed(
                    color=discord.Color.blue(),
                    description=f"{Emojis.check} {member.mention} got jailed - {reason}",
                )
                await ctx.send(embed=success)
            except Exception as e:
                embed = discord.Embed(
                    color=discord.Color.blue(),
                    description=f"{ctx.author.mention} there was a problem jailing {member.mention}: {str(e)}",
                )
                await ctx.send(embed=embed)
        else:
            logging.error("Jail role not found")
            await ctx.send("Jail role not found. Please check the configuration.")


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
            
            role = await ctx.guild.create_role(name="jail", color=0xff0000)
            for channel in ctx.guild.channels:
                await channel.set_permissions(role, view_channel=False)
    
            overwrite = {role: discord.PermissionOverwrite(view_channel=True), ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False)}
            jail = await ctx.guild.create_text_channel(name="jail", category=None, overwrites=overwrite)
            await cursor.execute("INSERT INTO setme (channel_id, role_id, guild_id) VALUES (?, ?, ?)", (jail.id, role.id, ctx.guild.id))
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
    
            button1 = Button(label="yes", style=discord.ButtonStyle.green)
            button2 = Button(label="no", style=discord.ButtonStyle.red)
            embed = discord.Embed(color=Colors.default, description=f"{ctx.author.mention} are you sure you want to clear jail module?")
    
            async def button1_callback(interaction: discord.Interaction):
                if interaction.user != ctx.author:
                    emb = discord.Embed(color=Colors.red, description=f"{Emojis.wrong} {interaction.user.mention}: this is not your message")
                    await interaction.response.send_message(embed=emb, ephemeral=True)
                    return
                async with ctx.bot.db.cursor() as cursor:
                    await cursor.execute("SELECT * FROM setme WHERE guild_id = ?", (ctx.guild.id,))
                    check = await cursor.fetchone()
                    channelid = check[0]
                    roleid = check[1]
                    channel = ctx.guild.get_channel(channelid)
                    role = ctx.guild.get_role(roleid)
                    try:
                        await role.delete()
                    except:
                        pass
    
                    try:
                        await channel.delete()
                    except:
                        pass
    
                    try:
                        await cursor.execute("DELETE FROM setme WHERE guild_id = ?", (ctx.guild.id,))
                        await ctx.bot.db.commit()
                        embed = discord.Embed(color=Colors.green, description=f"{ctx.author.mention}: jail module has been cleared")
                        await interaction.response.edit_message(embed=embed, view=None)
                    except:
                        pass
    
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





async def setup(bot):
    await bot.add_cog(Moderation(bot))
