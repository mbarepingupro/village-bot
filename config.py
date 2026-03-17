"""
config.py — All customizable settings live here.
=================================================
To add a new guild:        add an entry to GUILDS dict below.
To add a new item:         add an entry to ITEMS dict below.
To add a new upgrade:      add an entry to GUILD_UPGRADES dict below.
To change cooldowns:       edit the COOLDOWNS section.
To change sell prices:     edit SELL_PRICES.
To change shop listings:   edit SHOP.
"""

import os

# ── Bot settings ──────────────────────────────────────────────────────────────
BOT_TOKEN        = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
COMMAND_PREFIX   = "!"
DATA_FILE        = "/app/data/village_data.json"
BOT_CHANNEL_NAME = ""   # set to your channel name to restrict commands

# Auto-loot trigger — Streamcord go-live channel
GO_LIVE_CHANNEL  = "🔴-live-now"           # Streamcord go-live channel
GO_LIVE_TRIGGER  = "twitch.tv/mbarepingu"   # string to match in the message
VILLAGE_CHANNEL  = "🛖🧊-penguin-village"    # village bot channel
TRADE_CHANNEL    = "🤝-village-trade"          # dedicated trade channel

# Roles allowed to run mod commands (!startloot, !addgold, etc.)
MOD_ROLE_NAMES = ["Moderator", "Mod", "streamer"]

# Roles that bypass all cooldowns and restrictions (for testing)
SUPER_ROLES = ["streamer"]

# ── Timezone for daily reset ──────────────────────────────────────────────────
# Guild switch resets daily at 00:00 in this timezone
DAILY_RESET_TZ = "Europe/Berlin"

# ── Cooldowns (in seconds) ────────────────────────────────────────────────────
COOLDOWNS = {
    "gather": 3600,   # 1 hour
    "craft":  300,    # 5 minutes
    "loot":   3600,   # once per loot session
}

LOOT_WINDOW_SECONDS = 600   # loot window open for 10 min

# ── Guilds ────────────────────────────────────────────────────────────────────
# Fields:
#   emoji         : displayed everywhere
#   display_name  : full name shown to users
#   class_name    : job title members get
#   description   : shown in !join list
#   resources     : list of item_ids this guild gathers (exactly 2)
#   gather_bonus  : item_id -> multiplier applied on top of base gather
#   special       : unique mechanic description
#   loot_item     : exclusive item from loot drops
#
# ➕ To add a new guild: copy a block, fill in the fields, done.

GUILDS = {
    "horny_jail": {
        "emoji":        "🔒",
        "display_name": "Horny Jail",
        "class_name":   "Inmate",
        "description":  "Chaos reigns. Eggs and wood from mayhem.",
        "resources":    ["egg", "wood"],
        "gather_bonus": {"egg": 1.8, "wood": 1.5},
        "special":      "working HARD: 20% chance to double all resources on gather",
        "loot_item":    "get_out_of_jail_card",
    },
    "sea_lion_pit": {
        "emoji":        "🦭",
        "display_name": "Sea Lion Pit",
        "class_name":   "Sea Lion",
        "description":  "Masters of water. Fish and bones from the deep.",
        "resources":    ["fish", "bone"],
        "gather_bonus": {"fish": 2.0, "bone": 1.8},
        "special":      "Splash: nearby players get +2 fish when you gather",
        "loot_item":    "golden_herring",
    },
    "club_soda": {
        "emoji":        "🥤",
        "display_name": "Club Soda",
        "class_name":   "Mixologist",
        "description":  "Brew consumable buffs. Herbs and alcohol.",
        "resources":    ["herb", "alcohol"],
        "gather_bonus": {"herb": 1.8, "alcohol": 1.6},
        "special":      "Brew: only class that can craft potions and buffs",
        "loot_item":    "mystery_potion",
    },
    "the_circus": {
        "emoji":        "🎪",
        "display_name": "The Circus",
        "class_name":   "Performer",
        "description":  "Wild card. Candies and confetti everywhere.",
        "resources":    ["candy", "confetti"],
        "gather_bonus": {},   # wild roll — bonuses are random
        "special":      "Wild Roll: gather result is 0x to 3x at random",
        "loot_item":    "trick_coin",
    },
    "the_barracks": {
        "emoji":        "⚔️",
        "display_name": "The Barracks",
        "class_name":   "Soldier",
        "description":  "Disciplined warriors. Polar bear meat and fur.",
        "resources":    ["meat", "fur"],
        "gather_bonus": {"meat": 1.8, "fur": 1.6},
        "special":      "Ration: gather cooldown reduced to 45 min instead of 1 hour",
        "loot_item":    "ration_pack",
    },
    "cursed_temple": {
        "emoji":        "🏚️",
        "display_name": "Cursed Temple",
        "class_name":   "Cultist",
        "description":  "Dark rituals. Candles and soul shards.",
        "resources":    ["candle", "soul_shard"],
        "gather_bonus": {"candle": 1.8, "soul_shard": 1.5},
        "special":      "Ritual: 15% chance to find a random resource from any guild on gather",
        "loot_item":    "cursed_relic",
    },
    "the_guillotine": {
        "emoji":        "🪓",
        "display_name": "The Guillotine",
        "class_name":   "Executioner",
        "description":  "Cold and precise. Metal and blood beans.",
        "resources":    ["metal", "blood_bean"],
        "gather_bonus": {"metal": 1.8, "blood_bean": 1.6},
        "special":      "Precision: always get max roll on one resource per gather",
        "loot_item":    "executioner_hood",
    },

    # ── ADD NEW GUILDS BELOW THIS LINE ────────────────────────────────────────
    # "my_building": {
    #     "emoji":        "🏠",
    #     "display_name": "My Building",
    #     "class_name":   "ClassName",
    #     "description":  "What this guild does.",
    #     "resources":    ["item_id_1", "item_id_2"],
    #     "gather_bonus": {"item_id_1": 1.5},
    #     "special":      "Describe the unique mechanic",
    #     "loot_item":    "item_id_here",
    # },
}

