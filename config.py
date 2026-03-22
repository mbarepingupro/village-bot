"""
config.py — All customizable settings live here.
=================================================
Village Bot v2 — Cosmetic-focused redesign.

The game loop: join guild → gather resources → earn loot tokens on stream → craft cosmetics.

To add a new guild:      add an entry to GUILDS dict below.
To add a new item:       add an entry to ITEMS dict below.
To add a new cosmetic:   add to ITEMS + add a recipe to RECIPES.
To change cooldowns:     edit the COOLDOWNS section.
"""

import os

# ── Bot settings ──────────────────────────────────────────────────────────────
BOT_TOKEN        = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
COMMAND_PREFIX   = "!"
DATA_FILE        = "/app/data/village_data.json"
BOT_CHANNEL_NAME = ""   # set to your channel name to restrict commands

# Auto-loot trigger — Streamcord go-live channel
GO_LIVE_CHANNEL  = "🔴-live-now"
GO_LIVE_TRIGGER  = "twitch.tv/mbarepingu"
VILLAGE_CHANNEL  = "🛖🧊-penguin-village"

# Roles
MOD_ROLE_NAMES = ["Moderator", "Mod", "streamer"]
SUPER_ROLES    = ["streamer"]

# ── Timezone for daily reset ──────────────────────────────────────────────────
DAILY_RESET_TZ = "Europe/Berlin"

# ── Cooldowns (in seconds) ────────────────────────────────────────────────────
COOLDOWNS = {
    "gather": 3600,   # 1 hour
}

# ── Loot drops ────────────────────────────────────────────────────────────────
LOOT_WINDOW_SECONDS = 1800          # 30 minutes
LOOT_TOKEN_RANGE    = (1, 5)        # random tokens per claim
LOOT_RESOURCE_BONUS = (2, 5)        # bonus guild resources per claim

# ── XP & Levels ───────────────────────────────────────────────────────────────
XP_PER_GATHER      = 10
XP_PER_LOOT        = 25
XP_PER_LEVEL       = 100
LEVEL_GATHER_BONUS = 0.02   # +2% per level to all guild resources

# ── Guilds ────────────────────────────────────────────────────────────────────
# Each guild has 2 resources and a unique gathering gimmick.
# No upgrade system — class gimmicks are always active.

GUILDS = {
    "horny_jail": {
        "emoji":        "🔒",
        "display_name": "Horny Jail",
        "class_name":   "Inmate",
        "description":  "Chaos reigns. Eggs and wood from mayhem.",
        "resources":    ["egg", "wood"],
        "gather_bonus": {"egg": 1.8, "wood": 1.5},
        "special":      "Chaos Roll: 20% chance to double all resources on gather",
    },
    "sea_lion_pit": {
        "emoji":        "🦭",
        "display_name": "Sea Lion Pit",
        "class_name":   "Sea Lion",
        "description":  "Masters of water. Fish and bones from the deep.",
        "resources":    ["fish", "bone"],
        "gather_bonus": {"fish": 2.0, "bone": 1.8},
        "special":      "Splash: nearby players get +2 fish when you gather",
    },
    "club_soda": {
        "emoji":        "🥤",
        "display_name": "Club Soda",
        "class_name":   "Mixologist",
        "description":  "Brew masters. Herbs and alcohol.",
        "resources":    ["herb", "alcohol"],
        "gather_bonus": {"herb": 1.8, "alcohol": 1.6},
        "special":      "Brew Bonus: +30% to herb and alcohol yields",
    },
    "the_circus": {
        "emoji":        "🎪",
        "display_name": "The Circus",
        "class_name":   "Performer",
        "description":  "Wild card. Candies and confetti everywhere.",
        "resources":    ["candy", "confetti"],
        "gather_bonus": {},
        "special":      "Wild Roll: gather result is 0x to 3x at random",
    },
    "the_barracks": {
        "emoji":        "⚔️",
        "display_name": "The Barracks",
        "class_name":   "Soldier",
        "description":  "Disciplined warriors. Meat and fur.",
        "resources":    ["meat", "fur"],
        "gather_bonus": {"meat": 1.8, "fur": 1.6},
        "special":      "Ration: gather cooldown reduced to 45 min instead of 1 hour",
    },
    "cursed_temple": {
        "emoji":        "🏚️",
        "display_name": "Cursed Temple",
        "class_name":   "Cultist",
        "description":  "Dark rituals. Candles and soul shards.",
        "resources":    ["candle", "soul_shard"],
        "gather_bonus": {"candle": 1.8, "soul_shard": 1.5},
        "special":      "Ritual: 15% chance to find a random resource from any guild",
    },
    "the_guillotine": {
        "emoji":        "🪓",
        "display_name": "The Guillotine",
        "class_name":   "Executioner",
        "description":  "Cold and precise. Metal and blood beans.",
        "resources":    ["metal", "blood_bean"],
        "gather_bonus": {"metal": 1.8, "blood_bean": 1.6},
        "special":      "Precision: always get max roll on one resource per gather",
    },
}

