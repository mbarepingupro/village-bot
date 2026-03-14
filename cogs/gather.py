"""
cogs/gather.py — Gathering and crafting
=========================================
Commands: !gather, !craft

Spam protection:
- user_lock  : blocks the same user running !gather twice simultaneously
- data_lock  : blocks concurrent writes from different users corrupting the file
- cooldown   : per-user time gate stored in the save file
"""

import random
import discord
from discord.ext import commands
from config import GUILDS, ITEMS, BASE_GATHER, COOLDOWNS, XP_PER_GATHER, XP_PER_LEVEL
from cogs.data import (
    load_data, save_data, get_player,
    add_item, cooldown_remaining, set_cooldown, add_xp, fmt_time,
    data_lock, user_lock, is_super
)

# ── Craft recipes ─────────────────────────────────────────────────────────────
RECIPES = {
    "mystery_potion": {
        "needs":      {"herbs": 3, "fish": 1},
        "class_only": "Mixologist",
        "description": "3 herbs + 1 fish → Mystery Potion (Mixologist only)",
    },
}


class GatherCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="gather")
    async def gather(self, ctx):
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
    
                    remaining = cooldown_remaining(player, "gather", COOLDOWNS["gather"])
                    if remaining > 0 and not is_super(ctx):
                        await ctx.send(f"⏳ {ctx.author.mention} Rest for **{fmt_time(remaining)}** before gathering again.")
                        return
    
                    guild_cfg = GUILDS[player["guild"]]
                    bonuses   = dict(guild_cfg.get("gather_bonus", {}))
    
                    tool_id = player.get("equipped_tool")
                    if tool_id:
                        tool_def = ITEMS.get(tool_id, {})
                        for res, bonus in tool_def.get("bonus", {}).items():
                            bonuses[res] = bonuses.get(res, 1.0) + bonus
    
                    multiplier = 1.0
                    # Check for active effects (e.g. from mystery potion or trick coin)
                    active_effects = player.get("active_effects", {})
                    if "gather_multiplier" in active_effects:
                        multiplier = active_effects.pop("gather_multiplier")
                    if player["class"] == "Performer":
                        multiplier = random.choice([0, 0, 0.5, 1, 1, 1.5, 2, 3])
                    elif player["class"] == "Inmate":
                        if random.random() < 0.2:
                            multiplier = 2.0
    
                    gained = {}
                    for item_id, (mn, mx) in BASE_GATHER.items():
                        base_qty = random.randint(mn, mx)
                        bonus    = bonuses.get(item_id, 1.0)
                        qty      = max(0, int(base_qty * bonus * multiplier))
                        if qty > 0:
                            gained[item_id] = qty
                            add_item(player, item_id, qty)
    
                    splash_msg = ""
                    if player["class"] == "Sea Lion" and gained.get("fish", 0) > 0:
                        all_others = [
                            (uid, p) for uid, p in data["players"].items()
                            if p.get("guild") and uid != str(ctx.author.id)
                        ]
                        random.shuffle(all_others)
                        for uid, sp in all_others[:2]:
                            add_item(sp, "fish", 1)
                            splash_msg += f"\n🦭 Splash! <@{uid}> got +1 fish!"
    
                    set_cooldown(player, "gather")
                    player["stats"]["total_gathers"] += 1
                    levelled = add_xp(player, XP_PER_GATHER, XP_PER_LEVEL)
                    save_data(data)
    
                if not gained:
                    result_str = "Nothing! Better luck next time."
                else:
                    result_str = "  ".join(
                        f"{ITEMS[k]['emoji']} {v} {ITEMS[k]['name']}"
                        for k, v in gained.items()
                    )
    
                msg = (
                    f"{guild_cfg['emoji']} **{ctx.author.display_name}** ({player['class']}) gathered: "
                    f"**{result_str}**"
                )
                if multiplier == 2.0 and player["class"] == "Inmate":
                    msg += "\n🎲 **CHAOS ROLL! Double resources!**"
                if player["class"] == "Performer":
                    if multiplier == 0:
                        msg += "\n🎪 *The crowd was not impressed...*"
                    elif multiplier >= 2:
                        msg += f"\n🎪 **STANDING OVATION! {int(multiplier)}x haul!**"
                if splash_msg:
                    msg += splash_msg
                if levelled:
                    msg += f"\n⬆️ **LEVEL UP! {ctx.author.display_name} is now level {player['level']}!**"
    
                await ctx.send(msg)
    
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
            
    @commands.command(name="craft")
    async def craft(self, ctx, *, item_name: str = None):
        """Craft an item. Usage: !craft <item>"""

        if item_name is None:
            lines = ["**⚒️ Craft Recipes:**\n"]
            for item_id, recipe in RECIPES.items():
                item = ITEMS.get(item_id, {"name": item_id, "emoji": "❓"})
                restriction = f" *({recipe['class_only']} only)*" if recipe["class_only"] else ""
                lines.append(f"{item['emoji']} **{item['name']}**{restriction} — {recipe['description']}")
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
                    await ctx.send(f"❌ Only a **{recipe['class_only']}** can craft that.")
                    return

                remaining = cooldown_remaining(player, "gather", COOLDOWNS["gather"])
                super_user = is_super(ctx)
                await ctx.send(f"debug: remaining={remaining}, super={super_user}")
                if remaining > 0 and not super_user:
                    await ctx.send(f"⏳ {ctx.author.mention} Rest for **{fmt_time(remaining)}** before gathering again.")
                    return

                for need_item, qty in recipe["needs"].items():
                    if player["inventory"].get(need_item, 0) < qty:
                        item_info = ITEMS.get(need_item, {"name": need_item, "emoji": "❓"})
                        await ctx.send(
                            f"❌ You need **{qty}x {item_info['emoji']} {item_info['name']}** to craft this."
                        )
                        return

                for need_item, qty in recipe["needs"].items():
                    from cogs.data import remove_item
                    remove_item(player, need_item, qty)

                add_item(player, matched_id, 1)
                set_cooldown(player, "craft")
                save_data(data)

            result_item = ITEMS.get(matched_id, {"name": matched_id, "emoji": "✨"})
            await ctx.send(
                f"⚒️ **{ctx.author.display_name}** crafted "
                f"**{result_item['emoji']} {result_item['name']}**!"
            )


async def setup(bot):
    await bot.add_cog(GatherCog(bot))