# ── Guild upgrades ────────────────────────────────────────────────────────────
# Shared upgrades — the whole guild contributes resources to unlock.
# Costs use resources from OTHER guilds to encourage switching.
#
# Fields per upgrade:
#   name        : display name
#   description : what the upgrade does (flavor + mechanic tag)
#   cost        : dict of item_id -> qty needed in the pool
#   effect      : string tag used in gather.py to apply the bonus
#
# ➕ To add a new upgrade tier: add another entry to the list.

GUILD_UPGRADES = {
    "horny_jail": [
        {
            "name":        "Reinforced Bars",
            "description": "Chaos Roll chance increases to 30%.",
            "cost":        {"fish": 20, "bone": 10},
            "effect":      "chaos_boost",
        },
        {
            "name":        "Morning Wood",
            "description": "Chaos Roll now gives 3x instead of 2x.",
            "cost":        {"soul_shard": 15, "candle": 20},
            "effect":      "chaos_triple",
        },
    ],
    "sea_lion_pit": [
        {
            "name":        "Fish Ladder",
            "description": "Splash now hits 2 players instead of 1.",
            "cost":        {"egg": 20, "wood": 15},
            "effect":      "splash_double",
        },
        {
            "name":        "Coral Throne",
            "description": "Splash gives +3 fish instead of +2.",
            "cost":        {"herb": 20, "alcohol": 10},
            "effect":      "splash_triple",
        },
    ],
    "club_soda": [
        {
            "name":        "Herb Garden",
            "description": "Craft cooldown reduced to 3 minutes.",
            "cost":        {"candy": 20, "confetti": 15},
            "effect":      "craft_speed",
        },
        {
            "name":        "Secret Menu",
            "description": "Mixologists can craft Bone Brew and Scrambled Armor.",
            "cost":        {"metal": 15, "blood_bean": 10},
            "effect":      "secret_recipes",
        },
    ],
    "the_circus": [
        {
            "name":        "Big Top",
            "description": "Wild Roll minimum is now 0.5x instead of 0x.",
            "cost":        {"fish": 20, "bone": 15},
            "effect":      "wild_floor",
        },
        {
            "name":        "Sequin Vault",
            "description": "3x outcome is twice as likely.",
            "cost":        {"meat": 15, "fur": 20},
            "effect":      "wild_ceiling",
        },
    ],
    "the_barracks": [
        {
            "name":        "Drill Grounds",
            "description": "Gather cooldown drops to 30 minutes.",
            "cost":        {"soul_shard": 15, "candle": 20},
            "effect":      "barracks_speed",
        },
        {
            "name":        "Armory",
            "description": "+20% to all resources gathered.",
            "cost":        {"egg": 20, "wood": 25},
            "effect":      "armory_bonus",
        },
    ],
    "cursed_temple": [
        {
            "name":        "Bone Altar",
            "description": "Ritual chance increases to 25%.",
            "cost":        {"meat": 20, "fur": 15},
            "effect":      "ritual_boost",
        },
        {
            "name":        "Candle Array",
            "description": "Ritual can now find cursed exclusive items.",
            "cost":        {"metal": 15, "blood_bean": 20},
            "effect":      "ritual_cursed",
        },
    ],
    "the_guillotine": [
        {
            "name":        "Sharpening Stone",
            "description": "Precision now applies to both resources.",
            "cost":        {"candle": 20, "soul_shard": 15},
            "effect":      "precision_double",
        },
        {
            "name":        "Execution Chamber",
            "description": "+25% to metal and blood bean yields.",
            "cost":        {"fish": 20, "herb": 20},
            "effect":      "execution_bonus",
        },
    ],
}