# ── Items ─────────────────────────────────────────────────────────────────────

ITEMS = {
    # ── Resources ──────────────────────────────────────────────────────────────
    "egg":        {"name": "Egg",        "emoji": "🥚", "type": "resource", "description": "Fragile but valuable."},
    "wood":       {"name": "Wood",       "emoji": "🪵", "type": "resource", "description": "Basic building material."},
    "fish":       {"name": "Fish",       "emoji": "🐟", "type": "resource", "description": "Slippery. Good for trades."},
    "bone":       {"name": "Bone",       "emoji": "🦴", "type": "resource", "description": "From the deep."},
    "herb":       {"name": "Herb",       "emoji": "🌿", "type": "resource", "description": "Used in potions and brews."},
    "alcohol":    {"name": "Alcohol",    "emoji": "🍺", "type": "resource", "description": "Distilled in Club Soda."},
    "candy":      {"name": "Candy",      "emoji": "🍬", "type": "resource", "description": "Sticky and sweet."},
    "confetti":   {"name": "Confetti",   "emoji": "🎊", "type": "resource", "description": "It gets everywhere."},
    "meat":       {"name": "Meat",       "emoji": "🥩", "type": "resource", "description": "Tough but nutritious."},
    "fur":        {"name": "Fur",        "emoji": "🪶", "type": "resource", "description": "Warm and useful."},
    "candle":     {"name": "Candle",     "emoji": "🕯️", "type": "resource", "description": "Burns with an eerie light."},
    "soul_shard": {"name": "Soul Shard", "emoji": "🔮", "type": "resource", "description": "A fragment of something dark."},
    "metal":      {"name": "Metal",      "emoji": "⚙️", "type": "resource", "description": "Cold and sharp."},
    "blood_bean": {"name": "Blood Bean", "emoji": "🫘", "type": "resource", "description": "Don't ask what it's made of."},

    # ── Loot Token ─────────────────────────────────────────────────────────────
    "loot_token": {"name": "Loot Token", "emoji": "🎟️", "type": "resource", "description": "Earned by watching the stream. Required for crafting."},

    # ══════════════════════════════════════════════════════════════════════════
    # COSMETICS — COMMON TIER (1 loot token + single-guild resources)
    # ══════════════════════════════════════════════════════════════════════════

    # Guild scarves (outfit slot) — one per guild
    "jail_scarf":        {"name": "Jail Scarf",        "emoji": "🧣", "type": "cosmetic", "slot": "outfit", "description": "Red & white stripes. Crime pays."},
    "sea_lion_scarf":    {"name": "Sea Lion Scarf",    "emoji": "🧣", "type": "cosmetic", "slot": "outfit", "description": "Blue wave pattern. Smells like fish."},
    "soda_scarf":        {"name": "Soda Scarf",        "emoji": "🧣", "type": "cosmetic", "slot": "outfit", "description": "Green and bubbly. Fizzy."},
    "circus_scarf":      {"name": "Circus Scarf",      "emoji": "🧣", "type": "cosmetic", "slot": "outfit", "description": "Rainbow party scarf. Spectacular."},
    "soldier_scarf":     {"name": "Soldier Scarf",     "emoji": "🧣", "type": "cosmetic", "slot": "outfit", "description": "Camo pattern. Disciplined."},
    "cultist_scarf":     {"name": "Cultist Scarf",     "emoji": "🧣", "type": "cosmetic", "slot": "outfit", "description": "Dark purple. Whispers at night."},
    "executioner_scarf": {"name": "Executioner Scarf", "emoji": "🧣", "type": "cosmetic", "slot": "outfit", "description": "Iron grey. Final fashion."},

    # Guild accessories/hats — one per guild
    "egg_crown":     {"name": "Egg Crown",     "emoji": "🥚", "type": "cosmetic", "slot": "hat",       "description": "A cracked egg on your head. Bold."},
    "fish_necklace": {"name": "Fish Necklace", "emoji": "🐟", "type": "cosmetic", "slot": "accessory", "description": "Fish bones strung together. Elegant."},
    "herb_wreath":   {"name": "Herb Wreath",   "emoji": "🌿", "type": "cosmetic", "slot": "hat",       "description": "Leafy flower crown. Fragrant."},
    "candy_cane":    {"name": "Candy Cane",     "emoji": "🍭", "type": "cosmetic", "slot": "accessory", "description": "A held candy cane. Festive."},
    "dog_tag":       {"name": "Dog Tag",        "emoji": "🪪", "type": "cosmetic", "slot": "accessory", "description": "Military dog tag. Earned."},
    "candle_hat":    {"name": "Candle Hat",     "emoji": "🕯️", "type": "cosmetic", "slot": "hat",       "description": "Melting candle on your head. Lit."},
    "gear_monocle":  {"name": "Gear Monocle",   "emoji": "🔍", "type": "cosmetic", "slot": "accessory", "description": "Steampunk monocle. Distinguished."},

    # ══════════════════════════════════════════════════════════════════════════
    # COSMETICS — RARE TIER (3 loot tokens + cross-guild resources)
    # ══════════════════════════════════════════════════════════════════════════

    # Horny Jail rare set
    "inmate_cap":      {"name": "Inmate Cap",      "emoji": "🧢", "type": "cosmetic", "slot": "hat",    "description": "Black & white prisoner cap. Iconic."},
    "jail_jumpsuit":   {"name": "Jail Jumpsuit",   "emoji": "👔", "type": "cosmetic", "slot": "outfit", "description": "Orange jumpsuit. Classic."},

    # Sea Lion Pit rare set
    "sea_lion_crown":  {"name": "Sea Lion Crown",  "emoji": "👑", "type": "cosmetic", "slot": "hat",    "description": "Shell & coral crown. Majestic."},
    "sailor_coat":     {"name": "Sailor Coat",     "emoji": "🧥", "type": "cosmetic", "slot": "outfit", "description": "Navy blue coat. Seaworthy."},

    # Club Soda rare set
    "bartender_hat":   {"name": "Bartender Hat",   "emoji": "🎩", "type": "cosmetic", "slot": "hat",    "description": "Top hat with a lime. Classy."},
    "mixologist_apron":{"name": "Mixologist Apron", "emoji": "👨‍🍳", "type": "cosmetic", "slot": "outfit", "description": "Stained bar apron. Professional."},

    # Circus rare set
    "jester_hat":      {"name": "Jester Hat",      "emoji": "🎭", "type": "cosmetic", "slot": "hat",    "description": "Bells and all. Foolish."},
    "clown_suit":      {"name": "Clown Suit",      "emoji": "🤡", "type": "cosmetic", "slot": "outfit", "description": "Polka dots. Honk honk."},

    # Barracks rare set
    "soldier_helmet":  {"name": "Soldier Helmet",  "emoji": "⛑️", "type": "cosmetic", "slot": "hat",    "description": "Military helmet. Battle-tested."},
    "battle_armor":    {"name": "Battle Armor",    "emoji": "🛡️", "type": "cosmetic", "slot": "outfit", "description": "Fur-trimmed armor. Imposing."},

    # Cursed Temple rare set
    "cultist_hood":    {"name": "Cultist Hood",    "emoji": "🌑", "type": "cosmetic", "slot": "hat",    "description": "Dark hooded cowl. Mysterious."},
    "dark_robe":       {"name": "Dark Robe",       "emoji": "🖤", "type": "cosmetic", "slot": "outfit", "description": "Full cultist robe. Devoted."},

    # Guillotine rare set
    "executioner_mask":{"name": "Executioner Mask", "emoji": "🎭", "type": "cosmetic", "slot": "hat",    "description": "Black leather mask. Final."},
    "iron_suit":       {"name": "Iron Suit",        "emoji": "⚔️", "type": "cosmetic", "slot": "outfit", "description": "Heavy iron plate. Unstoppable."},

    # ══════════════════════════════════════════════════════════════════════════
    # COSMETICS — LEGENDARY TIER (20 loot tokens + multi-guild resources)
    # ══════════════════════════════════════════════════════════════════════════

    "golden_crown":      {"name": "Golden Crown",      "emoji": "👑", "type": "cosmetic", "slot": "hat",       "description": "The ultimate flex. Blinding."},
    "chaos_cloak":       {"name": "Chaos Cloak",        "emoji": "🌈", "type": "cosmetic", "slot": "outfit",    "description": "Shimmering multicolor. You've done it all."},
    "soul_flame_aura":   {"name": "Soul Flame Aura",    "emoji": "🔥", "type": "cosmetic", "slot": "accessory", "description": "Purple fire surrounds you. Feared."},
    "rainbow_scarf":     {"name": "Rainbow Scarf",      "emoji": "🏳️‍🌈", "type": "cosmetic", "slot": "outfit",    "description": "Flowing rainbow. Radiant."},
    "village_elder_staff":{"name": "Village Elder Staff","emoji": "🪄", "type": "cosmetic", "slot": "accessory", "description": "Glowing elder's staff. Respected."},
}

