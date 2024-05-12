import discord
from discord.ext import commands
from datetime import datetime, timezone

class General(commands.Cog, name="General"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="serverinfo", help="Displays information about the server.")
    async def server_info(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(title=guild.name, color=0x000000)  # Adjust the color to match the screenshot
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

        # Server creation date
        created_at = guild.created_at.strftime("%B %d, %Y")
        months_since_creation = (datetime.now(timezone.utc) - guild.created_at).days // 30
        embed.add_field(name="Server created on", value=f"```{created_at} ({months_since_creation} months ago)```", inline=False)

        # Owner
        try:
            owner = await guild.fetch_member(guild.owner_id)
            owner_name = owner.name if owner else "Owner not available"
        except:
            owner_name = "Owner not available"
        embed.add_field(name="Owner", value=f"```{owner_name}```", inline=True)

        # Members and Information
        human_count = sum(1 for member in guild.members if not member.bot)
        bot_count = sum(1 for member in guild.members if member.bot)
        members_info = f"Total: {guild.member_count}\nHumans: {human_count}\nBots: {bot_count}"
        verification_boosts = f"Verification: {str(guild.verification_level).title()}\nBoosts: {guild.premium_subscription_count} (level {guild.premium_tier})"
        embed.add_field(name="Members", value=f"```{members_info}```", inline=True)
        embed.add_field(name="Information", value=f"```{verification_boosts}```", inline=True)
        

        # Counts
        counts_info = f"Roles: {len(guild.roles)}/250\nEmojis: {len(guild.emojis)}/500\nBoosters: {len(guild.premium_subscribers)}"
        embed.add_field(name="Counts", value=f"```{counts_info}```", inline=False)

        embed.set_footer(text=f"Guild ID: {guild.id} - Today at {datetime.now(timezone.utc).strftime('%I:%M %p')}")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))