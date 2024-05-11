import discord
from discord.ext import commands
from backend.classes import Colors, Emojis

class Moderation(commands.Cog, name="moderation"):
    def __init__(self, bot):
        self.bot = bot

    async def get_guild_prefix(self, ctx):
        """Utility function to fetch the current guild prefix."""
        default_prefix = "!"  # Default to '!' or retrieve from a config/environment variable
        if not ctx.guild:
            return default_prefix
        async with self.bot.db.execute("SELECT prefix FROM guild_prefixes WHERE guild_id = ?", (str(ctx.guild.id),)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else default_prefix

    async def send_embed(self, ctx, description, color, title=None):
        """Helper function to send embeds with a consistent style."""
        prefix = await self.get_guild_prefix(ctx)
        full_description = description if not title else description + f"\n\nUse `{prefix}help` for more commands."
        embed = discord.Embed(title=title, description=full_description, color=color)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="kick", description="Kick a user out of the server.")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, context: commands.Context, member: discord.Member, *, reason="Not specified"):
        """ Kick a member from the server. """
        
        # Check if the member has administrator permissions
        if member.guild_permissions.administrator:
            # Check if the author is the server owner
            if context.author != context.guild.owner:
                print(f"DEBUG: Author is not identified as the server owner. Author: {context.author}, Server owner: {context.guild.owner}")
                return await self.send_embed(context, "Member has administrator permissions and cannot be kicked by non-owners.", Colors.red)
        
        # Check if the author is the server owner
        if context.author == context.guild.owner:
            print("DEBUG: Author is identified as the server owner.")
            pass
        else:
            # Check if the author's role is below the member's role
            if context.author.top_role.position <= member.top_role.position:
                return await self.send_embed(context, f'You\'re unable to kick {member.mention} because they are above you in the role hierarchy', Colors.red)

        try:
            await member.kick(reason=reason)
            description = f"{Emojis.check} **{member}** was kicked by **{context.author}** for: `{reason}`"
            await self.send_embed(context, description, Colors.green)
            try:
                await member.send(f"You were kicked from **{context.guild.name}** by **{context.author}**. Reason: `{reason}`")
            except discord.Forbidden:
                pass
        except Exception as e:
            await self.send_embed(context, f"Failed to kick the member due to: {str(e)}", Colors.red)

    # Other moderation commands go here

async def setup(bot):
    await bot.add_cog(Moderation(bot))
