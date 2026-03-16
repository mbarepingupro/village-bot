# 🏡 Village Bot — Setup & Extension Guide

## File structure
```
village_bot/
├── bot.py            ← entry point, don't touch
├── config.py         ← ALL your customization lives here
├── requirements.txt
├── Procfile          ← for Railway deployment
└── cogs/
    ├── data.py       ← save/load layer, don't touch
    ├── character.py  ← !join, !character, !inventory
    ├── gather.py     ← !gather, !craft
    ├── economy.py    ← !gold, !sell, !shop, !buy, !equip
    ├── guild.py      ← !guilds, !guildstatus, !contribute
    ├── items.py      ← !use (consumables)
    ├── loot.py       ← !startloot, !loot
    └── help.py       ← !help
```

---

## Deploy on Railway (free)

1. Go to https://railway.app → New Project → Deploy from GitHub
2. Upload the whole `village_bot/` folder
3. Add environment variable: `BOT_TOKEN` = your token from Discord Developer Portal
4. Go to **Volumes** tab → Add Volume → mount path `/app/data`
5. Railway auto-detects the Procfile and runs `python bot.py`

---

## Commands reference

### Character
| Command | What it does |
|---------|-------------|
| `!join` | See all guilds |
| `!join <guild>` | Join a guild (resets daily at 00:00 Berlin time) |
| `!character` | Your character sheet |
| `!character @user` | View someone else's sheet |
| `!inventory` | Your item bag |

### Gathering & Crafting
| Command | What it does |
|---------|-------------|
| `!gather` | Collect your guild's 2 resources (1hr cooldown) |
| `!craft` | See all craft recipes |
| `!craft <item>` | Craft an item |

### Items
| Command | What it does |
|---------|-------------|
| `!use` | See your usable items |
| `!use <item>` | Use a consumable |

### Guilds & Upgrades
| Command | What it does |
|---------|-------------|
| `!guilds` | See all guilds and their upgrade tiers |
| `!guildstatus` | Your guild's upgrade pool progress |
| `!contribute <resource> <qty>` | Donate resources toward your guild's next upgrade |

### Economy
| Command | What it does |
|---------|-------------|
| `!gold` | Check your gold balance |
| `!sell` | See resource sell prices |
| `!sell <item> <qty>` | Sell resources for gold |
| `!sell <item> all` | Sell your entire stack |
| `!shop` | Browse the shop |
| `!buy <item>` | Buy something |
| `!equip <item>` | Equip a tool or cosmetic |

### Stream Loot
| Command | What it does |
|---------|-------------|
| `!loot` | Claim loot during a live drop |

### Mod Only
| Command | What it does |
|---------|-------------|
| `!startloot` | Open the loot window when going live |
| `!endloot` | Force-close the loot window |
| `!addgold [amount]` | Add gold to yourself for testing (streamer role only) |

---

## The 7 Guilds

| Building | Class | Resources | Gimmick |
|---|---|---|---|
| 🔒 Horny Jail | Inmate | 🥚 Eggs + 🪵 Wood | Chaos Roll: 20% chance to double everything |
| 🦭 Sea Lion Pit | Sea Lion | 🐟 Fish + 🦴 Bones | Splash: nearby players get bonus fish |
| 🥤 Club Soda | Mixologist | 🌿 Herbs + 🍺 Alcohol | Brew: only class that can craft potions |
| 🎪 The Circus | Performer | 🍬 Candies + 🎊 Confetti | Wild Roll: 0x to 3x multiplier at random |
| ⚔️ The Barracks | Soldier | 🥩 Meat + 🪶 Fur | Ration: shorter gather cooldown (45min) |
| 🏚️ Cursed Temple | Cultist | 🕯️ Candles + 🔮 Soul Shards | Ritual: 15% chance to find rare items |
| 🪓 The Guillotine | Executioner | ⚙️ Metal + 🫘 Blood Beans | Precision: always max roll on one resource |

---

