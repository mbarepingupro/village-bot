"""
cogs/gather.py — Gathering and crafting
=========================================
Commands: !gather, !craft

Each guild only gathers its own 2 resources.
Class gimmicks are applied here.
Guild upgrade effects are checked from shared guild state.
"""

import random
import discord
from discord.ext import commands
from config import GUILDS, ITEMS, BASE_GATHER, COOLDOWNS, RECIPES, XP_PER_GATHER, XP_PER_LEVEL
from cogs.data import (
    load_data, save_data, get_player,
    add_item, remove_item, cooldown_remaining, set_cooldown,
    add_xp, fmt_time, data_lock, user_lock, is_super
)
from cogs.guild import get_guild_data


def get_guild_effects(data: dict, guild_key: str) -> list:
    """Return list of active effect tags for a guild."""
    return get_guild_data(data, guild_key).get("effects", [])


class GatherCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="gather")
    async def gather(self, ctx):
        """Gather your guild's resources."""
        try:
            if user_lock(ctx.author.id, "gather").locked():
                return

            async with user_lock(ctx.author.id, "gather"):
                async with data_lock:
                    data   = load_data()
                    player = get_player(data, ctx.author)

                    if player["guild"] is None:
                        await ctx.send(f"⚠️ {ctx.author.mention} Join a guild first with `!join`.")
                        return

                    guild_key = player["guild"]
                    guild_cfg = GUILDS[guild_key]
                    effects   = get_guild_effects(data, guild_key)

                    # ── Cooldown check ────────────────────────────────────────
                    cooldown = COOLDOWNS["gather"]
                    # Barracks upgrade: faster cooldown
                    if "barracks_speed" in effects and guild_key == "the_barracks":
                        cooldown = 1800   # 30 min
                    elif guild_key == "the_barracks":
                        cooldown = 2700   # 45 min base for Soldiers

                    remaining = cooldown_remaining(player, "gather", cooldown)
                    if remaining > 0 and not is_super(ctx):
                        await ctx.send(
                            f"⏳ {ctx.author.mention} Rest for **{fmt_time(remaining)}** before gathering again."
                        )
                        return

                    # ── Build bonuses from class + equipped tool ──────────────
                    bonuses = dict(guild_cfg.get("gather_bonus", {}))
                    tool_id = player.get("equipped_tool")
                    if tool_id:
                        tool_def = ITEMS.get(tool_id, {})
                        for res, bonus in tool_def.get("bonus", {}).items():
                            bonuses[res] = bonuses.get(res, 1.0) + bonus

                    # Armory upgrade bonus
                    if "armory_bonus" in effects and guild_key == "the_barracks":
                        for res in bonuses:
                            bonuses[res] = bonuses.get(res, 1.0) * 1.2

                    # ── Active effects from consumables ───────────────────────
                    multiplier     = 1.0
                    active_effects = player.get("active_effects", {})

                    if "gather_multiplier" in active_effects:
                        multiplier = active_effects.pop("gather_multiplier")

                    elif "crystal_charges" in active_effects:
                        charges = active_effects["crystal_charges"]
                        if charges > 0:
                            multiplier = 2.0
                            active_effects["crystal_charges"] -= 1
                            if active_effects["crystal_charges"] <= 0:
                                del active_effects["crystal_charges"]

                    elif "gather_boost" in active_effects:
                        multiplier = 1.5
                        del active_effects["gather_boost"]

                    # ── Class-specific mechanics ──────────────────────────────
                    chaos_chance  = 0.3 if "chaos_boost" in effects else 0.2
                    chaos_mult    = 3.0 if "chaos_triple" in effects else 2.0

                    special_msg = ""

                    if player["class"] == "Performer":
                        # Wild Roll
                        wild_floor   = 0.5 if "wild_floor" in effects else 0
                        wild_options = [wild_floor, 0.5, 1, 1, 1.5, 2]
                        if "wild_ceiling" in effects:
                            wild_options += [3, 3]
                        else:
                            wild_options += [3]
                        multiplier = random.choice(wild_options)

                        # Sequin charm overrides floor
                        if "wild_floor_once" in active_effects:
                            multiplier = max(multiplier, 1.0)
                            del active_effects["wild_floor_once"]

                        if multiplier == 0:
                            special_msg = "\n🎪 *The crowd was not impressed...*"
                        elif multiplier >= 2:
                            special_msg = f"\n🎪 **STANDING OVATION! {multiplier}x haul!**"

                    elif player["class"] == "Inmate":
                        if random.random() < chaos_chance:
                            multiplier  = chaos_mult
                            special_msg = f"\n🎲 **CHAOS ROLL! {chaos_mult}x resources!**"

                    elif player["class"] == "Cultist":
                        # Ritual: chance to find rare item
                        ritual_chance = 0.25 if "ritual_boost" in effects else 0.15
                        if random.random() < ritual_chance:
                            ritual_pool = ["trick_coin", "bone_brew", "sequin_charm"]
                            if "ritual_cursed" in effects:
                                ritual_pool += ["cursed_relic", "soul_shard"]
                            ritual_item = random.choice(ritual_pool)
                            add_item(player, ritual_item, 1)
                            item_name   = ITEMS.get(ritual_item, {}).get("name", ritual_item)
                            item_emoji  = ITEMS.get(ritual_item, {}).get("emoji", "✨")
                            special_msg = f"\n🕯️ **RITUAL!** You found {item_emoji} {item_name}!"

                    elif player["class"] == "Executioner":
                        # Precision: max roll on one (or both with upgrade) resource
                        precision_both = "precision_double" in effects
                        special_msg = "\n⚙️ *Precision strike!*"

                    # ── Roll resources (guild resources only) ─────────────────
                    resources = guild_cfg.get("resources", [])
                    gained    = {}

                    for i, item_id in enumerate(resources):
                        mn, mx   = BASE_GATHER.get(item_id, (1, 4))
                        bonus    = bonuses.get(item_id, 1.0)

                        # Executioner precision: max roll
                        if player["class"] == "Executioner":
                            if i == 0 or "precision_double" in effects:
                                base_qty = mx
                            else:
                                base_qty = random.randint(mn, mx)
                        else:
                            base_qty = random.randint(mn, mx)

                        qty = max(0, int(base_qty * bonus * multiplier))
                        if qty > 0:
                            gained[item_id] = qty
                            add_item(player, item_id, qty)

                    # ── Sea Lion splash ───────────────────────────────────────
                    splash_msg   = ""
                    splash_bonus = 3 if "splash_triple" in effects else 2
                    splash_count = 2 if "splash_double" in effects else 1

                    if player["class"] == "Sea Lion" and gained.get("fish", 0) > 0:
                        all_others = [
                            (uid, p) for uid, p in data["players"].items()
                            if p.get("guild") and uid != str(ctx.author.id)
                        ]
                        random.shuffle(all_others)
                        for uid, sp in all_others[:splash_count]:
                            add_item(sp, "fish", splash_bonus)
                            splash_msg += f"\n🦭 Splash! <@{uid}> got +{splash_bonus} fish!"

                    set_cooldown(player, "gather")
                    player["stats"]["total_gathers"] += 1
                    levelled = add_xp(player, XP_PER_GATHER, XP_PER_LEVEL)
                    save_data(data)

                # ── Build response (outside lock) ─────────────────────────────
                if not gained:
                    result_str = "Nothing this time..."
                else:
                    result_str = "  ".join(
                        f"{ITEMS[k]['emoji']} {v} {ITEMS[k]['name']}"
                        for k, v in gained.items()
                    )

                msg = (
                    f"{guild_cfg['emoji']} **{ctx.author.display_name}** "
                    f"({player['class']}) gathered: **{result_str}**"
                    f"{special_msg}"
                )
                if splash_msg:
                    msg += splash_msg
                if levelled:
                    msg += f"\n⬆️ **LEVEL UP! Now level {player['level']}!**"

                await ctx.send(msg)

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    @commands.command(name="craft")
    async def craft(self, ctx, *, item_name: str = None):
        """Craft an item. Usage: !craft <item>"""
        try:
            if item_name is None:
                lines = ["**⚒️ Craft Recipes:**\n"]
                for item_id, recipe in RECIPES.items():
                    item        = ITEMS.get(item_id, {"name": item_id, "emoji": "❓"})
                    restriction = f" *({recipe['class_only']} only)*" if recipe["class_only"] else ""
                    lines.append(
                        f"{item['emoji']} **{item['name']}**{restriction} — {recipe['description']}"
                    )
                await ctx.send("\n".join(lines))
                return

            matched_id = None
            for item_id in RECIPES:
                item = ITEMS.get(item_id, {"name": item_id})
                if item_name.lower() in [item_id.lower(), item["name"].lower()]:
                    matched_id = item_id
                    break

            if matched_id is None:
                await ctx.send(f"❌ No recipe for `{item_name}`. Type `!craft` to see recipes.")
                return

            if user_lock(ctx.author.id, "craft").locked():
                return

            async with user_lock(ctx.author.id, "craft"):
                async with data_lock:
                    data   = load_data()
                    player = get_player(data, ctx.author)
                    recipe = RECIPES[matched_id]

                    if recipe["class_only"] and player["class"] != recipe["class_only"]:
                        await ctx.send(
                            f"❌ Only a **{recipe['class_only']}** can craft that."
                        )
                        return

                    # Cooldown — reduced if Club Soda has craft_speed upgrade
                    craft_cd = COOLDOWNS["craft"]
                    if player["guild"]:
                        effects = get_guild_effects(data, player["guild"])
                        if "craft_speed" in effects and player["guild"] == "club_soda":
                            craft_cd = 180

                    remaining = cooldown_remaining(player, "craft", craft_cd)
                    if remaining > 0 and not is_super(ctx):
                        await ctx.send(f"⏳ Craft cooldown: **{fmt_time(remaining)}** remaining.")
                        return

                    # Check ingredients
                    for need_item, qty in recipe["needs"].items():
                        if player["inventory"].get(need_item, 0) < qty:
                            item_info = ITEMS.get(need_item, {"name": need_item, "emoji": "❓"})
                            await ctx.send(
                                f"❌ You need **{qty}x {item_info['emoji']} {item_info['name']}**."
                            )
                            return

                    for need_item, qty in recipe["needs"].items():
                        remove_item(player, need_item, qty)

                    add_item(player, matched_id, 1)
                    set_cooldown(player, "craft")
                    save_data(data)

                result_item = ITEMS.get(matched_id, {"name": matched_id, "emoji": "✨"})
                await ctx.send(
                    f"⚒️ **{ctx.author.display_name}** crafted "
                    f"**{result_item['emoji']} {result_item['name']}**!"
                )

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")


async def setup(bot):
    await bot.add_cog(GatherCog(bot))
