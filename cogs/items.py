"""
cogs/items.py — Consumable item effects
=========================================
Command: !use <item>

Adding a new consumable:
  1. Add the item to config.py ITEMS with "type": "consumable" and "effect": "your_tag"
  2. Write a function apply_your_tag(player, data) -> str below
  3. Register it in the EFFECTS dict at the bottom
  That's it. No other file needs to change.
"""

import random
import time
import discord
from discord.ext import commands
from config import ITEMS, COOLDOWNS
from cogs.data import (
    load_data, save_data, get_player,
    add_item, remove_item, data_lock, user_lock, is_super
)

# ── Effect functions ──────────────────────────────────────────────────────────
# Each function receives (player, data) and returns a result string shown to user.
# Modify player dict directly — save_data is called after.

def apply_mystery(player: dict, data: dict) -> str:
    """Random effect — could be great, could be nothing."""
    roll = random.random()

    if roll < 0.05:
        # 5% — jackpot, 50 gold
        player["gold"] = player.get("gold", 0) + 50
        player.setdefault("stats", {})
        player["stats"]["gold_earned"] = player["stats"].get("gold_earned", 0) + 50
        return "✨ **JACKPOT!** You found 50💰 gold at the bottom of the bottle!"

    elif roll < 0.25:
        # 20% — double next gather (set a flag)
        player["active_effects"] = player.get("active_effects", {})
        player["active_effects"]["gather_multiplier"] = 2.0
        return "💪 **Power surge!** Your next `!gather` gives double resources!"

    elif roll < 0.50:
        # 25% — reset gather cooldown
        player["cooldowns"]["gather"] = 0
        return "⚡ **Cooldown cleared!** You can `!gather` again immediately!"

    elif roll < 0.70:
        # 20% — bonus resources dumped directly
        wood = random.randint(3, 8)
        fish = random.randint(1, 4)
        add_item(player, "wood", wood)
        add_item(player, "fish", fish)
        return f"🌿 **Strange surge!** You feel energized and find 🪵{wood} wood and 🐟{fish} fish!"

    elif roll < 0.85:
        # 15% — small gold
        gold = random.randint(5, 15)
        player["gold"] = player.get("gold", 0) + gold
        player.setdefault("stats", {})
        player["stats"]["gold_earned"] = player["stats"].get("gold_earned", 0) + gold
        return f"💛 **Tastes like gold.** You gain {gold}💰."

    else:
        # 15% — nothing
        return "🤢 *It tasted awful and did absolutely nothing.*"


def apply_bone_brew(player: dict, data: dict) -> str:
    """Reset gather cooldown and give a small bone bonus."""
    player["cooldowns"]["gather"] = 0
    add_item(player, "bone", random.randint(3, 6))
    bones = player["inventory"].get("bone", 0)
    return f"🍺 **Bone Brew consumed!** Gather cooldown reset + bonus bones added. You now have {bones} bones."


def apply_crystal_potion(player: dict, data: dict) -> str:
    """2x gather multiplier for next 3 gathers."""
    player.setdefault("active_effects", {})
    player["active_effects"]["crystal_boost_remaining"] = 3
    return "💎 **Crystal Potion!** Your next **3 gathers** yield 2x resources!"


def apply_protein_shake(player: dict, data: dict) -> str:
    """50% gather bonus on next gather."""
    player.setdefault("active_effects", {})
    player["active_effects"]["gather_multiplier"] = 1.5
    return "🥤 **Protein Shake!** Your next `!gather` gives +50% resources!"


def apply_cooldown_reset(player: dict, data: dict) -> str:
    """Reset gather cooldown immediately."""
    player["cooldowns"]["gather"] = 0
    return "🔓 **Cooldown reset!** You can `!gather` again right now."


def apply_trick_coin(player: dict, data: dict) -> str:
    """50/50 — double next gather or nothing."""
    if random.random() < 0.5:
        player["active_effects"] = player.get("active_effects", {})
        player["active_effects"]["gather_multiplier"] = 2.0
        return "🪙 **Heads!** Your next `!gather` gives double resources!"
    else:
        return "🪙 **Tails.** Nothing happens. The coin lands in the dirt."


def apply_wanderer_map(player: dict, data: dict) -> str:
    """Bonus gather of all resource types."""
    loot = {
        "wood": random.randint(4, 10),
        "fish": random.randint(2, 6),
        "herb": random.randint(1, 4),
        "egg":  random.randint(2, 5),
    }
    for item_id, qty in loot.items():
        add_item(player, item_id, qty)
    lines = "  ".join(f"{ITEMS[k]['emoji']} {v}" for k, v in loot.items())
    return f"🗺️ **The map leads somewhere good!** You find: {lines}"


def apply_golden_herring(player: dict, data: dict) -> str:
    """Convert to 10 fish."""
    add_item(player, "fish", 10)
    return "🥇 **You trade the Golden Herring for 10🐟 fish!**"


def apply_gather_boost(player: dict, data: dict) -> str:
    """50% gather bonus on next gather — effect tag stored on protein_shake item."""
    player.setdefault("active_effects", {})
    player["active_effects"]["gather_multiplier"] = 1.5
    return "🥤 **Protein Shake!** Your next `!gather` gives +50% resources!"


