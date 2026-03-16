"""
cogs/trade.py — Player-to-player resource trading
====================================================
Commands:
  !trade @user <resource> <qty>   → offer a trade
  !tradeoffer                     → see your pending incoming offers
  !accept <offer_id>              → accept an offer
  !decline <offer_id>             → decline an offer
  !canceltrade                    → cancel your outgoing offer

Rules:
- One active outgoing offer per player at a time
- Offer expires after 5 minutes
- Only resources (type: "resource") can be traded
- Both players must be in a guild
"""

import time
import uuid
import discord
from discord.ext import commands
from config import ITEMS
from cogs.data import (
    load_data, save_data, get_player,
    add_item, remove_item, data_lock, user_lock
)

TRADE_EXPIRY_SECONDS = 300   # 5 minutes


def get_trades(data: dict) -> dict:
    """Get or create the trades store."""
    return data.setdefault("trades", {})


def expired(offer: dict) -> bool:
    return time.time() > offer["expires_at"]


def clean_expired(data: dict):
    """Remove expired offers and refund items to senders."""
    trades = get_trades(data)
    to_delete = []
    for offer_id, offer in trades.items():
        if expired(offer):
            # Refund to sender
            sender_uid = offer["from_uid"]
            if sender_uid in data["players"]:
                add_item(data["players"][sender_uid], offer["item_id"], offer["qty"])
            to_delete.append(offer_id)
    for offer_id in to_delete:
        del trades[offer_id]


class TradeCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ── !trade ────────────────────────────────────────────────────────────────
    @commands.command(name="trade")
    async def trade(self, ctx, target: discord.Member = None, item_name: str = None, qty: int = None):
        """Offer a resource trade. Usage: !trade @user fish 10"""
        try:
            if target is None or item_name is None or qty is None:
                await ctx.send(
                    "Usage: `!trade @user <item> <qty>`\n"
                    "Example: `!trade @Sofya fish 10` or `!trade @Sofya mystery potion 1`\n"
                    "Any item marked as tradeable can be traded."
                )
                return

            if target.id == ctx.author.id:
                await ctx.send("❌ You can't trade with yourself.")
                return

            if qty <= 0:
                await ctx.send("❌ Quantity must be greater than 0.")
                return

            async with user_lock(ctx.author.id, "trade"):
                async with data_lock:
                    data   = load_data()
                    sender = get_player(data, ctx.author)
                    recip  = get_player(data, target)

                    clean_expired(data)

                    # Must both be in guilds
                    if not sender["guild"]:
                        await ctx.send("⚠️ You need to join a guild before trading.")
                        return
                    if not recip["guild"]:
                        await ctx.send(f"⚠️ {target.display_name} needs to join a guild before they can receive trades.")
                        return

                    # Match item — any item with tradeable: True
                    matched_id = None
                    for item_id, item_def in ITEMS.items():
                        if (item_def.get("tradeable", False) and
                                item_name.lower() in [item_id.lower(), item_def["name"].lower()]):
                            matched_id = item_id
                            break

                    if matched_id is None:
                        await ctx.send(f"❌ `{item_name}` is not tradeable or doesn't exist.")
                        return

                    # Check sender has enough
                    in_bag = sender["inventory"].get(matched_id, 0)
                    if in_bag < qty:
                        item_def = ITEMS[matched_id]
                        await ctx.send(
                            f"❌ You only have **{in_bag}x {item_def['emoji']} {item_def['name']}**."
                        )
                        return

                    # Check sender doesn't already have an active outgoing offer
                    trades = get_trades(data)
                    existing = [o for o in trades.values() if o["from_uid"] == str(ctx.author.id)]
                    if existing:
                        await ctx.send(
                            "❌ You already have a pending trade offer. "
                            "Use `!canceltrade` to cancel it first."
                        )
                        return

                    # Deduct from sender immediately (held in escrow)
                    remove_item(sender, matched_id, qty)

                    # Create offer
                    offer_id = str(uuid.uuid4())[:8].upper()
                    trades[offer_id] = {
                        "from_uid":   str(ctx.author.id),
                        "from_name":  ctx.author.display_name,
                        "to_uid":     str(target.id),
                        "to_name":    target.display_name,
                        "item_id":    matched_id,
                        "qty":        qty,
                        "expires_at": time.time() + TRADE_EXPIRY_SECONDS,
                    }
                    save_data(data)

                item_def = ITEMS[matched_id]
                await ctx.send(
                    f"🤝 **{ctx.author.display_name}** offered **{qty}x {item_def['emoji']} {item_def['name']}** "
                    f"to **{target.display_name}**!\n"
                    f"Offer ID: `{offer_id}` — expires in 5 minutes.\n"
                    f"{target.mention} type `!accept {offer_id}` or `!decline {offer_id}`"
                )

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !tradeoffer ───────────────────────────────────────────────────────────
    @commands.command(name="tradeoffer", aliases=["offers"])
    async def tradeoffer(self, ctx):
        """See pending trade offers sent to you."""
        try:
            data = load_data()
            clean_expired(data)
            save_data(data)

            trades = get_trades(data)
            incoming = [
                (oid, o) for oid, o in trades.items()
                if o["to_uid"] == str(ctx.author.id)
            ]

            if not incoming:
                await ctx.send("📭 You have no pending trade offers.")
                return

            lines = ["**📬 Incoming Trade Offers:**\n"]
            for offer_id, offer in incoming:
                item_def = ITEMS.get(offer["item_id"], {"name": offer["item_id"], "emoji": "❓"})
                expires_in = int(offer["expires_at"] - time.time())
                lines.append(
                    f"`{offer_id}` — **{offer['from_name']}** offers "
                    f"**{offer['qty']}x {item_def['emoji']} {item_def['name']}** "
                    f"(expires in {expires_in // 60}m {expires_in % 60}s)\n"
                    f"  → `!accept {offer_id}` or `!decline {offer_id}`"
                )
            await ctx.send("\n".join(lines))

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !accept ───────────────────────────────────────────────────────────────
    @commands.command(name="accept")
    async def accept(self, ctx, offer_id: str = None):
        """Accept a trade offer. Usage: !accept <offer_id>"""
        try:
            if offer_id is None:
                await ctx.send("Usage: `!accept <offer_id>`")
                return

            offer_id = offer_id.upper()

            async with user_lock(ctx.author.id, "accept"):
                async with data_lock:
                    data   = load_data()
                    clean_expired(data)
                    trades = get_trades(data)

                    if offer_id not in trades:
                        await ctx.send(f"❌ Offer `{offer_id}` not found or has expired.")
                        return

                    offer = trades[offer_id]

                    if offer["to_uid"] != str(ctx.author.id):
                        await ctx.send("❌ That offer wasn't sent to you.")
                        return

                    # Give item to recipient
                    recip = get_player(data, ctx.author)
                    add_item(recip, offer["item_id"], offer["qty"])

                    del trades[offer_id]
                    save_data(data)

                item_def = ITEMS.get(offer["item_id"], {"name": offer["item_id"], "emoji": "❓"})
                await ctx.send(
                    f"✅ **{ctx.author.display_name}** accepted the trade!\n"
                    f"Received **{offer['qty']}x {item_def['emoji']} {item_def['name']}** "
                    f"from **{offer['from_name']}**."
                )

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !decline ──────────────────────────────────────────────────────────────
    @commands.command(name="decline")
    async def decline(self, ctx, offer_id: str = None):
        """Decline a trade offer. Usage: !decline <offer_id>"""
        try:
            if offer_id is None:
                await ctx.send("Usage: `!decline <offer_id>`")
                return

            offer_id = offer_id.upper()

            async with data_lock:
                data   = load_data()
                clean_expired(data)
                trades = get_trades(data)

                if offer_id not in trades:
                    await ctx.send(f"❌ Offer `{offer_id}` not found or has expired.")
                    return

                offer = trades[offer_id]

                if offer["to_uid"] != str(ctx.author.id):
                    await ctx.send("❌ That offer wasn't sent to you.")
                    return

                # Refund to sender
                sender_uid = offer["from_uid"]
                if sender_uid in data["players"]:
                    add_item(data["players"][sender_uid], offer["item_id"], offer["qty"])

                del trades[offer_id]
                save_data(data)

            item_def = ITEMS.get(offer["item_id"], {"name": offer["item_id"], "emoji": "❓"})
            await ctx.send(
                f"❌ **{ctx.author.display_name}** declined the trade.\n"
                f"**{offer['qty']}x {item_def['emoji']} {item_def['name']}** "
                f"returned to **{offer['from_name']}**."
            )

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !canceltrade ──────────────────────────────────────────────────────────
    @commands.command(name="canceltrade")
    async def canceltrade(self, ctx):
        """Cancel your outgoing trade offer and get your items back."""
        try:
            async with data_lock:
                data   = load_data()
                clean_expired(data)
                trades = get_trades(data)

                my_offer = None
                my_offer_id = None
                for offer_id, offer in trades.items():
                    if offer["from_uid"] == str(ctx.author.id):
                        my_offer = offer
                        my_offer_id = offer_id
                        break

                if my_offer is None:
                    await ctx.send("📭 You have no active outgoing trade offer.")
                    return

                # Refund
                sender = get_player(data, ctx.author)
                add_item(sender, my_offer["item_id"], my_offer["qty"])
                del trades[my_offer_id]
                save_data(data)

            item_def = ITEMS.get(my_offer["item_id"], {"name": my_offer["item_id"], "emoji": "❓"})
            await ctx.send(
                f"↩️ Trade cancelled. **{my_offer['qty']}x {item_def['emoji']} {item_def['name']}** "
                f"returned to your inventory."
            )

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")


async def setup(bot):
    await bot.add_cog(TradeCog(bot))