# ── Items ─────────────────────────────────────────────────────────────────────
# ➕ To add a new item: copy a block and fill it in.

ITEMS = {
    # ── Guild resources ────────────────────────────────────────────────────────
    "egg": {
        "name": "Egg", "emoji": "🥚",
        "type": "resource", "description": "Fragile but valuable.", "tradeable": True,
    },
    "wood": {
        "name": "Wood", "emoji": "🪵",
        "type": "resource", "description": "Basic building material.", "tradeable": True,
    },
    "fish": {
        "name": "Fish", "emoji": "🐟",
        "type": "resource", "description": "Slippery. Good for trades.", "tradeable": True,
    },
    "bone": {
        "name": "Bone", "emoji": "🦴",
        "type": "resource", "description": "From the deep. Useful for dark crafts.", "tradeable": True,
    },
    "herb": {
        "name": "Herb", "emoji": "🌿",
        "type": "resource", "description": "Used in potions and brews.", "tradeable": True,
    },
    "alcohol": {
        "name": "Alcohol", "emoji": "🍺",
        "type": "resource", "description": "Distilled in Club Soda's back room.", "tradeable": True,
    },
    "candy": {
        "name": "Candy", "emoji": "🍬",
        "type": "resource", "description": "Sticky and sweet. The Circus runs on these.", "tradeable": True,
    },
    "confetti": {
        "name": "Confetti", "emoji": "🎊",
        "type": "resource", "description": "It gets everywhere.", "tradeable": True,
    },
    "meat": {
        "name": "Polar Bear Meat", "emoji": "🥩",
        "type": "resource", "description": "Tough but nutritious.", "tradeable": True,
    },
    "fur": {
        "name": "Fur", "emoji": "🪶",
        "type": "resource", "description": "Warm and tradeable.", "tradeable": True,
    },
    "candle": {
        "name": "Candle", "emoji": "🕯️",
        "type": "resource", "description": "Burns with an eerie light.", "tradeable": True,
    },
    "soul_shard": {
        "name": "Soul Shard", "emoji": "🔮",
        "type": "resource", "description": "A fragment of something that shouldn't exist.", "tradeable": False,
    },
    "metal": {
        "name": "Metal", "emoji": "⚙️",
        "type": "resource", "description": "Cold and sharp.", "tradeable": True,
    },
    "blood_bean": {
        "name": "Blood Bean", "emoji": "🫘",
        "type": "resource", "description": "Don't ask what it's made of.", "tradeable": False,
    },

    # ── Consumables ────────────────────────────────────────────────────────────
    "mystery_potion": {
        "name": "Mystery Potion", "emoji": "🧪",
        "type": "consumable", "effect": "mystery",
        "description": "Unknown effect. Use at your own risk.", "tradeable": True,
    },
    "bone_brew": {
        "name": "Bone Brew", "emoji": "🍵",
        "type": "consumable", "effect": "cooldown_reset",
        "description": "Resets your gather cooldown immediately.", "tradeable": True,
    },
    "protein_shake": {
        "name": "Protein Shake", "emoji": "🥤",
        "type": "consumable", "effect": "gather_boost",
        "description": "+50% resources on your next gather.", "tradeable": True,
    },
    "crystal_potion": {
        "name": "Crystal Potion", "emoji": "💎",
        "type": "consumable", "effect": "triple_gather",
        "description": "2x gather for your next 3 gathers. Mixologist only.", "tradeable": True,
    },
    "meat_stew": {
        "name": "Meat Stew", "emoji": "🍲",
        "type": "consumable", "effect": "craft_reset",
        "description": "Resets your craft cooldown immediately.", "tradeable": True,
    },

    # ── Special / loot exclusives ──────────────────────────────────────────────
    "get_out_of_jail_card": {
        "name": "Get Out of Jail Card", "emoji": "🃏",
        "type": "consumable", "effect": "cooldown_reset",
        "description": "Resets your gather cooldown once.", "tradeable": False,
    },
    "golden_herring": {
        "name": "Golden Herring", "emoji": "🥇",
        "type": "consumable", "effect": "golden_herring",
        "description": "Worth 10 fish. Very shiny.", "tradeable": True,
    },
    "trick_coin": {
        "name": "Trick Coin", "emoji": "🪙",
        "type": "consumable", "effect": "trick_coin",
        "description": "Heads = double next gather. Tails = nothing.", "tradeable": False,
    },
    "ration_pack": {
        "name": "Ration Pack", "emoji": "🎒",
        "type": "consumable", "effect": "cooldown_reset",
        "description": "Emergency supplies. Resets gather cooldown.", "tradeable": False,
    },
    "cursed_relic": {
        "name": "Cursed Relic", "emoji": "☠️",
        "type": "consumable", "effect": "mystery",
        "description": "A relic from the temple. Its power is unknown.", "tradeable": False,
    },
    "executioner_hood": {
        "name": "Executioner's Hood", "emoji": "🪖",
        "type": "cosmetic", "slot": "hat",
        "description": "Worn by those who carry out the sentence.", "tradeable": False,
    },

    # ── Crafted consumables ────────────────────────────────────────────────────
    "sequin_charm": {
        "name": "Sequin Charm", "emoji": "✨",
        "type": "consumable", "effect": "wild_floor_once",
        "description": "Wild Roll minimum is 1x for one gather.", "tradeable": False,
    },

    # ── Tools ──────────────────────────────────────────────────────────────────
    "iron_axe": {
        "name": "Iron Axe", "emoji": "🪓",
        "type": "tool", "slot": "tool",
        "description": "+50% wood on every gather while equipped.",
        "tradeable": False, "bonus": {"wood": 0.5},
    },
    "fishing_rod": {
        "name": "Fishing Rod", "emoji": "🎣",
        "type": "tool", "slot": "tool",
        "description": "+50% fish on every gather while equipped.",
        "tradeable": False, "bonus": {"fish": 0.5},
    },
    "pickaxe": {
        "name": "Pickaxe", "emoji": "⛏️",
        "type": "tool", "slot": "tool",
        "description": "+50% metal on every gather while equipped.",
        "tradeable": False, "bonus": {"metal": 0.5},
    },

    # ── Cosmetics ──────────────────────────────────────────────────────────────
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
    "soldier_helmet": {
        "name": "Soldier Helmet", "emoji": "⛑️",
        "type": "cosmetic", "slot": "hat",
        "description": "Worn by the disciplined.", "tradeable": False,
    },
    "cultist_robe": {
        "name": "Cultist Robe", "emoji": "🌑",
        "type": "cosmetic", "slot": "outfit",
        "description": "For the devoted.", "tradeable": False,
    },

    # ── Stream unlocks ─────────────────────────────────────────────────────────
    "stream_command_slot": {
        "name": "Stream Command Slot", "emoji": "📺",
        "type": "stream_unlock",
        "description": "Unlocks a custom stream command. Activate with the streamer.",
        "tradeable": False,
    },

    # ── Limited edition cosmetics ──────────────────────────────────────────────
    "penguin_helmet": {
        "name": "Penguin Helmet", "emoji": "🐧",
        "type": "cosmetic", "slot": "hat",
        "description": "Awarded to the first penguins of the village. Rare.",
        "tradeable": False,
    },

    # ── ADD NEW ITEMS BELOW THIS LINE ──────────────────────────────────────────
    # "my_item": {
    #     "name": "My Item", "emoji": "✨",
    #     "type": "resource",
    #     "description": "What it does.", "tradeable": True,
    # },
}

