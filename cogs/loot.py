"""
cogs/loot.py — Stream loot drop event
=======================================
Commands:
  !startloot  (mod only) — opens the loot window
  !endloot    (mod only) — force-closes the window early
  !loot       (everyone) — claim during the window
"""

import time
import random
import discord
from discord.ext import commands
from config import (
    GUILDS, ITEMS, MOD_ROLE_NAMES,
    COOLDOWNS, LOOT_WINDOW_SECONDS,
    XP_PER_LOOT, XP_PER_LEVEL, GOLD_LOOT_REWARD
)
from cogs.data import (
    load_data, save_data, get_player,
    add_item, add_gold, cooldown_remaining, set_cooldown, add_xp, fmt_time, fmt_gold
)

# ── Loot tables ───────────────────────────────────────────────────────────────
# Each entry: (item_id, min_qty, max_qty, weight)
# Higher weight = more likely to be picked.
# Add more rows to make loot richer.

BASE_LOOT_TABLE = [
    ("wood",   2, 6,  40),
    ("stone",  1, 4,  40),
    ("fish",   1, 3,  30),
    ("herbs",  1, 2,  20),
]

RARE_LOOT_TABLE = [
    ("stream_command_slot", 1, 1, 5),
    ("jester_hat",          1, 1, 8),
    ("inmate_outfit",       1, 1, 8),
]

# ── Helper ────────────────────────────────────────────────────────────────────

def is_mod(ctx) -> bool:
    if isinstance(ctx.author, discord.Member):
        return any(r.name in MOD_ROLE_NAMES for r in ctx.author.roles)
    return False

def weighted_pick(table):
    items   = [(i, mn, mx) for i, mn, mx, _ in table]
    weights = [w for _, _, _, w in table]
    return random.choices(items, weights=weights, k=1)[0]

def roll_loot(player: dict) -> list[tuple[str, int]]:
    """
    Roll a loot bundle for a player based on their level and guild.
    Returns list of (item_id, qty).
    """
    results = {}

    # Base drop: 2–3 common items
    for _ in range(random.randint(2, 3)):
        item_id, mn, mx = weighted_pick(BASE_LOOT_TABLE)
        qty = random.randint(mn, mx)
        results[item_id] = results.get(item_id, 0) + qty

    # Level bonus: extra item every 5 levels
    if player["level"] >= 5:
        item_id, mn, mx = weighted_pick(BASE_LOOT_TABLE)
        results[item_id] = results.get(item_id, 0) + random.randint(mn, mx)

    # Rare roll: ~15% chance
    if random.random() < 0.15:
        item_id, mn, mx = weighted_pick(RARE_LOOT_TABLE)
        results[item_id] = results.get(item_id, 0) + random.randint(mn, mx)

    # Guild exclusive drop: ~25% chance
    if player["guild"] and player["guild"] in GUILDS:
        if random.random() < 0.25:
            exclusive = GUILDS[player["guild"]]["loot_item"]
            results[exclusive] = results.get(exclusive, 0) + 1

    return list(results.items())


class LootCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ── !startloot ────────────────────────────────────────────────────────────
    @commands.command(name="startloot")
    async def startloot(self, ctx):
        """[MOD] Open the loot window. Everyone has 5 minutes to !loot."""
        if not is_mod(ctx):
            await ctx.send("❌ Only mods can start a loot drop.")
            return

        data = load_data()
        if data.get("loot_active"):
            await ctx.send("⚠️ A loot window is already open!")
            return

        data["loot_active"]   = True
        data["loot_end_time"] = time.time() + LOOT_WINDOW_SECONDS
        data["loot_claimers"] = []   # track who claimed this session
        save_data(data)

        mins = LOOT_WINDOW_SECONDS // 60
        await ctx.send(
            f"🎁 **LOOT DROP!** The stream is live!\n"
            f"Type `!loot` in the next **{mins} minutes** to claim your rewards!\n"
            f"Higher level = better drops. Guild members get exclusive items!"
        )

    # ── !endloot ──────────────────────────────────────────────────────────────
    @commands.command(name="endloot")
    async def endloot(self, ctx):
        """[MOD] Force-close the loot window early."""
        if not is_mod(ctx):
            await ctx.send("❌ Only mods can end a loot drop.")
            return

        data = load_data()
        if not data.get("loot_active"):
            await ctx.send("⚠️ No loot window is currently open.")
            return

        count = len(data.get("loot_claimers", []))
        data["loot_active"]   = False
        data["loot_end_time"] = 0
        save_data(data)

        await ctx.send(f"🔒 Loot window closed. **{count}** players claimed drops.")

    # ── !loot ─────────────────────────────────────────────────────────────────
    @commands.command(name="loot")
    async def loot(self, ctx):
        """Claim your loot during a live stream loot drop."""
        data   = load_data()
        player = get_player(data, ctx.author)

        # Window check
        if not data.get("loot_active"):
            await ctx.send("🔒 No loot drop is active right now. Watch for `!startloot` when the stream goes live!")
            return

        if time.time() > data.get("loot_end_time", 0):
            data["loot_active"] = False
            save_data(data)
            await ctx.send("⌛ The loot window just closed!")
            return

        uid = str(ctx.author.id)
        if uid in data.get("loot_claimers", []):
            remaining = int(data["loot_end_time"] - time.time())
            await ctx.send(
                f"✋ {ctx.author.mention} You already claimed your loot this session! "
                f"Window closes in {fmt_time(remaining)}."
            )
            return

        # Must be in a guild to claim
        if player["guild"] is None:
            await ctx.send(
                f"⚠️ {ctx.author.mention} Join a guild first with `!join` to claim loot!"
            )
            return

        # Roll and give loot
        drops = roll_loot(player)
        for item_id, qty in drops:
            add_item(player, item_id, qty)

        # Gold reward
        gold_gained = round(random.uniform(*GOLD_LOOT_REWARD), 1)
        add_gold(player, gold_gained)

        data.setdefault("loot_claimers", []).append(uid)
        player["stats"]["total_loots"] += 1
        levelled = add_xp(player, XP_PER_LOOT, XP_PER_LEVEL)
        save_data(data)

        # Format response
        guild_cfg = GUILDS.get(player["guild"], {})
        drop_lines = []
        for item_id, qty in drops:
            item = ITEMS.get(item_id, {"name": item_id, "emoji": "❓"})
            drop_lines.append(f"{item['emoji']} **{item['name']}** x{qty}")

        msg = (
            f"🎁 {guild_cfg.get('emoji','')} **{ctx.author.display_name}** ({player['class']}) "
            f"claimed their loot:\n" + "\n".join(drop_lines) +
            f"\n💰 +**{gold_gained} gold** (total: {player['gold']})"
        )
        if levelled:
            msg += f"\n⬆️ **LEVEL UP! Now level {player['level']}!**"

        await ctx.send(msg)


async def setup(bot):
    await bot.add_cog(LootCog(bot))
