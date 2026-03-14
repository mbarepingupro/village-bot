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
            await ctx.send("gather reached")
            super_user = is_super(ctx)
            await ctx.send(f"super check passed: {super_user}")
            data = load_data()
            await ctx.send("data loaded")
            player = get_player(data, ctx.author)
            await ctx.send("player loaded")
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