# ── Gather table ──────────────────────────────────────────────────────────────
# Base amounts per guild resource before class bonuses.
# Each guild only rolls its own 2 resources.
# Format: item_id -> (min, max)

BASE_GATHER = {
    "egg":        (2, 6),
    "wood":       (2, 6),
    "fish":       (2, 6),
    "bone":       (1, 4),
    "herb":       (2, 5),
    "alcohol":    (1, 4),
    "candy":      (2, 6),
    "confetti":   (2, 8),
    "meat":       (1, 4),
    "fur":        (1, 4),
    "candle":     (1, 4),
    "soul_shard": (1, 3),
    "metal":      (1, 4),
    "blood_bean": (1, 3),
}

# ── Craft recipes ──────────────────────────────────────────────────────────────
# Format: result_item_id -> {"needs": {item_id: qty}, "class_only": None | "ClassName"}
# ➕ Add new recipes here.

RECIPES = {
    "mystery_potion": {
        "needs":      {"herb": 3, "alcohol": 1},
        "class_only": "Mixologist",
        "description": "3 herbs + 1 alcohol → Mystery Potion (Mixologist only)",
    },
    "bone_brew": {
        "needs":      {"bone": 2, "herb": 2},
        "class_only": None,
        "description": "2 bones + 2 herbs → Bone Brew (resets gather cooldown)",
    },
    "protein_shake": {
        "needs":      {"egg": 5, "fur": 3},
        "class_only": None,
        "description": "5 eggs + 3 fur → Scrambled Armor (+50% next gather)",
    },
    "crystal_potion": {
        "needs":      {"soul_shard": 3, "alcohol": 2},
        "class_only": "Mixologist",
        "description": "3 soul shards + 2 alcohol → Crystal Potion (2x for 3 gathers, Mixologist only)",
    },
    "sequin_charm": {
        "needs":      {"confetti": 4, "candle": 2},
        "class_only": None,
        "description": "4 confetti + 2 candles → Sequin Charm (Wild Roll min 1x once)",
    },
    "meat_stew": {
        "needs":      {"meat": 4, "fish": 2},
        "class_only": None,
        "description": "4 polar bear meat + 2 fish → Meat Stew (resets craft cooldown)",
    },
}

