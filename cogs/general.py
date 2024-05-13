import discord
import pytz
import aiosqlite
from typing import Union
from discord.ext import commands
from datetime import datetime, timezone
from backend.classes import Colors, Emojis

class General(commands.Cog, name="General"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="serverinfo", aliases=["si", "server", "guildinfo"], help="Displays information about the server.")
    async def server_info(self, ctx):
        guild = ctx.guild
        await guild.chunk()  # Ensure the guild cache is fully populated

        embed = discord.Embed(title=guild.name, color=Colors.default)  
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

        created_at = guild.created_at.strftime("%B %d, %Y")
        months_since_creation = (datetime.now(timezone.utc) - guild.created_at).days // 30
        embed.add_field(name="Server created on", value=f"```{created_at} ({months_since_creation} months ago)```", inline=False)

        owner_name = "Owner not available"
        try:
            owner = await guild.fetch_member(guild.owner_id)
            owner_name = owner.name if owner else "Owner not available"
        except:
            pass
        embed.add_field(name="Owner", value=f"```{owner_name}```", inline=True)

        human_count = sum(1 for member in guild.members if not member.bot)
        bot_count = sum(1 for member in guild.members if member.bot)
        members_info = f"Total: {guild.member_count}\nHumans: {human_count}\nBots: {bot_count}"
        verification_boosts = f"Verification: {str(guild.verification_level).title()}\nServer Boosts: {guild.premium_subscription_count} (level {guild.premium_tier})"
        counts_info = f"Roles: {len(guild.roles)}/250\nEmojis: {len(guild.emojis)}/500\nBoosters: {len(guild.premium_subscribers)}"
        
        embed.add_field(name="Members", value=f"```{members_info}```", inline=True)
        embed.add_field(name="Information", value=f"```{verification_boosts}```", inline=True)
        embed.add_field(name="Counts", value=f"```{counts_info}```", inline=False)

        embed.set_footer(text=f"Guild ID: {guild.id} - Today at {datetime.now(timezone.utc).strftime('%I:%M %p')}")

        buttons = []

        if guild.splash:
            buttons.append(discord.ui.Button(style=discord.ButtonStyle.url, label="Splash", url=guild.splash.url))
        if guild.banner:
            buttons.append(discord.ui.Button(style=discord.ButtonStyle.url, label="Banner", url=guild.banner.url))
        if guild.icon:
            buttons.append(discord.ui.Button(style=discord.ButtonStyle.url, label="Icon", url=guild.icon.url))

        if buttons:
            view = discord.ui.View()
            for button in buttons:
                view.add_item(button)
            await ctx.send(embed=embed, view=view)
        else:
            await ctx.send(embed=embed)




    @commands.command(name="userinfo", aliases=["ui"], description="Displays information about a user.")
    async def userinfo(self, ctx, user: Union[discord.Member, discord.User] = None):
        """Displays information about a user."""
        user = user or ctx.author

        embed = discord.Embed(color=Colors.default)
        embed.set_author(name=f"{user.name} ({user.id})", icon_url=user.avatar.url if user.avatar else None)
        embed.set_thumbnail(url=user.avatar.url if user.avatar else None)

        def format_time_ago(past_time):
            """Return a string representing how long ago `past_time` occurred."""
            now = datetime.now(timezone.utc)
            time_diff = now - past_time
            years, remainder = divmod(time_diff.days, 365)
            months, days = divmod(remainder, 30)

            if years > 0:
                return f"{years} year{'s' if years != 1 else ''} ago"
            if months > 0:
                return f"{months} month{'s' if months != 1 else ''} ago"
            if days > 0:
                return f"{days} day{'s' if days != 1 else ''} ago"
            hours, remainder = divmod(time_diff.seconds, 3600)
            if hours > 0:
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            minutes = remainder // 60
            if minutes > 0:
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            return "Just now"

        # Account creation and join dates
        created_at = user.created_at.strftime("%m/%d/%Y, %I:%M %p")
        created_ago = format_time_ago(user.created_at)
        embed.add_field(name="Account Created", value=f"{created_at} ({created_ago})", inline=False)

        if isinstance(user, discord.Member):
            joined_at = user.joined_at.strftime("%m/%d/%Y, %I:%M %p")
            joined_ago = format_time_ago(user.joined_at)
            server_name = ctx.guild.name
            embed.add_field(name=f"Joined {server_name}", value=f"{joined_at} ({joined_ago})", inline=False)

            # Roles
            roles = [role.mention for role in sorted(user.roles, key=lambda r: r.position, reverse=True) if role != ctx.guild.default_role]
            roles_str = ", ".join(roles) if roles else "None"
            embed.add_field(name=f"Roles [{len(roles)}]", value=roles_str, inline=False)

            # Additional fields like join position and mutual servers can be added if you have that data
            # Example:
            # embed.add_field(name="Join Position", value="61", inline=True)
            # embed.add_field(name="Mutual Servers", value="12", inline=True)

        footer_text = "User in this server." if isinstance(user, discord.Member) else "User not in this server."
        embed.set_footer(text=footer_text)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(General(bot))
