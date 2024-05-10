import discord
from discord.ext import commands
from discord.ext.commands import Context  # This import is crucial for using Context
import asyncio
import aiosqlite
import os
import datetime
import re
import logging
from typing import Optional
from discord import TextChannel
from bot import DiscordBot
from backend.classes import Colors, Emojis

class Utility(commands.Cog):
    def __init__(self, bot: DiscordBot):
        self.bot = bot
        self.deleted_messages = {}

    async def cog_load(self):
        self.bot.db = await aiosqlite.connect('database/database.db')  # Assuming the DB connection is shared across cogs
        await self.bot.db.execute("""
        CREATE TABLE IF NOT EXISTS afk (
            guild_id INTEGER,
            user_id INTEGER,
            reason TEXT,
            afk_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        await self.bot.db.commit()

    async def cog_unload(self):
        await self.bot.db.close()

    @commands.hybrid_command(help="afk", description="Set AFK status", usage="[reason]")
    async def afk(self, ctx, *, reason="AFK"):
        now = datetime.datetime.utcnow()
        async with self.bot.db.execute("SELECT afk_time FROM afk WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, ctx.author.id)) as cursor:
            result = await cursor.fetchone()
        if not result:
            await self.bot.db.execute("INSERT INTO afk (guild_id, user_id, reason, afk_time) VALUES (?, ?, ?, ?)", (ctx.guild.id, ctx.author.id, reason, now))
            await self.bot.db.commit()
            embed = discord.Embed(description=f"<:approve:1229814143209439282> {ctx.author.mention} You're now AFK with the status: **{reason}**", color=Colors.green)
            await ctx.send(embed=embed)
        else:
            await ctx.send("You are already marked as AFK.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        mentioned_users = message.mentions
        for user in mentioned_users:
            async with self.bot.db.execute("SELECT reason, afk_time FROM afk WHERE guild_id = ? AND user_id = ?", (message.guild.id, user.id)) as cursor:
                result = await cursor.fetchone()
            if result:
                time_away = datetime.datetime.utcnow() - datetime.datetime.strptime(result[1], "%Y-%m-%d %H:%M:%S.%f")
                formatted_time = self.format_time_diff(time_away)
                await message.channel.send(embed=discord.Embed(description=f"{user.mention} is AFK: **{result[0]}** (away for {formatted_time})", color=Colors.default))
        async with self.bot.db.execute("SELECT reason, afk_time FROM afk WHERE guild_id = ? AND user_id = ?", (message.guild.id, message.author.id)) as cursor:
            result = await cursor.fetchone()
        if result:
            afk_time = datetime.datetime.strptime(result[1], "%Y-%m-%d %H:%M:%S.%f")
            duration = datetime.datetime.utcnow() - afk_time
            formatted_time = self.format_time_diff(duration)
            await self.bot.db.execute("DELETE FROM afk WHERE guild_id = ? AND user_id = ?", (message.guild.id, message.author.id))
            await self.bot.db.commit()
            await message.reply(embed=discord.Embed(description=f":wave: {message.author.mention}, welcome back! You were away for **{formatted_time}**.", color=Colors.default), mention_author=False)

    def format_time_diff(self, duration):
        days, remainder = divmod(duration.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        parts = []
        if days > 0:
            parts.append(f"{int(days)} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{int(hours)} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{int(minutes)} minute{'s' if minutes != 1 else ''}")
        if seconds > 0 and not parts:  # Show seconds only if no larger units
            parts.append(f"{int(seconds)} second{'s' if seconds != 1 else ''}")
        return ", ".join(parts) if parts else "less than a minute"

    def contains_invite_link(self, content):
        invite_pattern = r"(discord.gg/|discord.com/invite/|discordapp.com/invite/)[a-zA-Z0-9]+"
        return bool(re.search(invite_pattern, content))

class Prefix(commands.Cog, name="prefix"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="setprefix",
        description="Sets a custom command prefix for this server.",
        usage="setprefix <prefix>"  # Clearly specify how to use the command
    )
    @commands.has_permissions(manage_guild=True)
    async def setprefix(self, context: commands.Context, *, prefix: str):
        """
        Sets a custom command prefix for the server.

        :param context: The application command context.
        :param prefix: The new prefix to set. It must be provided when using the command.
        """
        async with self.bot.db.execute("INSERT OR REPLACE INTO guild_prefixes (guild_id, prefix) VALUES (?, ?)", (context.guild.id, prefix)):
            await self.bot.db.commit()
        embed = discord.Embed(description=f"{Emojis.check} Prefix set to: `{prefix}**`", color=Colors.green)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="getprefix",
        description="Gets the current command prefix for this server."
    )
    async def getprefix(self, context: commands.Context):
        """
        Gets the current command prefix for the server.

        :param context: The application command context.
        """
        async with self.bot.db.execute("SELECT prefix FROM guild_prefixes WHERE guild_id = ?", (context.guild.id,)) as cursor:
            prefix = await cursor.fetchone()
            if prefix:
                embed = discord.Embed(description=f"{Emojis.check} :The current prefix is: **{prefix[0]}**", color=Colors.gold)
                await context.send(embed=embed)
            else:
                embed = discord.Embed(description=f"{Emojis.warning} :No custom prefix set. Default is `!`.", color=Colors.yellow)
                await context.send(embed=embed)

    async def on_command_error(self, context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'prefix':
                embed = discord.Embed(description=f"{Emojis.warning} Prefix is a required argument that is missing.", color=Colors.yellow)
                await context.send(embed=embed)
        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(description=f"{Emojis.warning} This command is on cooldown.", color=Colors.yellow)
            await context.send(embed=embed)
        elif isinstance(error, commands.CheckFailure):
            embed = discord.Embed(description=f"{Emojis.wrong} You do not have permission to use this command.", color=Colors.red)
            await context.send(embed=embed)
        else:
            logging.error("Unhandled command error: %s", str(error), exc_info=True)
            embed = discord.Embed(description=f"{Emojis.wrong} An error occurred: {str(error)}", color=Colors.red)
            await context.send(embed=embed)


# Register the cogs
async def setup(bot: DiscordBot):
    await bot.add_cog(Utility(bot))
    await bot.add_cog(Prefix(bot))