# ── Gold ───────────────────────────────────────────────────────────────────────
GOLD_LOOT_REWARD = (2.0, 8.0)

SELL_PRICES = {
    "egg":        0.1,
    "wood":       0.1,
    "candy":      0.1,
    "confetti":   0.1,
    "fish":       0.2,
    "bone":       0.3,
    "herb":       0.3,
    "meat":       0.4,
    "fur":        0.4,
    "alcohol":    0.5,
    "candle":     0.5,
    "metal":      0.8,
    "blood_bean": 1.0,
    "soul_shard": 1.5,
}

# ── Shop ───────────────────────────────────────────────────────────────────────
SHOP = {
    "iron_axe":         {"price": 30,  "guild_only": None},
    "fishing_rod":      {"price": 30,  "guild_only": None},
    "pickaxe":          {"price": 30,  "guild_only": None},
    "jester_hat":       {"price": 50,  "guild_only": "the_circus"},
    "inmate_outfit":    {"price": 50,  "guild_only": "horny_jail"},
    "sea_lion_hood":    {"price": 50,  "guild_only": "sea_lion_pit"},
    "soldier_helmet":   {"price": 50,  "guild_only": "the_barracks"},
    "cultist_robe":     {"price": 50,  "guild_only": "cursed_temple"},
    "executioner_hood": {"price": 50,  "guild_only": "the_guillotine"},
    # ── Tools (all resources) ─────────────────────────────────────────────────
    "egg_basket":       {"price": 30, "guild_only": None},
    "bone_saw":         {"price": 30, "guild_only": None},
    "herb_pouch":       {"price": 30, "guild_only": None},
    "flask":            {"price": 30, "guild_only": None},
    "candy_bag":        {"price": 30, "guild_only": None},
    "confetti_cannon":  {"price": 30, "guild_only": None},
    "hunting_knife":    {"price": 30, "guild_only": None},
    "fur_trap":         {"price": 30, "guild_only": None},
    "candle_mold":      {"price": 30, "guild_only": None},
    "soul_jar":         {"price": 30, "guild_only": None},
    "blood_vial":       {"price": 30, "guild_only": None},
    # ── ADD NEW SHOP ITEMS BELOW ──────────────────────────────────────────────
}

# ── XP & Levels ───────────────────────────────────────────────────────────────
XP_PER_GATHER  = 10
XP_PER_LOOT    = 25
XP_PER_LEVEL   = 100