## Adding a new guild

Open `config.py` and copy this block into the `GUILDS` dict:

```python
"my_building": {
    "emoji":        "🏠",
    "display_name": "My Building",
    "class_name":   "ClassName",
    "description":  "What this guild does.",
    "resources":    ["item_id_1", "item_id_2"],  # exactly 2 resources
    "gather_bonus": {"item_id_1": 1.5},
    "special":      "Describe the unique mechanic",
    "loot_item":    "item_id_here",
},
```

Then add upgrade tiers for it in `GUILD_UPGRADES`:

```python
"my_building": [
    {
        "name":        "Upgrade Name",
        "description": "What it does.",
        "cost":        {"fish": 20, "bone": 10},  # use OTHER guilds' resources
        "effect":      "effect_tag",
    },
],
```

---

## Adding a new item

In `config.py`, add to the `ITEMS` dict:

```python
"my_item": {
    "name": "My Item", "emoji": "✨",
    "type": "resource",   # resource | cosmetic | consumable | tool | special | stream_unlock
    "description": "What it does.", "tradeable": True,
},
```

For consumables, add `"effect": "my_effect"` and register the effect function in `cogs/items.py`.

For tools, add `"slot": "tool"` and `"bonus": {"resource_id": 0.5}`.

For cosmetics, add `"slot": "hat"` or `"slot": "outfit"` or `"slot": "accessory"` — used later for avatar system.

---

## Adding a new craft recipe

In `config.py`, add to the `RECIPES` dict:

```python
"result_item_id": {
    "needs":      {"wood": 5, "bone": 3},
    "class_only": None,   # or "Mixologist" to restrict
    "description": "5 wood + 3 bone → Result Item",
},
```

---

## Adding a new consumable effect

1. Add the item to `config.py` `ITEMS` with `"type": "consumable"` and `"effect": "your_tag"`
2. Write a function in `cogs/items.py`:
```python
def apply_your_tag(player: dict, data: dict) -> str:
    # modify player dict here
    return "Message shown to user"
```
3. Register it in the `EFFECTS` dict in `cogs/items.py`:
```python
EFFECTS = {
    ...
    "your_tag": apply_your_tag,
}
```
4. Register item → effect mapping in `ITEM_EFFECTS`:
```python
ITEM_EFFECTS = {
    ...
    "your_item_id": "your_tag",
}
```

---

## Adding a new feature module

1. Create `cogs/myfeature.py`
2. Add `"cogs.myfeature"` to the `COGS` list in `bot.py`
3. Template:

```python
from discord.ext import commands
from cogs.data import load_data, save_data, get_player, data_lock, user_lock

class MyFeatureCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="mycommand")
    async def my_command(self, ctx):
        try:
            async with user_lock(ctx.author.id, "mycommand"):
                async with data_lock:
                    data   = load_data()
                    player = get_player(data, ctx.author)
                    # ... your logic ...
                    save_data(data)
            await ctx.send("Done!")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

async def setup(bot):
    await bot.add_cog(MyFeatureCog(bot))
```

---

## Security protections in place

- **Per-user lock** — same user can't run the same command twice simultaneously
- **Global file lock** — concurrent writes from different users queue up safely
- **Atomic saves** — data written to temp file first, then renamed (no corrupt saves)
- **Input sanitization** — negative/zero quantities rejected before touching economy
- **Double-checked funds** — gold verified inside the lock before any purchase
- **remove_item helper** — always checks inventory before deducting, never goes negative

---

## Avatar system (future)

Every player's cosmetics are stored as `slot → item_id`. When you build the VTube Studio integration, read `player["cosmetics"]` and map slots to your avatar layers — the data structure is already ready.

---

## Versioning

Use GitHub Releases to snapshot stable versions before making big changes:
- Go to your repo → **Releases** → **Create a new release**
- Tag it (e.g. `v1.0`, `v2.0`) with a short description
- Railway always deploys from your latest `main` branch
