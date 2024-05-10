import discord
from discord.ext import commands
from backend.classes import Colors, Emojis

class Moderation(commands.Cog, name="moderation"):
    def __init__(self, bot):
        self.bot = bot

    async def send_embed(self, ctx, description, color):
        """Helper function to send embeds with a consistent style."""
        embed = discord.Embed(description=description, color=color)
        await ctx.send(embed=embed)

    @commands.command(name="kick", help="Kick a member from the server", usage="[member] <reason>", description="Moderation")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, user: discord.Member, *, reason=None):
        """Kick a member from the server."""
        async with ctx.typing():
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

    @commands.command(name="ban", help="Ban a member from the server", usage="[member] <reason>", description="Moderation")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, user: discord.Member, *, reason=None):
        """Ban a member from the server."""
        async with ctx.typing():
            if not reason:
                reason = f'Banned by {ctx.author}'

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
                except discord.Forbidden:
                    description = f"{Emojis.wrong} Failed to send a message to {user.mention} or ban them."
                    embed = discord.Embed(description=description, color=Colors.red)
                    await ctx.send(embed=embed)

    @commands.command(name="unban", help="Unban a member from the server", usage="[member]", description="Moderation")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user: discord.User):
        """Unban a member from the server."""
        async with ctx.typing():
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
