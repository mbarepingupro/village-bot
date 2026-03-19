"""
cogs/data.py — Shared data layer
=================================
All other cogs import from here. Never access village_data.json directly.

CONCURRENCY PROTECTION:
- data_lock      : asyncio.Lock — wrap ALL read+write operations with this
- user_lock(...) : per-user per-action lock — prevents spam duplicates
- save_data()    : atomic write (temp file + rename) — no corrupt saves
"""

import json, os, time, asyncio
import discord
from discord.ext import commands
from config import DATA_FILE

# ── Global file lock ──────────────────────────────────────────────────────────
data_lock = asyncio.Lock()

# ── Per-user per-action lock ──────────────────────────────────────────────────
_user_locks: dict[str, asyncio.Lock] = {}

def user_lock(user_id: int, action: str) -> asyncio.Lock:
    key = f"{user_id}:{action}"
    if key not in _user_locks:
        _user_locks[key] = asyncio.Lock()
    return _user_locks[key]

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"players": {}, "loot_active": False, "loot_end_time": 0}

def save_data(data: dict):
    """Atomic write — uses a temp file + os.replace to prevent corrupt saves."""
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, DATA_FILE)

def get_player(data: dict, user) -> dict:
    """Get or create a player record."""
    uid = str(user.id)
    if uid not in data["players"]:
        data["players"][uid] = {
            "name":          user.display_name,
            "guild":         None,
            "class":         None,
            "xp":            0,
            "level":         1,
            "gold":          0.0,
            "inventory":     {},
            "cosmetics":     {},
            "equipped_tool": None,
            "cooldowns":     {},
            "active_effects":{},
            "stats": {
                "total_gathers": 0,
                "total_loots":   0,
                "gold_earned":   0.0,
            }
        }
    p = data["players"][uid]
    p.setdefault("gold", 0.0)
    p.setdefault("equipped_tool", None)
    p.setdefault("active_effects", {})
    p.setdefault("stats", {}).setdefault("gold_earned", 0.0)
    p["name"] = user.display_name
    return p

def fmt_gold(amount: float) -> str:
    """Format gold for display — always 1 decimal place."""
    return f"{round(amount, 1):.1f}"

def add_item(player: dict, item_id: str, qty: int = 1):
    inv = player["inventory"]
    inv[item_id] = inv.get(item_id, 0) + qty

def remove_item(player: dict, item_id: str, qty: int = 1) -> bool:
    inv = player["inventory"]
    if inv.get(item_id, 0) < qty:
        return False
    inv[item_id] -= qty
    if inv[item_id] == 0:
        del inv[item_id]
    return True

def add_gold(player: dict, amount: float):
    if amount <= 0:
        return
    player["gold"] = round(player.get("gold", 0.0) + amount, 1)
    player.setdefault("stats", {})
    player["stats"]["gold_earned"] = round(
        player["stats"].get("gold_earned", 0.0) + amount, 1
    )

def spend_gold(player: dict, amount: float) -> bool:
    """Deduct gold. Returns False if insufficient funds."""
    if amount <= 0 or round(player.get("gold", 0.0), 1) < round(amount, 1):
        return False
    player["gold"] = round(player["gold"] - amount, 1)
    return True

def cooldown_remaining(player: dict, action: str, seconds: int) -> int:
    last = player["cooldowns"].get(action, 0)
    remaining = seconds - (time.time() - last)
    return max(0, int(remaining))

def set_cooldown(player: dict, action: str):
    player["cooldowns"][action] = time.time()

def add_xp(player: dict, amount: int, xp_per_level: int) -> bool:
    """Add XP, level up if threshold reached. Returns True if levelled up."""
    player["xp"] += amount
    if player["xp"] >= player["level"] * xp_per_level:
        player["xp"] -= player["level"] * xp_per_level
        player["level"] += 1
        return True
    return False

def fmt_time(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    return f"{seconds // 60}m {seconds % 60}s"

def sanitize_qty(qty, max_qty: int) -> int | None:
    """Validate and clamp a quantity input. Returns None if invalid."""
    try:
        qty = int(qty)
    except (TypeError, ValueError):
        return None
    if qty <= 0:
        return None
    return min(qty, max_qty)

def is_super(ctx) -> bool:
    """Returns True if the user has a SUPER_ROLES role (bypasses cooldowns)."""
    from config import SUPER_ROLES
    # In a server — check roles
    if isinstance(ctx.author, discord.Member):
        return any(r.name in SUPER_ROLES for r in ctx.author.roles)
    # In a DM — check if the bot can find the member in any mutual guild
    for guild in ctx.bot.guilds:
        member = guild.get_member(ctx.author.id)
        if member and any(r.name in SUPER_ROLES for r in member.roles):
            return True
    return False

def is_mod(ctx) -> bool:
    """Returns True if the user has a MOD_ROLE_NAMES role."""
    from config import MOD_ROLE_NAMES
    if isinstance(ctx.author, discord.Member):
        return any(r.name in MOD_ROLE_NAMES for r in ctx.author.roles)
    for guild in ctx.bot.guilds:
        member = guild.get_member(ctx.author.id)
        if member and any(r.name in MOD_ROLE_NAMES for r in member.roles):
            return True
    return False

# ── Cog ───────────────────────────────────────────────────────────────────────

class DataCog(commands.Cog):
    pass

async def setup(bot):
    await bot.add_cog(DataCog(bot))
