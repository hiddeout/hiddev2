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

async def setup(bot: DiscordBot):
    await bot.add_cog(Utility(bot))