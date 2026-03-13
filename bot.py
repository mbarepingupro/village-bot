"""
mbarepingu Village Bot — bot.py
================================
Entry point. Loads config and all feature modules (cogs).
You rarely need to edit this file.
"""

import asyncio
import discord
from discord.ext import commands
from config import BOT_TOKEN, COMMAND_PREFIX

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, help_command=None)

COGS = [
    "cogs.data",       # shared save/load layer
    "cogs.character",  # !join, !character, !inventory
    "cogs.gather",     # !gather, !craft
    "cogs.economy",    # !gold, !sell, !shop, !buy, !equip
    "cogs.loot",       # !startloot, !loot
    "cogs.help",       # !help
]

@bot.event
async def on_ready():
    print(f"✅  {bot.user} is online!")

async def main():
    async with bot:
        for cog in COGS:
            await bot.load_extension(cog)
            print(f"    ✔ loaded {cog}")
        await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
