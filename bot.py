import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging
import os
import datetime
import discord_ios
import aiosqlite
from backend.classes import Colors, Emojis
from database import DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')

# Load environment variables
load_dotenv()

# Intents setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

class DiscordBot(commands.Bot):
    def __init__(self, intents):
        super().__init__(command_prefix=self.dynamic_prefix, intents=intents, help_command=None)
        self.database = None
        self.start_time = datetime.datetime.now(datetime.timezone.utc)  # Make start_time timezone-aware
        self.uptime = None

    async def on_ready(self):
        current_time = datetime.datetime.now(datetime.timezone.utc)
        self.uptime = current_time - self.start_time
        if self.uptime:
            uptime_days = self.uptime.days if self.uptime.days is not None else 0
            uptime_hours = self.uptime.seconds // 3600
            uptime_minutes = (self.uptime.seconds % 3600) // 60
            logging.info(f"Bot is online. Uptime: {uptime_days} days, {uptime_hours} hours, {uptime_minutes} minutes")
        else:
            logging.error("Uptime is None.")


    async def dynamic_prefix(self, bot, message):
        """Dynamically get the prefix for the guild from the database."""
        if not message.guild:
            return commands.when_mentioned_or("!")(bot, message)
        prefix = await self.get_server_prefix(message.guild.id)
        return commands.when_mentioned_or(prefix)(bot, message)

    async def get_server_prefix(self, guild_id):
        """Utility function to fetch the current guild prefix."""
        default_prefix = "!"  # Default to '!' or retrieve from a config/environment variable
        try:
            async with self.database.connection.execute("SELECT prefix FROM guild_prefixes WHERE guild_id = ?", (guild_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else default_prefix
        except Exception as e:
            logging.error(f"Failed to fetch prefix for guild {guild_id}: {e}")
            return default_prefix

    async def init_db(self):
        self.database = DatabaseManager(connection=await aiosqlite.connect('database/database.db'))
        schema_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "database", "schema.sql")
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as schema_file:
                schema_sql = schema_file.read()
            logging.info("Executing schema SQL script.")
            await self.database.connection.executescript(schema_sql)
            await self.database.connection.commit()

    async def setup_hook(self):
        await self.init_db()
        await self.load_cogs()

    async def load_cogs(self):
        cogs_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "cogs")
        for file in os.listdir(cogs_dir):
            if file.endswith(".py"):
                extension = file[:-3]
                try:
                    await self.load_extension(f"cogs.{extension}")
                    logging.info(f"Loaded extension '{extension}'")
                except Exception as e:
                    logging.error(f"Failed to load extension {extension}.", exc_info=True)

    async def on_message(self, message):
        if message.author.bot:
            return
        if message.content.strip() == f"<@!{self.user.id}>":
            prefix = await self.get_server_prefix(message.guild.id if message.guild else None)
            await message.channel.send(f"My prefix here is `{prefix}`.")
        await self.process_commands(message)

    async def on_command_error(self, context, error):
        if isinstance(error, commands.CommandNotFound):
            prefix = await self.get_server_prefix(context.guild.id if context.guild else None)
            embed = discord.Embed(
                description=f"{Emojis.warning} Command not found. Use `{prefix}help` for a list of commands.",
                color=Colors.yellow
            )
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

bot = DiscordBot(intents=intents)
bot.run(os.getenv("TOKEN"))
