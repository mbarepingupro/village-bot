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
    sanitize_qty, data_lock, user_lock, is_super, fmt_gold
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
            f"💰 **{ctx.author.display_name}** has **{fmt_gold(player['gold'])}g**.\n"
            f"Earn more by selling resources (`!sell`) or claiming loot drops (`!loot`)."
        )

    # ── !prices ───────────────────────────────────────────────────────────────
    @commands.command(name="prices")
    async def prices(self, ctx):
        """Show current resource sell prices."""
        lines = ["**💱 Resource Sell Prices**\n",
                 "*Bank buyback prices coming soon — use `!sell <item> <qty>` to sell*\n"]
        for item_id, price in SELL_PRICES.items():
            item = ITEMS.get(item_id, {"name": item_id, "emoji": "❓"})
            lines.append(f"{item['emoji']} **{item['name']}** — {price}g each")
        await ctx.send("\n".join(lines))

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
            f"Balance: **{fmt_gold(player['gold'])}g**"
        )

    # ── !shop ─────────────────────────────────────────────────────────────────
    @commands.command(name="shop")
    async def shop(self, ctx):
        """Browse the shop. Buy with !buy <item>."""
        try:
            data   = load_data()
            player = get_player(data, ctx.author)
            save_data(data)

            player_guild = player.get("guild")
            player_level = player.get("level", 1)

            tools      = []
            cosmetics  = []
            exclusives = []
            locked_out = []

            for item_id, listing in SHOP.items():
                item      = ITEMS.get(item_id, {"name": item_id, "emoji": "❓", "type": "?"})
                price     = listing["price"]
                guild_key = listing.get("guild_only")
                min_level = listing.get("min_level", 1)
                owned     = (player["inventory"].get(item_id, 0) > 0 or
                             player.get("equipped_tool") == item_id or
                             item_id in player.get("cosmetics", {}).values())

                # Level locked
                if player_level < min_level and not is_super(ctx):
                    locked_out.append(
                        f"🔒 **{item['name']}** — *requires level {min_level}*"
                    )
                    continue

                tag = "✅ owned" if owned else f"{price}g"

                if guild_key:
                    guild_name = GUILDS.get(guild_key, {}).get("display_name", guild_key)
                    lock = "" if player_guild == guild_key else f" 🔒 *{guild_name} only*"
                    exclusives.append(
                        f"{item['emoji']} **{item['name']}** — {tag}{lock}\n"
                        f"   *{item['description']}*"
                    )
                elif item["type"] == "tool":
                    tools.append(
                        f"{item['emoji']} **{item['name']}** — {tag}\n"
                        f"   *{item['description']}*"
                    )
                else:
                    cosmetics.append(
                        f"{item['emoji']} **{item['name']}** — {tag}\n"
                        f"   *{item['description']}*"
                    )

            lines = [
                f"🏪 **The Shop** — Level {player_level} | Balance: **{fmt_gold(player['gold'])}g**\n"
            ]

            if tools:
                lines.append("**⚒️ Gather Tools**")
                lines.extend(tools)
            if cosmetics:
                lines.append("\n**🎨 Cosmetics**")
                lines.extend(cosmetics)
            if exclusives:
                lines.append("\n**⭐ Guild Exclusives**")
                lines.extend(exclusives)
            if locked_out:
                lines.append("\n**🔒 Locked (level up to unlock)**")
                lines.extend(locked_out)

            lines.append("\nUse `!buy <item name>` to purchase.")
            await ctx.send("\n".join(lines))

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !buy ──────────────────────────────────────────────────────────────────
    @commands.command(name="buy")
    async def buy(self, ctx, *, item_name: str):
        """Buy an item from the shop. Usage: !buy iron axe"""
        try:
            data   = load_data()
            player = get_player(data, ctx.author)

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

            # Level check
            min_level = listing.get("min_level", 1)
            if player.get("level", 1) < min_level and not is_super(ctx):
                await ctx.send(
                    f"🔒 **{item_def['name']}** requires **level {min_level}**. "
                    f"You are level {player.get('level', 1)}."
                )
                return

            # Guild restriction
            guild_key = listing.get("guild_only")
            if guild_key and player.get("guild") != guild_key and not is_super(ctx):
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

            price = listing["price"]

            if user_lock(ctx.author.id, "buy").locked():
                return

            async with user_lock(ctx.author.id, "buy"):
                async with data_lock:
                    data   = load_data()
                    player = get_player(data, ctx.author)
                    if not spend_gold(player, price):
                        await ctx.send(
                            f"❌ Not enough gold! **{item_def['name']}** costs **{price}g** "
                            f"but you only have **{fmt_gold(player['gold'])}g**."
                        )
                        return
                    add_item(player, matched_id, 1)
                    save_data(data)

            await ctx.send(
                f"🛍️ **{ctx.author.display_name}** bought **{item_def['emoji']} {item_def['name']}** "
                f"for **{price}g**!\n"
                f"Remaining balance: **{fmt_gold(player['gold'])}g**\n"
                + (f"Use `!equip {item_def['name']}` to put it to work!"
                   if item_def["type"] in ("tool", "cosmetic") else "")
            )

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !equip ────────────────────────────────────────────────────────────────
    @commands.command(name="equip")
    async def equip(self, ctx, *, item_name: str):
        """Equip a tool or cosmetic you own. Usage: !equip iron axe"""
        try:
            data   = load_data()
            player = get_player(data, ctx.author)

            matched_id = None
            for item_id in player["inventory"]:
                item = ITEMS.get(item_id, {"name": item_id})
                if item_name.lower() in [item_id.lower(), item["name"].lower()]:
                    matched_id = item_id
                    break

            if matched_id is None:
                await ctx.send(
                    f"❌ You don't have `{item_name}` in your bag. "
                    f"Buy it with `!buy` first."
                )
                return

            item_def   = ITEMS.get(matched_id, {})
            item_type  = item_def.get("type")

            # Level check — use shop min_level if item is in shop
            if matched_id in SHOP:
                min_level = SHOP[matched_id].get("min_level", 1)
                if player.get("level", 1) < min_level and not is_super(ctx):
                    await ctx.send(
                        f"🔒 **{item_def['name']}** requires **level {min_level}** to equip. "
                        f"You are level {player.get('level', 1)}."
                    )
                    return

            if item_type == "tool":
                player["equipped_tool"] = matched_id
                save_data(data)
                await ctx.send(
                    f"⚒️ **{ctx.author.display_name}** equipped "
                    f"**{item_def['emoji']} {item_def['name']}**!\n"
                    f"*{item_def['description']}*"
                )
            elif item_type == "cosmetic":
                slot = item_def.get("slot", "accessory")
                player.setdefault("cosmetics", {})[slot] = matched_id
                save_data(data)
                await ctx.send(
                    f"✨ **{ctx.author.display_name}** equipped "
                    f"**{item_def['emoji']} {item_def['name']}** [{slot}]!\n"
                    f"*{item_def['description']}*"
                )
            else:
                await ctx.send(f"❌ **{item_def.get('name', matched_id)}** can't be equipped.")

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !addgold ──────────────────────────────────────────────────────────────
    @commands.command(name="addgold")
    async def addgold(self, ctx, amount: int = 9999):
        """[MOD] Add gold for testing. Usage: !addgold or !addgold 50000"""
        try:
            if not is_super(ctx):
                return
            async with data_lock:
                data   = load_data()
                player = get_player(data, ctx.author)
                add_gold(player, amount)
                save_data(data)
            await ctx.send(
                f"💰 Added **{amount}g** to {ctx.author.display_name}. "
                f"Balance: **{fmt_gold(player['gold'])}g**"
            )
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !giveitem ─────────────────────────────────────────────────────────────
    @commands.command(name="giveitem")
    async def giveitem(self, ctx, target: discord.Member = None, *, item_name: str = None):
        """[MOD] Give any item to a player. Usage: !giveitem @user penguin helmet"""
        try:
            if not is_super(ctx):
                return
            if target is None or item_name is None:
                await ctx.send("Usage: `!giveitem @user <item name>`")
                return

            # Match item
            matched_id = None
            for item_id, item_def in ITEMS.items():
                if item_name.lower() in [item_id.lower(), item_def["name"].lower()]:
                    matched_id = item_id
                    break

            if matched_id is None:
                await ctx.send(f"❌ Item `{item_name}` not found.")
                return

            async with data_lock:
                data   = load_data()
                player = get_player(data, target)
                add_item(player, matched_id, 1)
                save_data(data)

            item_def = ITEMS[matched_id]
            await ctx.send(
                f"🎁 Gave **{item_def['emoji']} {item_def['name']}** to **{target.display_name}**!"
            )

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")


async def setup(bot):
    await bot.add_cog(EconomyCog(bot))
