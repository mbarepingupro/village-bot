"""
cogs/craft.py — Cosmetic crafting and equipping
=================================================
Commands:
  !craft              → see all recipes by tier
  !craft <item>       → craft a cosmetic
  !equip <item>       → equip a cosmetic to your penguin
"""

import discord
from discord.ext import commands
from config import ITEMS, RECIPES
from cogs.data import (
    load_data, save_data, get_player,
    add_item, remove_item, data_lock, user_lock, is_super
)


def match_item(name: str, pool: dict) -> str | None:
    """Match a user input to an item_id. Searches id and display name."""
    name = name.lower().strip()
    for item_id in pool:
        item = ITEMS.get(item_id, {"name": item_id})
        if name in [item_id.lower(), item["name"].lower()]:
            return item_id
    return None


class CraftCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ── !craft ────────────────────────────────────────────────────────────────
    @commands.command(name="craft")
    async def craft(self, ctx, *, item_name: str = None):
        """Craft a cosmetic. Usage: !craft or !craft <item name>"""

        # ── No args: show recipe list ─────────────────────────────────────────
        if item_name is None:
            try:
                data   = load_data()
                player = get_player(data, ctx.author)
                save_data(data)

                inv    = player["inventory"]
                tokens = inv.get("loot_token", 0)

                for tier_name, tier_label, tier_emoji in [
                    ("common",    "Common",    "🟢"),
                    ("rare",      "Rare",      "🔵"),
                    ("legendary", "Legendary", "🟡"),
                ]:
                    recipes = {k: v for k, v in RECIPES.items() if v["tier"] == tier_name}
                    if not recipes:
                        continue

                    lines = [f"\n{tier_emoji} **{tier_label} Cosmetics**"]
                    for item_id, recipe in recipes.items():
                        item = ITEMS.get(item_id, {"name": item_id, "emoji": "❓"})

                        # Check if already owned
                        owned = (
                            inv.get(item_id, 0) > 0 or
                            item_id in player.get("cosmetics", {}).values()
                        )
                        if owned:
                            lines.append(f"  ✅ {item['emoji']} **{item['name']}** — *owned*")
                            continue

                        # Build cost string with have/need
                        costs = []
                        can_afford = True
                        for res_id, qty in recipe["needs"].items():
                            res  = ITEMS.get(res_id, {"emoji": "❓", "name": res_id})
                            have = inv.get(res_id, 0)
                            mark = "✓" if have >= qty else "✗"
                            if have < qty:
                                can_afford = False
                            costs.append(f"{res['emoji']}{have}/{qty}")

                        token_cost = recipe["tokens"]
                        token_mark = "✓" if tokens >= token_cost else "✗"
                        if tokens < token_cost:
                            can_afford = False
                        costs.append(f"🎟️{tokens}/{token_cost}")

                        status = "**READY**" if can_afford else ""
                        cost_str = "  ".join(costs)
                        lines.append(
                            f"  {item['emoji']} **{item['name']}** [{item.get('slot', '?')}] — {cost_str} {status}"
                        )

                    await ctx.send("\n".join(lines))

                await ctx.send("\nUse `!craft <item name>` to craft.")

            except Exception as e:
                await ctx.send(f"❌ Error: {e}")
            return

        # ── Craft a specific item ─────────────────────────────────────────────
        try:
            matched_id = match_item(item_name, RECIPES)

            if matched_id is None:
                await ctx.send(
                    f"❌ No recipe for `{item_name}`. Type `!craft` to see all recipes."
                )
                return

            if user_lock(ctx.author.id, "craft").locked():
                return

            async with user_lock(ctx.author.id, "craft"):
                async with data_lock:
                    data   = load_data()
                    player = get_player(data, ctx.author)
                    recipe = RECIPES[matched_id]
                    item   = ITEMS.get(matched_id, {"name": matched_id, "emoji": "❓"})
                    inv    = player["inventory"]

                    # Check if already owned
                    already_owned = (
                        inv.get(matched_id, 0) > 0 or
                        matched_id in player.get("cosmetics", {}).values()
                    )
                    if already_owned and not is_super(ctx):
                        await ctx.send(f"✅ You already have **{item['emoji']} {item['name']}**!")
                        return

                    # Check loot tokens
                    token_cost = recipe["tokens"]
                    tokens     = inv.get("loot_token", 0)
                    if tokens < token_cost:
                        need = token_cost - tokens
                        await ctx.send(
                            f"🎟️ You need **{token_cost} Loot Token{'s' if token_cost != 1 else ''}** "
                            f"but only have **{tokens}**.\n"
                            f"Watch **{need}** more stream{'s' if need != 1 else ''} to earn enough!"
                        )
                        return

                    # Check resources
                    for res_id, qty in recipe["needs"].items():
                        if inv.get(res_id, 0) < qty:
                            res = ITEMS.get(res_id, {"name": res_id, "emoji": "❓"})
                            have = inv.get(res_id, 0)
                            await ctx.send(
                                f"❌ You need **{qty}x {res['emoji']} {res['name']}** "
                                f"but only have **{have}**."
                            )
                            return

                    # ── Deduct costs ──────────────────────────────────────────
                    remove_item(player, "loot_token", token_cost)
                    for res_id, qty in recipe["needs"].items():
                        remove_item(player, res_id, qty)

                    # ── Grant cosmetic ────────────────────────────────────────
                    add_item(player, matched_id, 1)
                    save_data(data)

            tier  = recipe["tier"]
            emoji = {"common": "🟢", "rare": "🔵", "legendary": "🟡"}.get(tier, "✨")

            msg = (
                f"{emoji} **{ctx.author.display_name}** crafted "
                f"**{item['emoji']} {item['name']}**!"
            )
            if tier == "legendary":
                msg += "\n🏆 **LEGENDARY CRAFT!** The village is in awe!"
            elif tier == "rare":
                msg += "\n⭐ A rare cosmetic. Looking good!"

            msg += f"\nUse `!equip {item['name']}` to put it on your penguin!"
            await ctx.send(msg)

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !equip ────────────────────────────────────────────────────────────────
    @commands.command(name="equip")
    async def equip(self, ctx, *, item_name: str):
        """Equip a cosmetic you've crafted. Usage: !equip jester hat"""
        try:
            # Search owned cosmetics in inventory
            data   = load_data()
            player = get_player(data, ctx.author)

            matched_id = None
            for item_id in player["inventory"]:
                item_def = ITEMS.get(item_id, {})
                if item_def.get("type") != "cosmetic":
                    continue
                if item_name.lower() in [item_id.lower(), item_def.get("name", "").lower()]:
                    matched_id = item_id
                    break

            # Also check already-equipped cosmetics
            if matched_id is None:
                for slot, item_id in player.get("cosmetics", {}).items():
                    item_def = ITEMS.get(item_id, {})
                    if item_name.lower() in [item_id.lower(), item_def.get("name", "").lower()]:
                        await ctx.send(
                            f"✅ **{item_def.get('emoji', '✨')} {item_def.get('name', item_id)}** "
                            f"is already equipped!"
                        )
                        return

            if matched_id is None:
                await ctx.send(
                    f"❌ You don't have a cosmetic called `{item_name}`. "
                    f"Craft one with `!craft`."
                )
                return

            item_def = ITEMS.get(matched_id, {})
            slot     = item_def.get("slot", "accessory")

            player.setdefault("cosmetics", {})[slot] = matched_id
            save_data(data)

            await ctx.send(
                f"✨ **{ctx.author.display_name}** equipped "
                f"**{item_def['emoji']} {item_def['name']}** [{slot}]!\n"
                f"*{item_def['description']}*\n"
                f"Now show it off on stream with Stream Avatars!"
            )

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")


async def setup(bot):
    await bot.add_cog(CraftCog(bot))
