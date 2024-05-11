import os
import discord
from discord.ext import commands
import aiosqlite
import json

class Jail(commands.Cog, name="Jail"):
    def __init__(self, bot):
        self.bot = bot
        # Ensure the database directory exists
        db_dir = os.path.join(os.path.dirname(__file__), 'database')
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        self.db_path = os.path.join(db_dir, 'database.db')
        self.schema_path = os.path.join(db_dir, 'schema.sql')

        # Connect to the database
        self.bot.loop.create_task(self.init_db())

    async def init_db(self):
        """Initializes the database and creates tables as per schema.sql."""
        self.bot.db = await aiosqlite.connect(self.db_path)
        # Use executescript to run SQL commands from the schema file
        with open(self.schema_path, 'r') as schema_file:
            schema_sql = schema_file.read()
        await self.bot.db.executescript(schema_sql)
        await self.bot.db.commit()

    async def close(self):
        """Close the database connection when the bot is shutting down."""
        await self.bot.db.close()

    @commands.command(name="setjail", description="Sets the jail role and channel for the server.")
    @commands.has_permissions(administrator=True)
    async def setjail(self, ctx: commands.Context):
        async with self.bot.db.execute("SELECT * FROM setme WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
            if await cursor.fetchone():
                return await ctx.send("Jail is already set up.")
            
            role = await ctx.guild.create_role(name="Jail", reason="Create jail role")
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                role: discord.PermissionOverwrite(read_messages=True)
            }
            channel = await ctx.guild.create_text_channel("jail", overwrites=overwrites, reason="Create jail channel")

            await self.bot.db.execute("INSERT INTO setme (channel_id, role_id, guild_id) VALUES (?, ?, ?)", 
                                      (channel.id, role.id, ctx.guild.id))
            await self.bot.db.commit()
            await ctx.send(f"Jail set up with channel {channel.mention} and role {role.mention}.")

    @commands.command(name="jail", description="Jails a member.")
    @commands.has_permissions(manage_roles=True)
    async def jail(self, ctx: commands.Context, member: discord.Member, *, reason="No reason provided"):
        async with self.bot.db.execute("SELECT role_id FROM setme WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
            result = await cursor.fetchone()
            if not result:
                return await ctx.send("Jail not configured. Use `setjail` first.")
            
            jail_role_id = result[0]
            jail_role = ctx.guild.get_role(jail_role_id)
            if not jail_role:
                return await ctx.send("Jail role does not exist. Reset the jail with `setjail`.")

            roles = [role.id for role in member.roles if role.id != ctx.guild.default_role.id]
            await member.edit(roles=[jail_role], reason=reason)

            roles_json = json.dumps(roles)
            await self.bot.db.execute("REPLACE INTO jail (guild_id, user_id, roles) VALUES (?, ?, ?)",
                                      (ctx.guild.id, member.id, roles_json))
            await self.bot.db.commit()
            await ctx.send(f"{member.mention} has been jailed for: {reason}")

    @commands.command(name="unjail", description="Releases a member from jail.")
    @commands.has_permissions(manage_roles=True)
    async def unjail(self, ctx: commands.Context, member: discord.Member):
        async with self.bot.db.execute("SELECT roles FROM jail WHERE guild_id = ? AND user_id = ?",
                                       (ctx.guild.id, member.id)) as cursor:
            result = await cursor.fetchone()
            if not result:
                return await ctx.send(f"{member.mention} is not jailed.")

            roles_ids = json.loads(result[0])
            roles = [ctx.guild.get_role(role_id) for role_id in roles_ids if ctx.guild.get_role(role_id)]
            await member.edit(roles=roles, reason="Release from jail")

            await self.bot.db.execute("DELETE FROM jail WHERE guild_id = ? AND user_id = ?",
                                      (ctx.guild.id, member.id))
            await self.bot.db.commit()
            await ctx.send(f"{member.mention} has been released from jail.")

async def setup(bot):
    jail = Jail(bot)
    await jail.init_db()
    bot.add_cog(jail)

async def close(bot):
    await bot.get_cog('Jail').close()