def apply_triple_gather(player: dict, data: dict) -> str:
    """2x gather for next 3 gathers — effect tag stored on crystal_potion item."""
    player.setdefault("active_effects", {})
    player["active_effects"]["crystal_boost_remaining"] = 3
    return "💎 **Crystal Potion!** Your next **3 gathers** yield 2x resources!"


def apply_wild_floor_once(player: dict, data: dict) -> str:
    """Sequin charm — Wild Roll minimum is 1x for one gather."""
    player.setdefault("active_effects", {})
    player["active_effects"]["wild_floor_once"] = True
    return "✨ **Sequin Charm!** Your next Wild Roll will be at least 1x!"


def apply_craft_reset(player: dict, data: dict) -> str:
    """Meat stew — reset craft cooldown immediately."""
    player["cooldowns"]["craft"] = 0
    return "🍲 **Meat Stew consumed!** Your craft cooldown has been reset!"


# ── Effect registry ───────────────────────────────────────────────────────────
# Maps effect tag (string) → function
# ➕ Register new effects here

EFFECTS = {
    "mystery":          apply_mystery,
    "cooldown_reset":   apply_cooldown_reset,
    "trick_coin":       apply_trick_coin,
    "wanderer_map":     apply_wanderer_map,
    "golden_herring":   apply_golden_herring,
    "bone_brew":        apply_bone_brew,
    "crystal_potion":   apply_crystal_potion,
    "triple_gather":    apply_triple_gather,
    "protein_shake":    apply_protein_shake,
    "gather_boost":     apply_gather_boost,
    "wild_floor_once":  apply_wild_floor_once,
    "craft_reset":      apply_craft_reset,
}

ITEM_EFFECTS = {
    "mystery_potion":       "mystery",
    "get_out_of_jail_card": "cooldown_reset",
    "ration_pack":          "cooldown_reset",
    "cursed_relic":         "mystery",
    "trick_coin":           "trick_coin",
    "wanderer_map":         "wanderer_map",
    "golden_herring":       "golden_herring",
    "bone_brew":            "bone_brew",
    "crystal_potion":       "triple_gather",
    "protein_shake":        "gather_boost",
    "sequin_charm":         "wild_floor_once",
    "meat_stew":            "craft_reset",
}


class ItemsCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="use")
    async def use(self, ctx, *, item_name: str = None):
        """Use a consumable item from your inventory. Usage: !use mystery potion"""

        if item_name is None:
            # Show usable items in inventory
            try:
                data   = load_data()
                player = get_player(data, ctx.author)
                save_data(data)

                usable = [
                    item_id for item_id in player["inventory"]
                    if item_id in ITEM_EFFECTS
                ]
                if not usable:
                    await ctx.send(
                        "🎒 You don't have any usable items. "
                        "Craft or find some first!"
                    )
                    return

                lines = ["**🎒 Usable items in your bag:**\n"]
                for item_id in usable:
                    item = ITEMS.get(item_id, {"name": item_id, "emoji": "❓", "description": ""})
                    qty  = player["inventory"][item_id]
                    lines.append(
                        f"{item['emoji']} **{item['name']}** x{qty} — *{item['description']}*"
                    )
                lines.append("\nUsage: `!use <item name>`")
                await ctx.send("\n".join(lines))
            except Exception as e:
                await ctx.send(f"❌ Error: {e}")
            return

        try:
            async with user_lock(ctx.author.id, "use"):
                async with data_lock:
                    data   = load_data()
                    player = get_player(data, ctx.author)

                    # Match item by name or id
                    matched_id = None
                    for item_id in ITEM_EFFECTS:
                        item = ITEMS.get(item_id, {"name": item_id})
                        if item_name.lower() in [item_id.lower(), item["name"].lower()]:
                            matched_id = item_id
                            break

                    if matched_id is None:
                        await ctx.send(
                            f"❌ `{item_name}` is not a usable item. "
                            f"Type `!use` to see what you can use."
                        )
                        return

                    # Check inventory
                    if player["inventory"].get(matched_id, 0) < 1:
                        item = ITEMS.get(matched_id, {"name": matched_id, "emoji": "❓"})
                        await ctx.send(
                            f"❌ You don't have **{item['emoji']} {item['name']}** in your bag."
                        )
                        return

                    # Consume the item
                    remove_item(player, matched_id, 1)

                    # Apply effect
                    effect_tag = ITEM_EFFECTS[matched_id]
                    effect_fn  = EFFECTS.get(effect_tag)
                    if effect_fn:
                        result_msg = effect_fn(player, data)
                    else:
                        result_msg = "✨ You used the item but nothing happened."

                    save_data(data)

                item_def = ITEMS.get(matched_id, {"name": matched_id, "emoji": "❓"})
                await ctx.send(
                    f"{item_def['emoji']} **{ctx.author.display_name}** used "
                    f"**{item_def['name']}**!\n{result_msg}"
                )

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")


async def setup(bot):
    await bot.add_cog(ItemsCog(bot))
