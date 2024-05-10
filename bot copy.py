import json
import logging
import os
import platform
import random
import sys

import aiosqlite
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
from dotenv import load_dotenv

from database import DatabaseManager

if not os.path.isfile(f"{os.path.realpath(os.path.dirname(__file__))}/config.json"):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open(f"{os.path.realpath(os.path.dirname(__file__))}/config.json") as file:
        config = json.load(file)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

logger = logging.getLogger("discord_bot")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
file_handler = logging.FileHandler(filename='discord.log', mode='w', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(console_handler)
logger.addHandler(file_handler)

class DiscordBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=self.get_prefix, intents=intents, help_command=None)
        self.config = config
        self.database = None

    @staticmethod
    async def get_prefix(bot, message):
        default_prefix = '!'  # Default to '!' if not found in the database
        if not message.guild:
            return commands.when_mentioned_or(default_prefix)(bot, message)
        async with bot.database.connection.execute("SELECT prefix FROM guild_prefixes WHERE guild_id = ?", (message.guild.id,)) as cursor:
            prefix = await cursor.fetchone()
            return commands.when_mentioned_or(prefix[0] if prefix else default_prefix)(bot, message)

    async def init_db(self):
        db_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "database", "database.db")
        self.database = DatabaseManager(connection=await aiosqlite.connect(db_path))
        schema_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "database", "schema.sql")
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as schema_file:
                schema_sql = schema_file.read()
            
            logger.info("Executing schema SQL script.")
            
            await self.database.connection.executescript(schema_sql)
            await self.database.connection.commit()
        else:
            logger.error("schema.sql file not found, ensure it's located at " + schema_path)

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
                    logger.info(f"Loaded extension '{extension}'")
                except Exception as e:
                    logger.error(f"Failed to load extension {extension}.", exc_info=e)

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
            logger.error("Unhandled command error: %s", str(error), exc_info=error)
            raise error

load_dotenv()
bot = DiscordBot()
bot.run(os.getenv("TOKEN"))
