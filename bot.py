"""
mbarepingu Village Bot v2 — bot.py
====================================
Cosmetic-focused redesign.
Channel behaviour:
  - DMs: all commands always work
  - Village channel: public commands respond there, others send DM + brief notice
  - Other channels: ignored
"""

import asyncio
import time
import discord
from discord.ext import commands
from config import (
    BOT_TOKEN, COMMAND_PREFIX, BOT_CHANNEL_NAME,
    GO_LIVE_CHANNEL, GO_LIVE_TRIGGER, VILLAGE_CHANNEL,
    LOOT_WINDOW_SECONDS
)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, help_command=None)

# Commands that respond publicly in the village channel
PUBLIC_COMMANDS = {
    "gather", "join", "loot", "craft", "equip",
    "startloot", "endloot", "village"
}

COGS = [
    "cogs.data",
    "cogs.character",
    "cogs.gather",
    "cogs.craft",
    "cogs.loot",
    "cogs.village",
    "cogs.help",
]

@bot.event
async def on_ready():
    print(f"✅  {bot.user} is online!")

@bot.check
async def routing(ctx):
    command_name = ctx.command.name if ctx.command else ""
    is_dm        = isinstance(ctx.channel, discord.DMChannel)
    channel_name = getattr(ctx.channel, 'name', '')

    # DMs: always allow
    if is_dm:
        return True

    # Outside village channel: ignore
    if BOT_CHANNEL_NAME and channel_name != BOT_CHANNEL_NAME:
        return False

    # Public commands respond in channel
    if command_name in PUBLIC_COMMANDS:
        return True

    # All other commands: DM the user
    try:
        dm_channel = await ctx.author.create_dm()
        notice = await ctx.send(f"📬 {ctx.author.mention} check your DMs!")
        original_send = ctx.send
        async def dm_send(*args, **kwargs):
            kwargs.pop('delete_after', None)
            return await dm_channel.send(*args, **kwargs)
        ctx.send = dm_send
        async def cleanup():
            await asyncio.sleep(5)
            try:
                await notice.delete()
            except Exception:
                pass
        asyncio.create_task(cleanup())
    except discord.Forbidden:
        await ctx.send(f"📬 {ctx.author.mention} please enable DMs to receive bot responses!")
        return False

    return True

@bot.event
async def on_message(message):
    if isinstance(message.channel, discord.DMChannel):
        await bot.process_commands(message)
        return

    # ── Auto-loot trigger ─────────────────────────────────────────────────────
    if (
        message.author != bot.user and
        getattr(message.channel, 'name', '') == GO_LIVE_CHANNEL and
        GO_LIVE_TRIGGER.lower() in message.content.lower()
    ):
        from cogs.data import load_data, save_data
        data = load_data()

        if not data.get("loot_active"):
            data["loot_active"]   = True
            data["loot_end_time"] = time.time() + LOOT_WINDOW_SECONDS
            data["loot_claimers"] = []
            save_data(data)

            mins       = LOOT_WINDOW_SECONDS // 60
            village_ch = discord.utils.get(message.guild.text_channels, name=VILLAGE_CHANNEL)

            await message.channel.send(
                f"🎟️ Loot drop activated! Head to "
                f"{village_ch.mention if village_ch else '#' + VILLAGE_CHANNEL} "
                f"and type `!loot` to claim your tokens!"
            )

            if village_ch:
                await village_ch.send(
                    f"🔴 **mbarepingu is LIVE!**\n"
                    f"🎟️ **LOOT TOKEN DROP!**\n"
                    f"Type `!loot` in the next **{mins} minutes** to claim your tokens!\n"
                    f"Tokens are needed to craft cosmetics. Don't miss out!"
                )
            print(f"✅ Auto-loot triggered.")

    await bot.process_commands(message)

async def main():
    async with bot:
        for cog in COGS:
            await bot.load_extension(cog)
            print(f"    ✔ loaded {cog}")
        await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
