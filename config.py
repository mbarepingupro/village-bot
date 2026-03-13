"""
config.py — All customizable settings live here.
=================================================
To add a new guild:   add an entry to GUILDS dict below.
To add a new item:    add an entry to ITEMS dict below.
To change cooldowns:  edit the COOLDOWNS section.
"""

import os

# ── Bot settings ─────────────────────────────────────────────────────────────
BOT_TOKEN      = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
COMMAND_PREFIX = "!"
DATA_FILE      = "/app/data/village_data.json"

# IDs of Discord roles/users allowed to run mod commands (!startloot etc.)
MOD_ROLE_NAMES = ["Moderator", "Mod", "streamer"]   # add your mod role names here

#Channel name where the bot works exclusiveky
BOT_CHANNEL_NAME = "🛖🧊-penguin-village"    # exact name of your Discord channel

# ── Cooldowns (in seconds) ────────────────────────────────────────────────────
COOLDOWNS = {
    "gather": 120,    # 2 minutes
    "craft":  300,    # 5 minutes
    "loot":   3600,   # can only claim loot once per session
}

LOOT_WINDOW_SECONDS = 300   # how long the loot window stays open (5 min)

# ── Guilds ────────────────────────────────────────────────────────────────────
# Each guild assigns a class to members who join it.
#
# Fields:
#   emoji        : displayed everywhere
#   class_name   : the job title members get
#   description  : shown in !help and !join
#   gather_bonus : dict of item_id -> multiplier (e.g. 1.5 = 50% more of that item)
#   special      : short string describing the unique mechanic (flavor text for now,
#                  hook it up in cogs/gather.py when you want real logic)
#   loot_item    : item_id of the exclusive loot drop for this guild
#
# ➕ To add a new guild, copy one block and fill in the fields.

GUILDS = {
    "horny_jail": {
        "emoji":        "🔒",
        "display_name": "Horny Jail",
        "class_name":   "Inmate",
        "description":  "Chaos reigns. Bonus contraband, XP from mayhem.",
        "gather_bonus": {"contraband": 2.0, "wood": 0.8},
        "special":      "Chaos Roll: 20% chance to double all resources on gather",
        "loot_item":    "get_out_of_jail_card",
    },
    "sea_lion_pit": {
        "emoji":        "🦭",
        "display_name": "Sea Lion Pit",
        "class_name":   "Sea Lion",
        "description":  "Masters of water. Best fish yields, splash bonuses.",
        "gather_bonus": {"fish": 2.0, "stone": 0.9},
        "special":      "Splash: nearby players get +1 fish when you gather",
        "loot_item":    "golden_herring",
    },
    "club_soda": {
        "emoji":        "🥤",
        "display_name": "Club Soda",
        "class_name":   "Mixologist",
        "description":  "Brew consumable buffs no other class can make.",
        "gather_bonus": {"herbs": 1.8, "fish": 1.2},
        "special":      "Craft: can combine resources into buff potions",
        "loot_item":    "mystery_potion",
    },
    "the_circus": {
        "emoji":        "🎪",
        "display_name": "The Circus",
        "class_name":   "Performer",
        "description":  "Wild card. High risk, high reward on every gather.",
        "gather_bonus": {},   # bonuses are random — see special
        "special":      "Wild Roll: gather result is 0x to 3x at random",
        "loot_item":    "trick_coin",
    },
    "wayward_hall": {
        "emoji":        "🌀",
        "display_name": "The Wayward Hall",
        "class_name":   "Wanderer",
        "description":  "Jack of all trades. Gathers every resource type equally.",
        "gather_bonus": {"wood": 1.2, "stone": 1.2, "fish": 1.2, "herbs": 1.2},
        "special":      "Roam: can gather from any biome without penalty",
        "loot_item":    "wanderer_map",
    },

    # ── ADD NEW GUILDS BELOW THIS LINE ─────────────────────────────────────
    # "my_new_building": {
    #     "emoji":        "🏚️",
    #     "display_name": "My New Building",
    #     "class_name":   "ClassName",
    #     "description":  "What this guild does.",
    #     "gather_bonus": {"wood": 1.5},
    #     "special":      "Describe the unique mechanic here",
    #     "loot_item":    "item_id_here",
    # },
}

