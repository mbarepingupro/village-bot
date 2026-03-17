"""
mbarepingu Village Bot — bot.py
================================
Entry point. Loads config and all feature modules (cogs).

Channel behaviour:
  - Public commands (answer in channel): !gather, !join, !loot, !contribute, !trade, !accept, !decline
  - DM commands (answer via DM): everything else
  - Trade commands: trade channel only
"""

import asyncio
import time
import discord
from discord.ext import commands
from config import (
    BOT_TOKEN, COMMAND_PREFIX, BOT_CHANNEL_NAME,
    GO_LIVE_CHANNEL, GO_LIVE_TRIGGER, VILLAGE_CHANNEL,
    TRADE_CHANNEL, LOOT_WINDOW_SECONDS
)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, help_command=None)

# Commands that respond publicly in the village channel
PUBLIC_COMMANDS = {
    "gather", "join", "loot", "contribute", "donate",
    "trade", "accept", "decline", "canceltrade", "tradeoffer", "offers",
    "startloot", "endloot", "addgold"  # mod commands stay public
}

COGS = [
    "cogs.data",
    "cogs.guild",
    "cogs.character",
    "cogs.gather",
    "cogs.economy",
    "cogs.loot",
    "cogs.items",
    "cogs.trade",
    "cogs.help",
]

@bot.event
async def on_ready():
    print(f"✅  {bot.user} is online!")

@bot.check
async def channel_and_dm_routing(ctx):
    """
    Route commands:
    - DMs: always allowed
    - Trade commands: only in trade channel
    - Public commands: respond in village channel
    - Everything else: respond via DM
    """
    channel_name = ctx.channel.name if hasattr(ctx.channel, 'name') else ""
    command_name = ctx.command.name if ctx.command else ""

    # Always allow DMs
    if isinstance(ctx.channel, discord.DMChannel):
        return True

    # Trade commands — only in trade channel
    if command_name in {"trade", "accept", "decline", "canceltrade", "tradeoffer", "offers"}:
        if channel_name != TRADE_CHANNEL:
            trade_ch = discord.utils.get(ctx.guild.text_channels, name=TRADE_CHANNEL)
            if trade_ch:
                await ctx.send(f"🤝 Trades happen in {trade_ch.mention}!")
            return False
        return True

    # Only respond in the village channel for server messages
    if BOT_CHANNEL_NAME and channel_name != BOT_CHANNEL_NAME:
        return False

    # DM-only commands — send DM and post a small notice
    if command_name and command_name not in PUBLIC_COMMANDS:
        try:
            notice = await ctx.send(f"📬 {ctx.author.mention} check your DMs!")
            ctx.channel = await ctx.author.create_dm()
            await asyncio.sleep(5)
            try:
                await notice.delete()
            except Exception:
                pass
        except discord.Forbidden:
            await ctx.send(f"📬 {ctx.author.mention} please enable DMs so I can respond privately!")
            return False

    return True

@bot.event
async def on_message(message):
    # ── Auto-loot trigger ─────────────────────────────────────────────────────
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

            # Short note in go-live channel
            await message.channel.send(
                f"🎁 Loot drop activated! Head to "
                f"{discord.utils.get(message.guild.text_channels, name=VILLAGE_CHANNEL).mention} "
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

    await bot.process_commands(message)

async def main():
    async with bot:
        for cog in COGS:
            await bot.load_extension(cog)
            print(f"    ✔ loaded {cog}")
        await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
