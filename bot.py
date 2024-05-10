import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import json
import logging
import os
import platform
import random
import sys
import aiosqlite

from database import DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')

# Load environment variables
load_dotenv()

# Intents setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

# Define the get_prefix function correctly outside of the class
async def get_prefix(bot, message):
    default_prefix = '!'  # This should be configurable
    if not message.guild:
        return commands.when_mentioned_or(default_prefix)(bot, message)
    async with bot.database.connection.execute("SELECT prefix FROM guild_prefixes WHERE guild_id = ?", (message.guild.id,)) as cursor:
        prefix = await cursor.fetchone()
        return commands.when_mentioned_or(prefix[0] if prefix else default_prefix)(bot, message)

class DiscordBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=get_prefix, intents=intents, help_command=None)
        self.database = None

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
        self.status_task.start()

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

    @tasks.loop(minutes=1)
    async def status_task(self):
        statuses = ["dev", "hiddeout"]
        await self.change_presence(activity=discord.Game(random.choice(statuses)))

    @status_task.before_loop
    async def before_status_task(self):
        await self.wait_until_ready()

    async def on_message(self, message):
        if message.author.bot:
            return
        await self.process_commands(message)

    async def on_command_error(self, context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await context.send("This command is on cooldown.")
        elif isinstance(error, commands.CheckFailure):
            await context.send("You do not have permission to use this command.")
        else:
            logging.error("Unhandled command error: %s", str(error), exc_info=True)
            await context.send(f"An error occurred: {str(error)}")

bot = DiscordBot()
bot.run(os.getenv("TOKEN"))