# ── Gather table ──────────────────────────────────────────────────────────────
# Base amounts per guild resource before class bonuses.
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

# ── Craft recipes ─────────────────────────────────────────────────────────────
# Every recipe requires loot tokens (earned on stream) + resources.
#
# Tiers:
#   Common    — 1 token  + single-guild resources
#   Rare      — 3 tokens + cross-guild resources
#   Legendary — 20 tokens + multi-guild resources
#
# Format:
#   result_item_id -> {
#       "needs":  {resource: qty, ...},
#       "tokens": int,           # loot tokens required
#       "tier":   "common" | "rare" | "legendary",
#   }

RECIPES = {
    # ── COMMON — Guild Scarves (outfit) ───────────────────────────────────────
    "jail_scarf":        {"needs": {"egg": 10, "wood": 8},         "tokens": 1, "tier": "common"},
    "sea_lion_scarf":    {"needs": {"fish": 10, "bone": 8},        "tokens": 1, "tier": "common"},
    "soda_scarf":        {"needs": {"herb": 10, "alcohol": 8},     "tokens": 1, "tier": "common"},
    "circus_scarf":      {"needs": {"candy": 10, "confetti": 8},   "tokens": 1, "tier": "common"},
    "soldier_scarf":     {"needs": {"meat": 10, "fur": 8},         "tokens": 1, "tier": "common"},
    "cultist_scarf":     {"needs": {"candle": 10, "soul_shard": 8},"tokens": 1, "tier": "common"},
    "executioner_scarf": {"needs": {"metal": 10, "blood_bean": 8}, "tokens": 1, "tier": "common"},

    # ── COMMON — Guild Accessories/Hats ───────────────────────────────────────
    "egg_crown":     {"needs": {"egg": 15},    "tokens": 1, "tier": "common"},
    "fish_necklace": {"needs": {"fish": 15},   "tokens": 1, "tier": "common"},
    "herb_wreath":   {"needs": {"herb": 15},   "tokens": 1, "tier": "common"},
    "candy_cane":    {"needs": {"candy": 15},  "tokens": 1, "tier": "common"},
    "dog_tag":       {"needs": {"meat": 15},   "tokens": 1, "tier": "common"},
    "candle_hat":    {"needs": {"candle": 15}, "tokens": 1, "tier": "common"},
    "gear_monocle":  {"needs": {"metal": 15},  "tokens": 1, "tier": "common"},

    # ── RARE — Horny Jail ─────────────────────────────────────────────────────
    "inmate_cap":    {"needs": {"egg": 20, "wood": 15, "bone": 12},    "tokens": 3, "tier": "rare"},
    "jail_jumpsuit": {"needs": {"wood": 20, "egg": 15, "fur": 12},     "tokens": 3, "tier": "rare"},

    # ── RARE — Sea Lion Pit ───────────────────────────────────────────────────
    "sea_lion_crown": {"needs": {"fish": 20, "bone": 15, "metal": 12},  "tokens": 3, "tier": "rare"},
    "sailor_coat":    {"needs": {"bone": 20, "fish": 15, "herb": 12},   "tokens": 3, "tier": "rare"},

    # ── RARE — Club Soda ──────────────────────────────────────────────────────
    "bartender_hat":    {"needs": {"herb": 20, "alcohol": 15, "candy": 12},   "tokens": 3, "tier": "rare"},
    "mixologist_apron": {"needs": {"alcohol": 20, "herb": 15, "egg": 12},     "tokens": 3, "tier": "rare"},

    # ── RARE — The Circus ─────────────────────────────────────────────────────
    "jester_hat": {"needs": {"candy": 20, "confetti": 15, "candle": 12},   "tokens": 3, "tier": "rare"},
    "clown_suit": {"needs": {"confetti": 20, "candy": 15, "alcohol": 12}, "tokens": 3, "tier": "rare"},

    # ── RARE — The Barracks ───────────────────────────────────────────────────
    "soldier_helmet": {"needs": {"meat": 20, "fur": 15, "metal": 12},  "tokens": 3, "tier": "rare"},
    "battle_armor":   {"needs": {"fur": 20, "meat": 15, "bone": 12},   "tokens": 3, "tier": "rare"},

    # ── RARE — Cursed Temple ──────────────────────────────────────────────────
    "cultist_hood": {"needs": {"candle": 20, "soul_shard": 15, "confetti": 12}, "tokens": 3, "tier": "rare"},
    "dark_robe":    {"needs": {"soul_shard": 20, "candle": 15, "herb": 12},     "tokens": 3, "tier": "rare"},

    # ── RARE — The Guillotine ─────────────────────────────────────────────────
    "executioner_mask": {"needs": {"metal": 20, "blood_bean": 15, "fur": 12},        "tokens": 3, "tier": "rare"},
    "iron_suit":        {"needs": {"blood_bean": 20, "metal": 15, "soul_shard": 12}, "tokens": 3, "tier": "rare"},

    # ── LEGENDARY ─────────────────────────────────────────────────────────────
    "golden_crown": {
        "needs":  {"metal": 30, "fish": 20, "egg": 15},
        "tokens": 20, "tier": "legendary",
    },
    "chaos_cloak": {
        "needs":  {"egg": 15, "wood": 15, "fish": 15, "bone": 15, "herb": 15,
                   "alcohol": 15, "candy": 15, "confetti": 15, "meat": 15,
                   "fur": 15, "candle": 15, "soul_shard": 15, "metal": 15,
                   "blood_bean": 15},
        "tokens": 20, "tier": "legendary",
    },
    "soul_flame_aura": {
        "needs":  {"soul_shard": 30, "candle": 25, "blood_bean": 20},
        "tokens": 20, "tier": "legendary",
    },
    "rainbow_scarf": {
        "needs":  {"candy": 20, "confetti": 20, "herb": 20, "egg": 20},
        "tokens": 20, "tier": "legendary",
    },
    "village_elder_staff": {
        "needs":  {"wood": 25, "bone": 25, "metal": 25, "soul_shard": 20},
        "tokens": 20, "tier": "legendary",
    },
}
