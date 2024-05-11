import discord
from discord.ext import commands

class MyHelp(commands.MinimalHelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Help")
        for cog, commands in mapping.items():
            filtered = await self.filter_commands(commands, sort=True)
            if filtered:  # Check if filtered is not None
                command_signatures = [self.get_command_signature(c) for c in filtered]
                if command_signatures:
                    cog_name = getattr(cog, "qualified_name", "No Category")
                    embed.add_field(name=cog_name, value="\n".join(command_signatures), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

async def setup(bot):
    bot.help_command = MyHelp()
    return bot.help_command
