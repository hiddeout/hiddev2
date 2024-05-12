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

    @commands.command(name="unban", help="Unban a member from the server", usage="[member]", description="Moderation")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user: discord.User = None):
        """Unban a member from the server."""
        if user is None:
            await self.create_embed(ctx, "Command: unban", "Unbans the mentioned user from the guild.\nSyntax & Example: ```Syntax: ,unban (user)\nExample: ,unban @omtfiji```", discord.Color.default())
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

async def setup(bot):
    await bot.add_cog(Moderation(bot))