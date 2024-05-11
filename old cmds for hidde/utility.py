import discord
import asyncio
import re
import aiosqlite
import datetime
import os
from typing import Optional
from discord.ext import commands
from discord import TextChannel
from bot import DiscordBot
from backend.classes import Colors, Emojis  # Assuming these are defined correctly in your backend.classes

reaction_message_author = {}
reaction_message_author_avatar = {}
reaction_message_emoji_url = {}
reaction_message_emoji_name = {}
reaction_message_id = {}
edit_message_author = {}
edit_message_content1 = {}
edit_message_content2 = {}
edit_message_author_avatar = {}
edit_message_id = {}






class Utility(commands.Cog):
    def __init__(self, bot: DiscordBot):
        self.bot = bot
        self.deleted_messages = {}
        self.db_path = 'database/database.db'  # Adjusted to relative path

    async def cog_load(self):
        dir_path = os.path.dirname(self.db_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)  # Create the dir if it does not exist
        self.bot.db = await aiosqlite.connect(self.db_path)
        # Create table if not exists (Example schema)
        await self.bot.db.execute("""
        CREATE TABLE IF NOT EXISTS afk (
            guild_id INTEGER,
            user_id INTEGER,
            reason TEXT
        )
        """)
        await self.bot.db.commit()

    async def cog_unload(self):
        await self.bot.db.close()

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if member is None or member.bot:
            return
        reaction_message_author[payload.channel_id] = member.name
        reaction_message_author_avatar[payload.channel_id] = member.display_avatar.url
        reaction_message_emoji_url[payload.channel_id] = payload.emoji.url
        reaction_message_emoji_name[payload.channel_id] = payload.emoji.name
        reaction_message_id[payload.channel_id] = payload.message_id

    @commands.hybrid_command(help="afk", description="afk man", usage="[command]")
    async def afk(self, ctx, *, reason="AFK"):
        result = await self.bot.db.fetchrow("SELECT * FROM afk WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, ctx.author.id)
        if result is None:
            await self.bot.db.execute("INSERT INTO afk (guild_id, user_id, reason) VALUES ($1, $2, $3)", ctx.guild.id, ctx.author.id, reason)
            embed = discord.Embed(description=f"> You're now AFK with the status: **{reason}**", color=Colors.default)
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        mentioned_users = message.mentions
        for user in mentioned_users:
            result = await self.bot.db.fetchrow("SELECT * FROM afk WHERE guild_id = $1 AND user_id = $2", message.guild.id, user.id)
            if result:
                await message.channel.send(embed=discord.Embed(description=f"{user.mention} is AFK: **{result['reason']}**", color=Colors.default))
        result = await self.bot.db.fetchrow("SELECT * FROM afk WHERE guild_id = $1 AND user_id = $2", message.guild.id, message.author.id)
        if result:
            await self.bot.db.execute("DELETE FROM afk WHERE guild_id = $1 AND user_id = $2", message.guild.id, message.author.id)
            await message.channel.send(embed=discord.Embed(description="> Welcome back, you are no longer AFK.", color=Colors.default))

    @commands.hybrid_command(aliases=['sav', 'serveravatar'])
    async def memberavatar(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        avatar_url = member.guild_avatar
        if avatar_url:
            embed = discord.Embed(title=f"{member.name}'s server avatar", url=avatar_url)
            embed.set_image(url=avatar_url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("This member doesn't have a server avatar set.")

    @commands.hybrid_command(aliases=['av', 'pfp'])
    async def avatar(self, ctx, *, member: Optional[discord.User | discord.Member] = None):
        member = member or ctx.author
        avatar_url = member.avatar
        if avatar_url:
            embed = discord.Embed(title=f"{member.name}'s avatar", url=avatar_url, color=Colors.default)
            embed.set_image(url=avatar_url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("This member doesn't have an avatar set.")

    @commands.hybrid_command()
    async def banner(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        req = await self.bot.http.request(discord.http.Route("GET", "/users/{uid}", uid=user.id))
        banner_id = req.get("banner")
        if banner_id:
            banner_url = f"https://cdn.discordapp.com/banners/{user.id}/{banner_id}?size=1024"
            embed = discord.Embed(title=f"{user.name}'s banner", url=banner_url, color=Colors.default)
            embed.set_image(url=banner_url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("This member doesn't have a banner set.")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.content:
            channel_id = message.channel.id
            if channel_id not in self.deleted_messages:
                self.deleted_messages[channel_id] = []
            content = message.content
            if self.contains_invite_link(content):
                content = f"{Emojis.warning} This message contains an invite link."
            self.deleted_messages[channel_id].append((content, message.author.name, message.created_at))

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.content != after.content:
            await self.on_message_delete(before)

    def contains_invite_link(self, content):
        invite_pattern = r"(discord.gg/|discord.com/invite/|discordapp.com/invite/)[a-zA-Z0-9]+"
        return bool(re.search(invite_pattern, content))

    @commands.hybrid_command(aliases=['s'])
    async def snipe(self, ctx, index: int = 1):
        channel_id = ctx.channel.id
        if channel_id in self.deleted_messages:
            deleted_list = self.deleted_messages[channel_id]
            total_deleted = len(deleted_list)
            if 1 <= index <= total_deleted:
                content, author, created_at = deleted_list[-index]
                embed = discord.Embed(description=content, color=Colors.default)
                embed.set_author(name=author)
                central_tz = datetime.timezone(datetime.timedelta(hours=-4))
                created_at_central = created_at.astimezone(central_tz)
                embed.set_footer(text=f"{index}/{total_deleted} | {created_at_central.strftime('%I:%M %p')}")
                await ctx.send(embed=embed)
            else:
                await ctx.send("Invalid message index.")
        else:
            await ctx.send("No recently deleted messages to snipe.")

    @commands.hybrid_command(aliases=['whois', 'wi', 'userinfo', 'user'])
    async def ui(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(title="User Information", color=Colors.default)
        embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name="Name", value=member.name)
        embed.add_field(name="ID", value=member.id)
        embed.add_field(name="Created At", value=member.created_at.strftime("%b %d, %Y %H:%M:%S UTC"))
        if member.top_role != member.guild.default_role:
            embed.add_field(name="Top Role", value=member.top_role.mention)
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="serverinfo", description="Shows the information for your server", aliases=["si"])
    async def serverinfo(self, ctx):
        guild = ctx.guild
        server_id = guild.id
        server_owner = guild.owner
        server_created_at = int(ctx.guild.created_at.timestamp())
        member_count = guild.member_count
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        category_channels = len(guild.categories)
        verification_level = str(guild.verification_level)
        server_icon_url = str(guild.icon) if guild.icon else None
        embed = discord.Embed(title="Server Info:", color=Colors.default)
        embed.set_thumbnail(url=server_icon_url)
        embed.add_field(name="Server ID", value=server_id, inline=False)
        embed.add_field(name="Owner", value=server_owner, inline=False)
        embed.add_field(name="Server Created", value=f"<t:{server_created_at}:R>", inline=False)
        embed.add_field(name="Members", value=f"Total: {member_count}", inline=False)
        embed.add_field(name="Channels", value=f"Text: {text_channels}\nVoice: {voice_channels}\nCategories: {category_channels}", inline=False)
        embed.add_field(name="Verification Level", value=verification_level, inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='clearsnipe', aliases=['cs'])
    @commands.bot_has_guild_permissions(manage_messages=True)
    async def clearsnipe(self, ctx):
        channel_id = ctx.channel.id
        if channel_id in self.deleted_messages:
            del self.deleted_messages[channel_id]
            await ctx.message.add_reaction("👍")

    @commands.hybrid_command(aliases=["mc"], help="Check how many members does your server have", description="Utility")
    async def membercount(self, ctx):
        b = len(set(b for b in ctx.guild.members if b.bot))
        h = len(set(b for b in ctx.guild.members if not b.bot))
        embed = discord.Embed(color=Colors.default)
        embed.set_author(name=f"{ctx.guild.name}'s member count", icon_url=ctx.guild.icon)
        embed.add_field(name="Members", value=h)
        embed.add_field(name="Total", value=ctx.guild.member_count)
        embed.add_field(name="Bots", value=b)
        await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=["rs"], help="Check the latest reaction removal of a channel", usage="<channel>", description="Utility")
    async def reactionsnipe(self, ctx, *, channel: TextChannel=None):
        channel = channel or ctx.channel
        try:
            em = discord.Embed(color=Colors.default, description=f"{reaction_message_emoji_name[channel.id]}\n[Emoji link]({reaction_message_emoji_url[channel.id]})\n[Message link](https://discord.com/channels/{ctx.guild.id}/{channel.id}/{reaction_message_id[channel.id]})")
            em.set_author(name=reaction_message_author[channel.id], icon_url=reaction_message_author_avatar[channel.id])
            em.set_image(url=reaction_message_emoji_url[channel.id])
            await ctx.send(embed=em)
        except KeyError:
            await ctx.send(f"There is no deleted reaction in {channel.mention}")

    @commands.hybrid_command(aliases=["es"], help="Check the latest edited message from a channel", usage="<channel>", description="Utility")
    async def editsnipe(self, ctx, *, channel: TextChannel=None):
        channel = channel or ctx.channel
        try:
            em = discord.Embed(color=Colors.default, description=f"Edited message in {channel.mention} - [Jump](https://discord.com/channels/{ctx.guild.id}/{channel.id}/{edit_message_id[channel.id]})")
            em.set_author(name=edit_message_author[channel.id], icon_url=edit_message_author_avatar[channel.id])
            em.add_field(name="Old", value=edit_message_content1[channel.id], inline=False)
            em.add_field(name="New", value=edit_message_content2[channel.id], inline=False)
            await ctx.send(embed=em)
        except KeyError:
            await ctx.send(f"There is no edited message in {channel.mention}")

async def setup(bot: DiscordBot):
    await bot.add_cog(Utility(bot))
