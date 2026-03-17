"""
cogs/trade.py — Player-to-player trading
==========================================
Commands (trade channel only):
  !trade <qty> <item> @user                    → gift
  !trade <qty> <item> @user for <qty> <item>   → exchange offer
  !trade <qty>g @user                          → send gold
  !trade <qty>g @user for <qty> <item>         → gold for resources
  !accept                                      → accept your one pending offer
  !decline                                     → decline your one pending offer
  !tradeoffer                                  → see your pending incoming offer
  !canceltrade                                 → cancel your outgoing offer

Rules:
  - Must be used in the trade channel
  - One active outgoing offer per player at a time
  - One active incoming offer per player at a time
  - Offers expire after 5 minutes
  - Any item with tradeable: True can be traded, plus gold (use 'g' or 'gold')
"""

import time
import discord
from discord.ext import commands
from config import ITEMS, TRADE_CHANNEL
from cogs.data import (
    load_data, save_data, get_player,
    add_item, remove_item, add_gold, spend_gold,
    data_lock, user_lock, fmt_gold
)

TRADE_EXPIRY = 300   # 5 minutes


def get_trades(data: dict) -> dict:
    return data.setdefault("trades", {})


def expired(offer: dict) -> bool:
    return time.time() > offer["expires_at"]


def clean_expired(data: dict):
    """Remove expired offers and refund senders."""
    trades    = get_trades(data)
    to_delete = []
    for offer_id, offer in trades.items():
        if expired(offer):
            sender_uid = offer["from_uid"]
            if sender_uid in data["players"]:
                p = data["players"][sender_uid]
                if offer["offer_type"] == "gold":
                    add_gold(p, offer["offer_qty"])
                else:
                    add_item(p, offer["offer_item"], offer["offer_qty"])
            to_delete.append(offer_id)
    for oid in to_delete:
        del trades[oid]


def parse_item(token: str) -> tuple[str | None, bool]:
    """
    Try to match a token to an item_id or gold.
    Returns (item_id, is_gold).
    item_id is None if no match found.
    """
    token = token.lower().strip()
    if token in ("g", "gold"):
        return ("gold", True)
    for item_id, item_def in ITEMS.items():
        if token in [item_id.lower(), item_def["name"].lower()]:
            return (item_id, False)
    return (None, False)


def fmt_offer(offer: dict) -> str:
    """Human-readable offer string."""
    if offer["offer_type"] == "gold":
        giving = f"**{fmt_gold(offer['offer_qty'])}g**"
    else:
        item = ITEMS.get(offer["offer_item"], {"name": offer["offer_item"], "emoji": "❓"})
        giving = f"**{offer['offer_qty']}x {item['emoji']} {item['name']}**"

    if offer["want_type"] == "none":
        return f"{giving} as a gift"
    elif offer["want_type"] == "gold":
        return f"{giving} for **{fmt_gold(offer['want_qty'])}g**"
    else:
        want_item = ITEMS.get(offer["want_item"], {"name": offer["want_item"], "emoji": "❓"})
        return f"{giving} for **{offer['want_qty']}x {want_item['emoji']} {want_item['name']}**"


class TradeCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def in_trade_channel(self, ctx) -> bool:
        return ctx.channel.name == TRADE_CHANNEL

    # ── !trade ────────────────────────────────────────────────────────────────
    @commands.command(name="trade")
    async def trade(self, ctx, *, args: str = None):
        """
        Trade items or gold with another player.
        Usage:
          !trade 3 egg @user
          !trade 3 egg @user for 3 herb
          !trade 5g @user
          !trade 5g @user for 3 fish
        """
        try:
            if not self.in_trade_channel(ctx):
                await ctx.send(
                    f"🤝 Trades happen in <#{discord.utils.get(ctx.guild.text_channels, name=TRADE_CHANNEL).id}>!"
                    if discord.utils.get(ctx.guild.text_channels, name=TRADE_CHANNEL)
                    else f"🤝 Trades happen in the #{TRADE_CHANNEL} channel!"
                )
                return

            if args is None:
                await ctx.send(
                    "**Usage:**\n"
                    "`!trade 3 egg @user` — gift\n"
                    "`!trade 3 egg @user for 3 herb` — exchange\n"
                    "`!trade 5g @user` — send gold\n"
                    "`!trade 5g @user for 3 fish` — gold for resources"
                )
                return

            # ── Parse arguments ───────────────────────────────────────────────
            # Split on "for" to separate offer from want
            parts = args.lower().split(" for ", 1)
            offer_str = parts[0].strip()
            want_str  = parts[1].strip() if len(parts) > 1 else None

            # Extract @mention from offer_str
            target = None
            if ctx.message.mentions:
                target = ctx.message.mentions[0]

            if target is None:
                await ctx.send("❌ You need to @mention the person you're trading with.")
                return

            if target.id == ctx.author.id:
                await ctx.send("❌ You can't trade with yourself.")
                return

            # Remove the mention from offer_str to parse qty + item
            mention_str = f"<@{target.id}>"
            mention_str2 = f"<@!{target.id}>"
            offer_str = offer_str.replace(mention_str, "").replace(mention_str2, "").strip()

            # Parse offer: "<qty> <item>" or "<qty>g"
            offer_tokens = offer_str.split()
            if len(offer_tokens) < 1:
                await ctx.send("❌ Couldn't parse your offer. Check the usage with `!trade`.")
                return

            # Handle "5g" or "5 g" or "5 gold"
            raw_qty = offer_tokens[0].rstrip("g")
            try:
                offer_qty = float(raw_qty) if offer_tokens[0].endswith("g") else int(offer_tokens[0])
                if offer_tokens[0].endswith("g"):
                    offer_item_id = "gold"
                    offer_is_gold = True
                else:
                    item_token = " ".join(offer_tokens[1:]).strip()
                    offer_item_id, offer_is_gold = parse_item(item_token)
            except ValueError:
                await ctx.send("❌ Invalid quantity. Example: `!trade 3 egg @user`")
                return

            if offer_item_id is None:
                await ctx.send(f"❌ Couldn't find that item. Check spelling or use `!prices` to see resources.")
                return

            if offer_qty <= 0:
                await ctx.send("❌ Quantity must be greater than 0.")
                return

            # Parse want (optional)
            want_item_id = None
            want_is_gold = False
            want_qty     = 0

            if want_str:
                want_tokens = want_str.split()
                try:
                    if want_tokens[0].endswith("g"):
                        want_qty     = float(want_tokens[0].rstrip("g"))
                        want_item_id = "gold"
                        want_is_gold = True
                    else:
                        want_qty      = int(want_tokens[0])
                        want_token    = " ".join(want_tokens[1:]).strip()
                        want_item_id, want_is_gold = parse_item(want_token)
                except ValueError:
                    await ctx.send("❌ Couldn't parse what you want. Example: `!trade 3 egg @user for 3 herb`")
                    return

                if want_item_id is None:
                    await ctx.send(f"❌ Couldn't find the item you want in exchange.")
                    return
                if want_qty <= 0:
                    await ctx.send("❌ The quantity you want must be greater than 0.")
                    return

            # ── Execute trade ─────────────────────────────────────────────────
            if user_lock(ctx.author.id, "trade").locked():
                return

            async with user_lock(ctx.author.id, "trade"):
                async with data_lock:
                    data   = load_data()
                    sender = get_player(data, ctx.author)
                    recip  = get_player(data, target)

                    clean_expired(data)
                    trades = get_trades(data)

                    # Check sender doesn't already have an outgoing offer
                    existing_out = [o for o in trades.values() if o["from_uid"] == str(ctx.author.id)]
                    if existing_out:
                        await ctx.send(
                            "❌ You already have a pending trade offer. "
                            "Use `!canceltrade` to cancel it first."
                        )
                        return

                    # Check recipient doesn't already have an incoming offer
                    existing_in = [o for o in trades.values() if o["to_uid"] == str(target.id)]
                    if existing_in:
                        await ctx.send(
                            f"❌ **{target.display_name}** already has a pending trade offer. "
                            f"Try again once it resolves."
                        )
                        return

                    # Validate sender has what they're offering
                    if offer_is_gold:
                        if round(sender.get("gold", 0), 1) < offer_qty:
                            await ctx.send(
                                f"❌ You only have **{fmt_gold(sender['gold'])}g**."
                            )
                            return
                        spend_gold(sender, offer_qty)
                    else:
                        in_bag = sender["inventory"].get(offer_item_id, 0)
                        if in_bag < offer_qty:
                            item_def = ITEMS.get(offer_item_id, {"name": offer_item_id, "emoji": "❓"})
                            await ctx.send(
                                f"❌ You only have **{in_bag}x {item_def['emoji']} {item_def['name']}**."
                            )
                            return
                        remove_item(sender, offer_item_id, int(offer_qty))

                    # For gifts (no want), complete immediately
                    if want_item_id is None:
                        if offer_is_gold:
                            add_gold(recip, offer_qty)
                            msg = (
                                f"🎁 **{ctx.author.display_name}** gifted "
                                f"**{fmt_gold(offer_qty)}g** to **{target.display_name}**!"
                            )
                        else:
                            item_def = ITEMS.get(offer_item_id, {"name": offer_item_id, "emoji": "❓"})
                            add_item(recip, offer_item_id, int(offer_qty))
                            msg = (
                                f"🎁 **{ctx.author.display_name}** gifted "
                                f"**{int(offer_qty)}x {item_def['emoji']} {item_def['name']}** "
                                f"to **{target.display_name}**!"
                            )
                        save_data(data)
                        await ctx.send(msg)
                        return

                    # Exchange offer — create pending trade
                    offer_id = f"{str(ctx.author.id)[-4:]}{str(target.id)[-4:]}"
                    trades[offer_id] = {
                        "from_uid":   str(ctx.author.id),
                        "from_name":  ctx.author.display_name,
                        "to_uid":     str(target.id),
                        "to_name":    target.display_name,
                        "offer_type": "gold" if offer_is_gold else "item",
                        "offer_item": offer_item_id,
                        "offer_qty":  offer_qty,
                        "want_type":  "gold" if want_is_gold else "item",
                        "want_item":  want_item_id,
                        "want_qty":   want_qty,
                        "expires_at": time.time() + TRADE_EXPIRY,
                    }
                    save_data(data)

                offer = trades[offer_id]
                await ctx.send(
                    f"🤝 **{ctx.author.display_name}** offers {fmt_offer(offer)} "
                    f"to {target.mention}\n"
                    f"Type `!accept` to accept or `!decline` to decline. "
                    f"*Expires in 5 minutes.*"
                )

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !accept ───────────────────────────────────────────────────────────────
    @commands.command(name="accept")
    async def accept(self, ctx):
        """Accept your pending incoming trade offer."""
        try:
            if not self.in_trade_channel(ctx):
                return

            async with user_lock(ctx.author.id, "accept"):
                async with data_lock:
                    data   = load_data()
                    clean_expired(data)
                    trades = get_trades(data)

                    # Find the one offer addressed to this user
                    my_offer    = None
                    my_offer_id = None
                    for oid, offer in trades.items():
                        if offer["to_uid"] == str(ctx.author.id):
                            my_offer    = offer
                            my_offer_id = oid
                            break

                    if my_offer is None:
                        await ctx.send("📭 You have no pending trade offer.")
                        return

                    recip  = get_player(data, ctx.author)
                    sender = data["players"].get(my_offer["from_uid"])

                    # Validate recipient has what sender wants
                    if my_offer["want_type"] == "gold":
                        if round(recip.get("gold", 0), 1) < my_offer["want_qty"]:
                            await ctx.send(
                                f"❌ You need **{fmt_gold(my_offer['want_qty'])}g** to accept this trade "
                                f"but only have **{fmt_gold(recip['gold'])}g**."
                            )
                            return
                        spend_gold(recip, my_offer["want_qty"])
                        if sender:
                            add_gold(sender, my_offer["want_qty"])
                    else:
                        want_id  = my_offer["want_item"]
                        want_qty = int(my_offer["want_qty"])
                        in_bag   = recip["inventory"].get(want_id, 0)
                        if in_bag < want_qty:
                            want_def = ITEMS.get(want_id, {"name": want_id, "emoji": "❓"})
                            await ctx.send(
                                f"❌ You need **{want_qty}x {want_def['emoji']} {want_def['name']}** "
                                f"to accept this trade but only have {in_bag}."
                            )
                            return
                        remove_item(recip, want_id, want_qty)
                        if sender:
                            add_item(sender, want_id, want_qty)

                    # Give recipient what sender offered
                    if my_offer["offer_type"] == "gold":
                        add_gold(recip, my_offer["offer_qty"])
                    else:
                        add_item(recip, my_offer["offer_item"], int(my_offer["offer_qty"]))

                    del trades[my_offer_id]
                    save_data(data)

                await ctx.send(
                    f"✅ Trade complete!\n"
                    f"**{my_offer['from_name']}** and **{ctx.author.display_name}** "
                    f"successfully exchanged goods."
                )

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !decline ──────────────────────────────────────────────────────────────
    @commands.command(name="decline")
    async def decline(self, ctx):
        """Decline your pending incoming trade offer."""
        try:
            if not self.in_trade_channel(ctx):
                return

            async with data_lock:
                data   = load_data()
                clean_expired(data)
                trades = get_trades(data)

                my_offer    = None
                my_offer_id = None
                for oid, offer in trades.items():
                    if offer["to_uid"] == str(ctx.author.id):
                        my_offer    = offer
                        my_offer_id = oid
                        break

                if my_offer is None:
                    await ctx.send("📭 You have no pending trade offer.")
                    return

                # Refund sender
                sender = data["players"].get(my_offer["from_uid"])
                if sender:
                    if my_offer["offer_type"] == "gold":
                        add_gold(sender, my_offer["offer_qty"])
                    else:
                        add_item(sender, my_offer["offer_item"], int(my_offer["offer_qty"]))

                del trades[my_offer_id]
                save_data(data)

            await ctx.send(
                f"❌ **{ctx.author.display_name}** declined the trade from "
                f"**{my_offer['from_name']}**. Items returned."
            )

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !tradeoffer ───────────────────────────────────────────────────────────
    @commands.command(name="tradeoffer", aliases=["offers"])
    async def tradeoffer(self, ctx):
        """See your pending incoming trade offer."""
        try:
            if not self.in_trade_channel(ctx):
                return

            data = load_data()
            clean_expired(data)
            save_data(data)
            trades = get_trades(data)

            my_offer = None
            for offer in trades.values():
                if offer["to_uid"] == str(ctx.author.id):
                    my_offer = offer
                    break

            if my_offer is None:
                await ctx.send("📭 You have no pending trade offer.")
                return

            expires_in = int(my_offer["expires_at"] - time.time())
            await ctx.send(
                f"📬 **{my_offer['from_name']}** wants to trade {fmt_offer(my_offer)} with you.\n"
                f"Expires in {expires_in // 60}m {expires_in % 60}s.\n"
                f"Type `!accept` or `!decline`."
            )

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !canceltrade ──────────────────────────────────────────────────────────
    @commands.command(name="canceltrade")
    async def canceltrade(self, ctx):
        """Cancel your outgoing trade offer and get your items back."""
        try:
            if not self.in_trade_channel(ctx):
                return

            async with data_lock:
                data   = load_data()
                clean_expired(data)
                trades = get_trades(data)

                my_offer    = None
                my_offer_id = None
                for oid, offer in trades.items():
                    if offer["from_uid"] == str(ctx.author.id):
                        my_offer    = offer
                        my_offer_id = oid
                        break

                if my_offer is None:
                    await ctx.send("📭 You have no active outgoing trade offer.")
                    return

                sender = get_player(data, ctx.author)
                if my_offer["offer_type"] == "gold":
                    add_gold(sender, my_offer["offer_qty"])
                else:
                    add_item(sender, my_offer["offer_item"], int(my_offer["offer_qty"]))

                del trades[my_offer_id]
                save_data(data)

            await ctx.send(
                f"↩️ Trade cancelled. Your offered items have been returned."
            )

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")


async def setup(bot):
    await bot.add_cog(TradeCog(bot))
