"""
cogs/loot.py — Stream loot drop event
=======================================
Commands:
  !startloot  (mod only) — opens the loot window
  !endloot    (mod only) — force-closes the window early
  !loot       (everyone) — claim during the window

Rewards: 1-5 loot tokens + small guild resource bonus.
Window: 30 minutes (auto-triggered by Streamcord or manual !startloot).
One claim per user per session.
"""

import time
import random
import discord
from discord.ext import commands
from config import (
    GUILDS, ITEMS, LOOT_WINDOW_SECONDS,
    LOOT_TOKEN_RANGE, LOOT_RESOURCE_BONUS,
    XP_PER_LOOT, XP_PER_LEVEL,
)
from cogs.data import (
    load_data, save_data, get_player,
    add_item, add_xp, fmt_time, data_lock, user_lock, is_mod
)


class LootCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ── !startloot ────────────────────────────────────────────────────────────
    @commands.command(name="startloot")
    async def startloot(self, ctx):
        """[MOD] Open the loot window."""
        if not is_mod(ctx):
            await ctx.send("❌ Only mods can start a loot drop.")
            return

        async with data_lock:
            data = load_data()
            if data.get("loot_active"):
                await ctx.send("⚠️ A loot window is already open!")
                return
            data["loot_active"]   = True
            data["loot_end_time"] = time.time() + LOOT_WINDOW_SECONDS
            data["loot_claimers"] = []
            save_data(data)

        mins = LOOT_WINDOW_SECONDS // 60
        await ctx.send(
            f"🔴 **STREAM IS LIVE!**\n"
            f"🎟️ Type `!loot` in the next **{mins} minutes** to claim your **Loot Tokens**!\n"
            f"Tokens are required to craft cosmetics. Don't miss out!"
        )

    # ── !endloot ──────────────────────────────────────────────────────────────
    @commands.command(name="endloot")
    async def endloot(self, ctx):
        """[MOD] Force-close the loot window."""
        if not is_mod(ctx):
            await ctx.send("❌ Only mods can end a loot drop.")
            return

        async with data_lock:
            data = load_data()
            if not data.get("loot_active"):
                await ctx.send("⚠️ No loot window is currently open.")
                return
            count = len(data.get("loot_claimers", []))
            data["loot_active"]   = False
            data["loot_end_time"] = 0
            save_data(data)

        await ctx.send(f"🔒 Loot window closed. **{count}** players claimed tokens.")

    # ── !loot ─────────────────────────────────────────────────────────────────
    @commands.command(name="loot")
    async def loot(self, ctx):
        """Claim your loot tokens during a live stream."""
        try:
            if user_lock(ctx.author.id, "loot").locked():
                return

            async with user_lock(ctx.author.id, "loot"):
                async with data_lock:
                    data   = load_data()
                    player = get_player(data, ctx.author)

                    # Window checks
                    if not data.get("loot_active"):
                        await ctx.send(
                            "🔒 No loot drop is active right now. "
                            "Watch for the next stream!"
                        )
                        return

                    if time.time() > data.get("loot_end_time", 0):
                        data["loot_active"] = False
                        save_data(data)
                        await ctx.send("⌛ The loot window just closed!")
                        return

                    # One claim per session
                    uid = str(ctx.author.id)
                    if uid in data.get("loot_claimers", []):
                        remaining = int(data["loot_end_time"] - time.time())
                        await ctx.send(
                            f"✋ {ctx.author.mention} You already claimed this session! "
                            f"Window closes in {fmt_time(remaining)}."
                        )
                        return

                    # Must have a guild (for resource bonus)
                    if player["guild"] is None:
                        await ctx.send(
                            f"⚠️ {ctx.author.mention} Join a guild first with `!join` to claim loot!"
                        )
                        return

                    # ── Roll tokens ───────────────────────────────────────────
                    tokens = random.randint(*LOOT_TOKEN_RANGE)
                    add_item(player, "loot_token", tokens)

                    # ── Bonus guild resources ─────────────────────────────────
                    guild_cfg = GUILDS.get(player["guild"], {})
                    resources = guild_cfg.get("resources", [])
                    bonus_resources = {}
                    for res_id in resources:
                        qty = random.randint(*LOOT_RESOURCE_BONUS)
                        add_item(player, res_id, qty)
                        bonus_resources[res_id] = qty

                    # ── Mark claimed + XP ─────────────────────────────────────
                    data.setdefault("loot_claimers", []).append(uid)
                    player["stats"]["total_streams"] = player["stats"].get("total_streams", 0) + 1
                    levelled = add_xp(player, XP_PER_LOOT, XP_PER_LEVEL)
                    save_data(data)

                # ── Build response ────────────────────────────────────────────
                total_tokens = player["inventory"].get("loot_token", 0)

                token_msg = f"🎟️ **+{tokens} Loot Token{'s' if tokens != 1 else ''}!**"
                if tokens == LOOT_TOKEN_RANGE[1]:
                    token_msg += " 🎉 **MAX ROLL!**"
                token_msg += f" (total: {total_tokens})"

                bonus_str = "  ".join(
                    f"{ITEMS[k]['emoji']} +{v} {ITEMS[k]['name']}"
                    for k, v in bonus_resources.items()
                )

                msg = (
                    f"🎁 **{ctx.author.display_name}** claimed their loot!\n"
                    f"{token_msg}\n"
                    f"{bonus_str}"
                )
                if levelled:
                    msg += f"\n⬆️ **LEVEL UP! Now level {player['level']}!**"

                await ctx.send(msg)

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")


async def setup(bot):
    await bot.add_cog(LootCog(bot))
