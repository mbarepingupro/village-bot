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
    ├── loot.py       ← !startloot, !loot
    └── help.py       ← !help
```

---

## Deploy on Railway (free)

1. Go to https://railway.app → New Project → Deploy from GitHub
2. Upload the whole `village_bot/` folder
3. Add environment variable: `BOT_TOKEN` = your token from Discord Developer Portal
4. Railway auto-detects the Procfile and runs `python bot.py`

---

## Adding a new guild

Open `config.py` and copy this block into the `GUILDS` dict:

```python
"my_building": {
    "emoji":        "🏚️",
    "display_name": "My Building",
    "class_name":   "ClassName",
    "description":  "What this guild does.",
    "gather_bonus": {"wood": 1.5},   # 50% more wood
    "special":      "Describe the unique mechanic",
    "loot_item":    "some_item_id",  # must exist in ITEMS
},
```

That's it. The bot picks it up automatically on restart.

---

## Adding a new item

In `config.py`, add to the `ITEMS` dict:

```python
"my_item": {
    "name": "My Item", "emoji": "✨",
    "type": "resource",   # resource | cosmetic | consumable | special | stream_unlock
    "description": "What it does.",
    "tradeable": True,
},
```

For cosmetics, add a `"slot"` field (`"hat"`, `"outfit"`, `"accessory"`) — this is used later when you build the avatar system.

---

## Adding a new craft recipe

In `cogs/gather.py`, add to the `RECIPES` dict:

```python
"result_item_id": {
    "needs":      {"wood": 5, "stone": 3},
    "class_only": None,   # or "Mixologist" to restrict
    "description": "5 wood + 3 stone → Result Item",
},
```

---

## Adding a new feature module

1. Create `cogs/myfeature.py`
2. Add `"cogs.myfeature"` to the `COGS` list in `bot.py`
3. The template for a cog:

```python
from discord.ext import commands
from cogs.data import load_data, save_data, get_player

class MyFeatureCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="mycommand")
    async def my_command(self, ctx):
        data   = load_data()
        player = get_player(data, ctx.author)
        # ... your logic ...
        save_data(data)
        await ctx.send("Done!")

async def setup(bot):
    await bot.add_cog(MyFeatureCog(bot))
```

---

## Avatar system (future)

Every player record in `village_data.json` already has a `cosmetics` dict with slot→item_id mappings. When you're ready to build the avatar layer, the data is already structured for it — just read `player["cosmetics"]` and map slots to your VTube Studio layers.
```
