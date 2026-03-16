"""
mbarepingu Village Bot — bot.py
================================
Entry point. Loads config and all feature modules (cogs).
"""

import asyncio
import time
import discord
from discord.ext import commands
from config import (
    BOT_TOKEN, COMMAND_PREFIX, BOT_CHANNEL_NAME,
    GO_LIVE_CHANNEL, GO_LIVE_TRIGGER, VILLAGE_CHANNEL, LOOT_WINDOW_SECONDS
)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, help_command=None)

COGS = [
    "cogs.data",       # shared save/load layer
    "cogs.guild",      # guild contributions and upgrades
    "cogs.character",  # !join, !character, !inventory
    "cogs.gather",     # !gather, !craft
    "cogs.economy",    # !gold, !sell, !shop, !buy, !equip, !prices
    "cogs.loot",       # !startloot, !loot
    "cogs.items",      # !use
    "cogs.trade",      # !trade, !accept, !decline
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

@bot.event
async def on_message(message):
    # ── Auto-loot trigger ─────────────────────────────────────────────────────
    # Fires when Streamcord posts in the go-live channel.
    if (
        message.author != bot.user and
        message.channel.name == GO_LIVE_CHANNEL and
        GO_LIVE_TRIGGER.lower() in message.content.lower()
    ):
        from cogs.data import load_data, save_data
        data = load_data()

        if not data.get("loot_active"):
            data["loot_active"]   = True
            data["loot_end_time"] = time.time() + LOOT_WINDOW_SECONDS
            data["loot_claimers"] = []
            save_data(data)

            mins = LOOT_WINDOW_SECONDS // 60

            # Short confirmation in go-live channel
            await message.channel.send(
                f"🎁 Loot drop activated! Head to <#{message.guild.get_channel_named(VILLAGE_CHANNEL).id if message.guild.get_channel_named(VILLAGE_CHANNEL) else VILLAGE_CHANNEL}> "
                f"and type `!loot` to claim your rewards!"
            )

            # Full announcement in village channel
            village_ch = discord.utils.get(message.guild.text_channels, name=VILLAGE_CHANNEL)
            if village_ch:
                await village_ch.send(
                    f"🔴 **mbarepingu is LIVE!**\n"
                    f"🎁 **LOOT DROP ACTIVATED!**\n"
                    f"Type `!loot` in the next **{mins} minutes** to claim your rewards!\n"
                    f"Higher level = better drops. Guild members get exclusive items!"
                )

            print(f"✅ Auto-loot triggered by Streamcord notification.")

    # Required so commands still work alongside on_message
    await bot.process_commands(message)

async def main():
    async with bot:
        for cog in COGS:
            await bot.load_extension(cog)
            print(f"    ✔ loaded {cog}")
        await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