# ── Items ─────────────────────────────────────────────────────────────────────
# Every item that can exist in the game is defined here.
#
# Fields:
#   name        : display name
#   emoji       : displayed in inventory
#   type        : "resource" | "cosmetic" | "consumable" | "stream_unlock" | "special"
#   slot        : (cosmetics only) "hat" | "outfit" | "accessory" — for avatar system
#   description : shown in !inventory
#   tradeable   : whether players can give it to others (future feature)
#
# ➕ To add a new item, copy a block and fill it in.

ITEMS = {
    # ── Resources ──────────────────────────────────────────────────────────
    "wood": {
        "name": "Wood", "emoji": "🪵",
        "type": "resource", "description": "Basic building material.", "tradeable": True,
    },
    "stone": {
        "name": "Stone", "emoji": "🪨",
        "type": "resource", "description": "Solid and reliable.", "tradeable": True,
    },
    "fish": {
        "name": "Fish", "emoji": "🐟",
        "type": "resource", "description": "Slippery. Good for trades.", "tradeable": True,
    },
    "herbs": {
        "name": "Herbs", "emoji": "🌿",
        "type": "resource", "description": "Used in crafting potions.", "tradeable": True,
    },
    "contraband": {
        "name": "Contraband", "emoji": "📦",
        "type": "resource", "description": "Don't ask where this came from.", "tradeable": False,
    },

    # ── Guild exclusive loot drops ──────────────────────────────────────────
    "get_out_of_jail_card": {
        "name": "Get Out of Jail Card", "emoji": "🃏",
        "type": "special", "description": "Removes your gather cooldown once.", "tradeable": False,
    },
    "golden_herring": {
        "name": "Golden Herring", "emoji": "🥇",
        "type": "special", "description": "Worth 10 fish. Very shiny.", "tradeable": True,
    },
    "mystery_potion": {
        "name": "Mystery Potion", "emoji": "🧪",
        "type": "consumable", "description": "A brew of unknown effect. Use at your own risk.", "tradeable": True,
    },
    "trick_coin": {
        "name": "Trick Coin", "emoji": "🪙",
        "type": "special", "description": "Flip it: heads = double next gather, tails = nothing.", "tradeable": False,
    },
    "wanderer_map": {
        "name": "Wanderer's Map", "emoji": "🗺️",
        "type": "special", "description": "Shows a hidden gather location. Bonus resources once.", "tradeable": False,
    },

    # ── Cosmetics (avatar-ready) ────────────────────────────────────────────
    "jester_hat": {
        "name": "Jester Hat", "emoji": "🎭",
        "type": "cosmetic", "slot": "hat",
        "description": "For the true performer.", "tradeable": False,
    },
    "inmate_outfit": {
        "name": "Inmate Outfit", "emoji": "👔",
        "type": "cosmetic", "slot": "outfit",
        "description": "Stripes. Classic.", "tradeable": False,
    },

    # ── Stream unlocks ──────────────────────────────────────────────────────
    "stream_command_slot": {
        "name": "Stream Command Slot", "emoji": "📺",
        "type": "stream_unlock",
        "description": "Unlocks a custom command usable on stream. Activate with the streamer.", "tradeable": False,
    },

    # ── Gather tools (buyable in shop, boost yield) ────────────────────────────
    "iron_axe": {
        "name": "Iron Axe", "emoji": "🪓",
        "type": "tool", "slot": "tool",
        "description": "+50% wood on every gather while equipped.",
        "tradeable": False,
        "bonus": {"wood": 0.5},   # added on top of base, stacks with class bonus
    },
    "fishing_rod": {
        "name": "Fishing Rod", "emoji": "🎣",
        "type": "tool", "slot": "tool",
        "description": "+50% fish on every gather while equipped.",
        "tradeable": False,
        "bonus": {"fish": 0.5},
    },
    "pickaxe": {
        "name": "Pickaxe", "emoji": "⛏️",
        "type": "tool", "slot": "tool",
        "description": "+50% stone on every gather while equipped.",
        "tradeable": False,
        "bonus": {"stone": 0.5},
    },

    # ── Cosmetics (avatar-ready) ────────────────────────────────────────────
    "jester_hat": {
        "name": "Jester Hat", "emoji": "🎭",
        "type": "cosmetic", "slot": "hat",
        "description": "For the true performer.", "tradeable": False,
    },
    "inmate_outfit": {
        "name": "Inmate Outfit", "emoji": "👔",
        "type": "cosmetic", "slot": "outfit",
        "description": "Stripes. Classic.", "tradeable": False,
    },
    "sea_lion_hood": {
        "name": "Sea Lion Hood", "emoji": "🦭",
        "type": "cosmetic", "slot": "hat",
        "description": "Honk.", "tradeable": False,
    },
    "wanderer_cloak": {
        "name": "Wanderer's Cloak", "emoji": "🧥",
        "type": "cosmetic", "slot": "outfit",
        "description": "Worn by those who belong everywhere and nowhere.",
        "tradeable": False,
    },

    # ── Stream unlocks ──────────────────────────────────────────────────────
    "stream_command_slot": {
        "name": "Stream Command Slot", "emoji": "📺",
        "type": "stream_unlock",
        "description": "Unlocks a custom command usable on stream. Activate with the streamer.",
        "tradeable": False,
    },

    # ── ADD NEW ITEMS BELOW THIS LINE ───────────────────────────────────────
    # "my_item": {
    #     "name": "My Item", "emoji": "✨",
    #     "type": "resource",
    #     "description": "What it does.", "tradeable": True,
    # },
}

