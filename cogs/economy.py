"""
cogs/economy.py — Gold economy
================================
Commands: !gold, !sell, !shop, !buy, !equip
"""

import discord
from discord.ext import commands
from config import GUILDS, ITEMS, SELL_PRICES, SHOP
from cogs.data import (
    load_data, save_data, get_player,
    add_item, remove_item, add_gold, spend_gold,
    sanitize_qty, data_lock, user_lock
)


class EconomyCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ── !gold ─────────────────────────────────────────────────────────────────
    @commands.command(name="gold", aliases=["wallet", "coins"])
    async def gold(self, ctx):
        """Check your gold balance."""
        data   = load_data()
        player = get_player(data, ctx.author)
        save_data(data)
        await ctx.send(
            f"💰 **{ctx.author.display_name}** has **{player['gold']} gold**.\n"
            f"Earn more by selling resources (`!sell`) or claiming loot drops (`!loot`)."
        )

    # ── !sell ─────────────────────────────────────────────────────────────────
    @commands.command(name="sell")
    async def sell(self, ctx, item_name: str = None, qty: int = None):
        """Sell resources for gold. Usage: !sell <item> <qty> or !sell all"""
        data   = load_data()
        player = get_player(data, ctx.author)

        # Show sell prices if no args
        if item_name is None:
            lines = ["**💱 Sell Prices (per unit):**\n"]
            for item_id, price in SELL_PRICES.items():
                item = ITEMS.get(item_id, {"name": item_id, "emoji": "❓"})
                in_bag = player["inventory"].get(item_id, 0)
                lines.append(
                    f"{item['emoji']} **{item['name']}** — {price}💰 each  *(you have {in_bag})*"
                )
            lines.append("\nUsage: `!sell wood 10`  or  `!sell wood all`")
            await ctx.send("\n".join(lines))
            return

        # Match item
        matched_id = None
        for item_id in SELL_PRICES:
            item = ITEMS.get(item_id, {"name": item_id})
            if item_name.lower() in [item_id.lower(), item["name"].lower()]:
                matched_id = item_id
                break

        if matched_id is None:
            await ctx.send(
                f"❌ `{item_name}` can't be sold here. Type `!sell` to see what's accepted."
            )
            return

        in_bag = player["inventory"].get(matched_id, 0)
        if in_bag == 0:
            await ctx.send(f"❌ You don't have any {ITEMS[matched_id]['emoji']} {ITEMS[matched_id]['name']} to sell.")
            return

        # Resolve qty — sanitize to prevent negative/zero exploits
        if qty is None or str(qty).lower() == "all":
            qty = in_bag
        qty = sanitize_qty(qty, in_bag)
        if qty is None:
            await ctx.send("❌ Please provide a valid quantity greater than 0.")
            return

        if user_lock(ctx.author.id, "sell").locked():
            return

        async with user_lock(ctx.author.id, "sell"):
            async with data_lock:
                data   = load_data()
                player = get_player(data, ctx.author)
                # Re-check inventory inside lock (could have changed)
                in_bag = player["inventory"].get(matched_id, 0)
                qty    = min(qty, in_bag)
                if qty <= 0:
                    await ctx.send("❌ Nothing to sell.")
                    return
                price    = SELL_PRICES[matched_id]
                earned   = price * qty
                item_def = ITEMS[matched_id]
                remove_item(player, matched_id, qty)
                add_gold(player, earned)
                save_data(data)

        await ctx.send(
            f"💱 **{ctx.author.display_name}** sold **{qty}x {item_def['emoji']} {item_def['name']}** "
            f"for **{earned}💰 gold**.\n"
            f"Balance: **{player['gold']} gold**"
        )

    # ── !shop ─────────────────────────────────────────────────────────────────
    @commands.command(name="shop")
    async def shop(self, ctx):
        """Browse the shop. Buy with !buy <item>."""
        data   = load_data()
        player = get_player(data, ctx.author)
        save_data(data)

        player_guild = player.get("guild")

        tools      = []
        cosmetics  = []
        exclusives = []

        for item_id, listing in SHOP.items():
            item      = ITEMS.get(item_id, {"name": item_id, "emoji": "❓", "type": "?"})
            price     = listing["price"]
            guild_key = listing.get("guild_only")
            owned     = player["inventory"].get(item_id, 0) > 0 or player.get("equipped_tool") == item_id

            tag = "✅ owned" if owned else f"{price}💰"

            if guild_key:
                guild_name = GUILDS.get(guild_key, {}).get("display_name", guild_key)
                lock = "" if player_guild == guild_key else f" 🔒 *{guild_name} only*"
                exclusives.append(f"{item['emoji']} **{item['name']}** — {tag}{lock}\n   *{item['description']}*")
            elif item["type"] == "tool":
                tools.append(f"{item['emoji']} **{item['name']}** — {tag}\n   *{item['description']}*")
            else:
                cosmetics.append(f"{item['emoji']} **{item['name']}** — {tag}\n   *{item['description']}*")

        lines = [f"🏪 **The Shop** — your balance: **{player['gold']}💰**\n"]

        if tools:
            lines.append("**⚒️ Gather Tools**")
            lines.extend(tools)
        if cosmetics:
            lines.append("\n**🎨 Cosmetics**")
            lines.extend(cosmetics)
        if exclusives:
            lines.append("\n**⭐ Guild Exclusives**")
            lines.extend(exclusives)

        lines.append("\nUse `!buy <item name>` to purchase.")
        await ctx.send("\n".join(lines))

    # ── !buy ──────────────────────────────────────────────────────────────────
    @commands.command(name="buy")
    async def buy(self, ctx, *, item_name: str):
        """Buy an item from the shop. Usage: !buy iron axe"""
        data   = load_data()
        player = get_player(data, ctx.author)

        # Match shop listing
        matched_id = None
        for item_id in SHOP:
            item = ITEMS.get(item_id, {"name": item_id})
            if item_name.lower() in [item_id.lower(), item["name"].lower()]:
                matched_id = item_id
                break

        if matched_id is None:
            await ctx.send(f"❌ `{item_name}` not found in the shop. Check `!shop`.")
            return

        listing  = SHOP[matched_id]
        item_def = ITEMS[matched_id]

        # Guild restriction
        guild_key = listing.get("guild_only")
        if guild_key and player.get("guild") != guild_key:
            guild_name = GUILDS.get(guild_key, {}).get("display_name", guild_key)
            await ctx.send(f"🔒 **{item_def['name']}** is only available to **{guild_name}** members.")
            return

        # Already owned
        already_has = (
            player["inventory"].get(matched_id, 0) > 0 or
            player.get("equipped_tool") == matched_id or
            matched_id in player.get("cosmetics", {}).values()
        )
        if already_has and not is_super(ctx):
            await ctx.send(f"✅ You already own **{item_def['emoji']} {item_def['name']}**.")
            return

        # Funds check
        price = listing["price"]
        if not spend_gold(player, price):
            await ctx.send(
                f"❌ Not enough gold! **{item_def['name']}** costs **{price}💰** "
                f"but you only have **{player['gold']}💰**.\n"
                f"Sell resources with `!sell` to earn more."
            )
            return

        if user_lock(ctx.author.id, "buy").locked():
            return

        async with user_lock(ctx.author.id, "buy"):
            async with data_lock:
                # Re-load inside lock so concurrent buyers can't both succeed
                data   = load_data()
                player = get_player(data, ctx.author)
                # Re-check funds inside lock
                if not spend_gold(player, price):
                    await ctx.send(
                        f"❌ Not enough gold! **{item_def['name']}** costs **{price}💰** "
                        f"but you only have **{player['gold']}💰**."
                    )
                    return
                add_item(player, matched_id, 1)
                save_data(data)

        await ctx.send(
            f"🛍️ **{ctx.author.display_name}** bought **{item_def['emoji']} {item_def['name']}** "
            f"for **{price}💰**!\n"
            f"Remaining balance: **{player['gold']}💰**\n"
            + (f"Use `!equip {item_def['name']}` to put it to work!" if item_def["type"] in ("tool", "cosmetic") else "")
        )

    # ── !equip ────────────────────────────────────────────────────────────────
    @commands.command(name="equip")
    async def equip(self, ctx, *, item_name: str):
        """Equip a tool or cosmetic you own. Usage: !equip iron axe"""
        data   = load_data()
        player = get_player(data, ctx.author)

        # Match item in inventory
        matched_id = None
        for item_id in player["inventory"]:
            item = ITEMS.get(item_id, {"name": item_id})
            if item_name.lower() in [item_id.lower(), item["name"].lower()]:
                matched_id = item_id
                break

        if matched_id is None:
            await ctx.send(
                f"❌ You don't have `{item_name}` in your bag. "
                f"Buy it with `!buy` first, then equip it."
            )
            return

        item_def = ITEMS.get(matched_id, {})
        item_type = item_def.get("type")

        if item_type == "tool":
            player["equipped_tool"] = matched_id
            save_data(data)
            await ctx.send(
                f"⚒️ **{ctx.author.display_name}** equipped **{item_def['emoji']} {item_def['name']}**!\n"
                f"*{item_def['description']}*"
            )

        elif item_type == "cosmetic":
            slot = item_def.get("slot", "accessory")
            player.setdefault("cosmetics", {})[slot] = matched_id
            save_data(data)
            await ctx.send(
                f"✨ **{ctx.author.display_name}** equipped **{item_def['emoji']} {item_def['name']}** "
                f"[{slot}]!\n*{item_def['description']}*"
            )

        else:
            await ctx.send(f"❌ **{item_def.get('name', matched_id)}** can't be equipped.")


async def setup(bot):
    await bot.add_cog(EconomyCog(bot))
