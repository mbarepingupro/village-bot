"""
mbarepingu Village Bot — bot.py
================================
Entry point. Loads config and all feature modules (cogs).
"""

import asyncio
import discord
from discord.ext import commands
from config import BOT_TOKEN, COMMAND_PREFIX, BOT_CHANNEL_NAME

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, help_command=None)

COGS = [
    "cogs.data",       # shared save/load layer
    "cogs.guild",      # guild contributions and upgrades
    "cogs.character",  # !join, !profile, !inventory
    "cogs.gather",     # !gather, !craft
    "cogs.economy",    # !gold, !sell, !shop, !buy, !equip
    "cogs.loot",       # !startloot, !loot
    "cogs.items",      # !use
    "cogs.trade",     # !trade, !accept, !decline
    "cogs.help",       # !help
]

@bot.event
async def on_ready():
    print(f"✅  {bot.user} is online!")

@bot.check
async def only_in_bot_channel(ctx):
    if BOT_CHANNEL_NAME and ctx.channel.name != BOT_CHANNEL_NAME:
        return False
    return True

async def main():
    async with bot:
        for cog in COGS:
            await bot.load_extension(cog)
            print(f"    ✔ loaded {cog}")
        await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