# ── Gather table ──────────────────────────────────────────────────────────────
# Base resource amounts before class bonuses are applied.
# Format: item_id -> (min, max)

BASE_GATHER = {
    "wood":  (2, 6),
    "stone": (1, 4),
    "fish":  (0, 3),
    "herbs": (0, 2),
}

# ── Gold ──────────────────────────────────────────────────────────────────────
# Gold is a currency, not a gathered resource.
# Earned by: selling resources, loot drops, future combat rewards.

GOLD_LOOT_REWARD = (5, 20)    # (min, max) gold from a loot drop

# Sell prices: how much gold 1 unit of each resource is worth.
# ➕ Add any resource here to make it sellable.
SELL_PRICES = {
    "wood":       1,
    "stone":      1,
    "fish":       2,
    "herbs":      3,
    "contraband": 5,
}

# ── Shop ──────────────────────────────────────────────────────────────────────
# Items available in !shop.
# Format: item_id -> {"price": gold_cost, "guild_only": None | "guild_key"}
# guild_only restricts purchase to members of that guild.
# ➕ Add new shop listings here — item must also exist in ITEMS.

SHOP = {
    # Tools
    "iron_axe":    {"price": 30,  "guild_only": None},
    "fishing_rod": {"price": 30,  "guild_only": None},
    "pickaxe":     {"price": 30,  "guild_only": None},

    # Cosmetics
    "jester_hat":      {"price": 50,  "guild_only": "the_circus"},
    "inmate_outfit":   {"price": 50,  "guild_only": "horny_jail"},
    "sea_lion_hood":   {"price": 50,  "guild_only": "sea_lion_pit"},
    "wanderer_cloak":  {"price": 50,  "guild_only": "wayward_hall"},

    # ── ADD NEW SHOP ITEMS BELOW THIS LINE ────────────────────────────────
    # "my_item": {"price": 100, "guild_only": None},
}

# ── XP & Levels ───────────────────────────────────────────────────────────────
XP_PER_GATHER  = 10
XP_PER_LOOT    = 25
XP_PER_LEVEL   = 100   # XP needed to level up (flat for now, easy to make a curve)
