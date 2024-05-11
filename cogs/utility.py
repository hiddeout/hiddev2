import discord
from discord.ext import commands
import asyncio
import aiosqlite
import os
import datetime
import re
import logging
from typing import Optional
from backend.classes import Colors, Emojis
import aiohttp
import time


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
    async def slowmode(self, ctx, action: str, seconds: int = None):
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("You do not have permission to manage channels.")
            return 

        if action.lower() == "on":
            if seconds is None:
                await ctx.send("Please specify the number of seconds for slowmode.")
                return

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


async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))
