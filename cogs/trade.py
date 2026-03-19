"""
cogs/trade.py — Player-to-player trading + open market
========================================================
All commands work in the trade channel only.

Direct trades (person to person):
  !trade 3 fish @user              → gift
  !trade 3 fish @user for 3 herb   → exchange offer
  !trade 5g @user                  → send gold
  !trade 5g @user for 3 fish       → gold for resources
  !accept                          → accept your one incoming offer
  !decline                         → decline your one incoming offer
  !canceltrade                     → cancel your outgoing offer

Open market (no target needed):
  !offer 1 crystal potion for 1g   → post a public listing
  !offer 3 fish for 2 herb         → post a resource swap listing
  !market                          → browse all active listings
  !buy A3K                         → claim a listing by its 3-char code
  !unoffer                         → cancel your own listing
"""

import time
import random
import string
import discord
from discord.ext import commands
from config import ITEMS, TRADE_CHANNEL
from cogs.data import (
    load_data, save_data, get_player,
    add_item, remove_item, add_gold, spend_gold,
    data_lock, user_lock, fmt_gold
)

TRADE_EXPIRY  = 300    # 5 min for direct trades
OFFER_EXPIRY  = 86400  # 24 hours for open listings


def get_trades(data: dict) -> dict:
    return data.setdefault("trades", {})

def get_listings(data: dict) -> dict:
    return data.setdefault("listings", {})

def expired(offer: dict, expiry: int) -> bool:
    return time.time() > offer["expires_at"]

def clean_expired(data: dict):
    # Clean direct trades
    trades    = get_trades(data)
    to_delete = []
    for oid, offer in trades.items():
        if time.time() > offer["expires_at"]:
            uid = offer["from_uid"]
            if uid in data["players"]:
                p = data["players"][uid]
                if offer["offer_type"] == "gold":
                    add_gold(p, offer["offer_qty"])
                else:
                    add_item(p, offer["offer_item"], int(offer["offer_qty"]))
            to_delete.append(oid)
    for oid in to_delete:
        del trades[oid]

    # Clean expired listings (refund)
    listings  = get_listings(data)
    to_delete = []
    for code, listing in listings.items():
        if time.time() > listing["expires_at"]:
            uid = listing["from_uid"]
            if uid in data["players"]:
                p = data["players"][uid]
                if listing["offer_type"] == "gold":
                    add_gold(p, listing["offer_qty"])
                else:
                    add_item(p, listing["offer_item"], int(listing["offer_qty"]))
            to_delete.append(code)
    for code in to_delete:
        del listings[code]

def gen_code(existing: set) -> str:
    """Generate a unique 3-char alphanumeric code."""
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choices(chars, k=3))
        if code not in existing:
            return code

def parse_item_token(token: str):
    """Match a token to item_id or gold. Returns (item_id, is_gold) or (None, False)."""
    token = token.lower().strip()
    if token in ("g", "gold"):
        return ("gold", True)
    for item_id, item_def in ITEMS.items():
        aliases = [
            item_id.lower(),
            item_def["name"].lower(),
            item_def["name"].lower().split()[0],
        ]
        if token in aliases:
            return (item_id, False)
    return (None, False)

def fmt_side(item_id, qty, is_gold) -> str:
    if is_gold:
        return f"**{fmt_gold(qty)}g**"
    item = ITEMS.get(item_id, {"name": item_id, "emoji": "❓"})
    return f"**{int(qty)}x {item['emoji']} {item['name']}**"

def parse_trade_args(args: str, mentions: list):
    """
    Parse trade args. Returns dict with keys:
      target, offer_item, offer_qty, offer_is_gold,
      want_item, want_qty, want_is_gold, error
    """
    result = {
        "target": None, "offer_item": None, "offer_qty": 0,
        "offer_is_gold": False, "want_item": None,
        "want_qty": 0, "want_is_gold": False, "error": None
    }

    # Split on "for"
    parts     = args.lower().split(" for ", 1)
    offer_str = parts[0].strip()
    want_str  = parts[1].strip() if len(parts) > 1 else None

    # Extract mention from offer_str
    if mentions:
        result["target"] = mentions[0]
        for placeholder in [f"<@{mentions[0].id}>", f"<@!{mentions[0].id}>"]:
            offer_str = offer_str.replace(placeholder.lower(), "").strip()
            offer_str = offer_str.replace(placeholder, "").strip()

    # Parse offer qty + item
    tokens = offer_str.split()
    if not tokens:
        result["error"] = "Couldn't parse offer amount."
        return result

    raw = tokens[0]
    try:
        if raw.endswith("g"):
            result["offer_qty"]     = float(raw[:-1])
            result["offer_item"]    = "gold"
            result["offer_is_gold"] = True
        else:
            result["offer_qty"] = int(raw)
            item_token = " ".join(tokens[1:]).strip()
            item_id, is_gold    = parse_item_token(item_token)
            result["offer_item"]    = item_id
            result["offer_is_gold"] = is_gold
    except ValueError:
        result["error"] = "Invalid quantity."
        return result

    if result["offer_item"] is None:
        result["error"] = "Couldn't find that item."
        return result

    if result["offer_qty"] <= 0:
        result["error"] = "Quantity must be greater than 0."
        return result

    # Parse want side (optional)
    if want_str:
        wtokens = want_str.split()
        try:
            if wtokens[0].endswith("g"):
                result["want_qty"]     = float(wtokens[0][:-1])
                result["want_item"]    = "gold"
                result["want_is_gold"] = True
            else:
                result["want_qty"] = int(wtokens[0])
                item_token = " ".join(wtokens[1:]).strip()
                item_id, is_gold    = parse_item_token(item_token)
                result["want_item"]    = item_id
                result["want_is_gold"] = is_gold
        except ValueError:
            result["error"] = "Invalid quantity in 'for' part."
            return result

        if result["want_item"] is None:
            result["error"] = "Couldn't find the item you want in exchange."
            return result
        if result["want_qty"] <= 0:
            result["error"] = "The quantity you want must be greater than 0."
            return result

    return result


class TradeCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def in_trade_channel(self, ctx) -> bool:
        if isinstance(ctx.channel, discord.DMChannel):
            return True
        return getattr(ctx.channel, 'name', '') == TRADE_CHANNEL

    async def send_trade_only(self, ctx):
        trade_ch = discord.utils.get(ctx.guild.text_channels, name=TRADE_CHANNEL)
        if trade_ch:
            await ctx.send(f"🤝 Trades happen in {trade_ch.mention}!")
        else:
            await ctx.send(f"🤝 Use the #{TRADE_CHANNEL} channel for trades!")

    # ── !trade ────────────────────────────────────────────────────────────────
    @commands.command(name="trade")
    async def trade(self, ctx, *, args: str = None):
        """
        Trade with a specific player.
        !trade 3 fish @user              → gift
        !trade 3 fish @user for 3 herb   → exchange
        !trade 5g @user                  → send gold
        """
        try:
            if not self.in_trade_channel(ctx):
                await self.send_trade_only(ctx)
                return

            if args is None:
                await ctx.send(
                    "**Direct trade usage:**\n"
                    "`!trade 3 fish @user` — gift\n"
                    "`!trade 3 fish @user for 3 herb` — exchange\n"
                    "`!trade 5g @user` — send gold\n\n"
                    "**Open market:**\n"
                    "`!offer 3 fish for 2g` — post a listing\n"
                    "`!market` — browse listings"
                )
                return

            parsed = parse_trade_args(args, ctx.message.mentions)
            if parsed["error"]:
                await ctx.send(f"❌ {parsed['error']}")
                return

            target = parsed["target"]
            if target is None:
                await ctx.send("❌ You need to @mention the person you're trading with.")
                return
            if target.id == ctx.author.id:
                await ctx.send("❌ You can't trade with yourself.")
                return

            async with user_lock(ctx.author.id, "trade"):
                async with data_lock:
                    data   = load_data()
                    sender = get_player(data, ctx.author)
                    recip  = get_player(data, target)
                    clean_expired(data)
                    trades = get_trades(data)

                    # Check no existing outgoing offer
                    if any(o["from_uid"] == str(ctx.author.id) for o in trades.values()):
                        await ctx.send("❌ You already have a pending offer. Use `!canceltrade` first.")
                        return

                    # Check recipient doesn't already have an incoming offer
                    if any(o["to_uid"] == str(target.id) for o in trades.values()):
                        await ctx.send(f"❌ **{target.display_name}** already has a pending offer.")
                        return

                    # Validate and escrow sender's offering
                    if parsed["offer_is_gold"]:
                        if round(sender.get("gold", 0), 1) < parsed["offer_qty"]:
                            await ctx.send(f"❌ You only have **{fmt_gold(sender['gold'])}g**.")
                            return
                        spend_gold(sender, parsed["offer_qty"])
                    else:
                        in_bag = sender["inventory"].get(parsed["offer_item"], 0)
                        if in_bag < parsed["offer_qty"]:
                            item = ITEMS.get(parsed["offer_item"], {"name": parsed["offer_item"], "emoji": "❓"})
                            await ctx.send(f"❌ You only have **{in_bag}x {item['emoji']} {item['name']}**.")
                            return
                        remove_item(sender, parsed["offer_item"], int(parsed["offer_qty"]))

                    # Gift — complete immediately
                    if parsed["want_item"] is None:
                        if parsed["offer_is_gold"]:
                            add_gold(recip, parsed["offer_qty"])
                            msg = f"🎁 **{ctx.author.display_name}** gifted **{fmt_gold(parsed['offer_qty'])}g** to **{target.display_name}**!"
                        else:
                            add_item(recip, parsed["offer_item"], int(parsed["offer_qty"]))
                            msg = f"🎁 **{ctx.author.display_name}** gifted {fmt_side(parsed['offer_item'], parsed['offer_qty'], False)} to **{target.display_name}**!"
                        save_data(data)
                        await ctx.send(msg)
                        return

                    # Exchange — create pending offer
                    offer_id = f"{str(ctx.author.id)[-4:]}{str(target.id)[-4:]}"
                    trades[offer_id] = {
                        "from_uid":   str(ctx.author.id),
                        "from_name":  ctx.author.display_name,
                        "to_uid":     str(target.id),
                        "to_name":    target.display_name,
                        "offer_type": "gold" if parsed["offer_is_gold"] else "item",
                        "offer_item": parsed["offer_item"],
                        "offer_qty":  parsed["offer_qty"],
                        "want_type":  "gold" if parsed["want_is_gold"] else "item",
                        "want_item":  parsed["want_item"],
                        "want_qty":   parsed["want_qty"],
                        "expires_at": time.time() + TRADE_EXPIRY,
                    }
                    save_data(data)

            offer = trades[offer_id]
            giving  = fmt_side(offer["offer_item"], offer["offer_qty"], offer["offer_type"] == "gold")
            wanting = fmt_side(offer["want_item"],  offer["want_qty"],  offer["want_type"]  == "gold")
            await ctx.send(
                f"🤝 **{ctx.author.display_name}** offers {giving} to {target.mention} "
                f"in exchange for {wanting}\n"
                f"{target.mention} type `!accept` or `!decline` *(expires in 5 min)*"
            )

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !accept ───────────────────────────────────────────────────────────────
    @commands.command(name="accept")
    async def accept(self, ctx):
        """Accept your pending incoming trade offer."""
        try:
            if not self.in_trade_channel(ctx):
                await self.send_trade_only(ctx)
                return

            async with user_lock(ctx.author.id, "accept"):
                async with data_lock:
                    data = load_data()
                    clean_expired(data)
                    trades = get_trades(data)

                    my_offer = None
                    my_oid   = None
                    for oid, offer in trades.items():
                        if offer["to_uid"] == str(ctx.author.id):
                            my_offer = offer
                            my_oid   = oid
                            break

                    if my_offer is None:
                        await ctx.send("📭 You have no pending trade offer.")
                        return

                    recip  = get_player(data, ctx.author)
                    sender = data["players"].get(my_offer["from_uid"])

                    # Validate recipient has what sender wants
                    if my_offer["want_type"] == "gold":
                        if round(recip.get("gold", 0), 1) < my_offer["want_qty"]:
                            await ctx.send(f"❌ You need **{fmt_gold(my_offer['want_qty'])}g** but only have **{fmt_gold(recip['gold'])}g**.")
                            return
                        spend_gold(recip, my_offer["want_qty"])
                        if sender:
                            add_gold(sender, my_offer["want_qty"])
                    else:
                        want_id  = my_offer["want_item"]
                        want_qty = int(my_offer["want_qty"])
                        if recip["inventory"].get(want_id, 0) < want_qty:
                            item = ITEMS.get(want_id, {"name": want_id, "emoji": "❓"})
                            await ctx.send(f"❌ You need **{want_qty}x {item['emoji']} {item['name']}** but don't have enough.")
                            return
                        remove_item(recip, want_id, want_qty)
                        if sender:
                            add_item(sender, want_id, want_qty)

                    # Give recipient what sender offered
                    if my_offer["offer_type"] == "gold":
                        add_gold(recip, my_offer["offer_qty"])
                    else:
                        add_item(recip, my_offer["offer_item"], int(my_offer["offer_qty"]))

                    del trades[my_oid]
                    save_data(data)

            await ctx.send(
                f"✅ Trade complete! **{my_offer['from_name']}** and "
                f"**{ctx.author.display_name}** exchanged goods."
            )

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !decline ──────────────────────────────────────────────────────────────
    @commands.command(name="decline")
    async def decline(self, ctx):
        """Decline your pending incoming trade offer."""
        try:
            if not self.in_trade_channel(ctx):
                await self.send_trade_only(ctx)
                return

            async with data_lock:
                data = load_data()
                clean_expired(data)
                trades = get_trades(data)

                my_offer = None
                my_oid   = None
                for oid, offer in trades.items():
                    if offer["to_uid"] == str(ctx.author.id):
                        my_offer = offer
                        my_oid   = oid
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

                del trades[my_oid]
                save_data(data)

            await ctx.send(f"❌ **{ctx.author.display_name}** declined the trade. Items returned to **{my_offer['from_name']}**.")

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !canceltrade ──────────────────────────────────────────────────────────
    @commands.command(name="canceltrade")
    async def canceltrade(self, ctx):
        """Cancel your outgoing trade offer."""
        try:
            if not self.in_trade_channel(ctx):
                await self.send_trade_only(ctx)
                return

            async with data_lock:
                data = load_data()
                clean_expired(data)
                trades = get_trades(data)

                my_offer = None
                my_oid   = None
                for oid, offer in trades.items():
                    if offer["from_uid"] == str(ctx.author.id):
                        my_offer = offer
                        my_oid   = oid
                        break

                if my_offer is None:
                    await ctx.send("📭 You have no active outgoing offer.")
                    return

                sender = get_player(data, ctx.author)
                if my_offer["offer_type"] == "gold":
                    add_gold(sender, my_offer["offer_qty"])
                else:
                    add_item(sender, my_offer["offer_item"], int(my_offer["offer_qty"]))

                del trades[my_oid]
                save_data(data)

            await ctx.send("↩️ Trade cancelled. Your items have been returned.")

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !offer ────────────────────────────────────────────────────────────────
    @commands.command(name="offer")
    async def offer(self, ctx, *, args: str = None):
        """
        Post an open market listing (no target needed).
        !offer 1 crystal potion for 1g
        !offer 3 fish for 2 herb
        """
        try:
            if not self.in_trade_channel(ctx):
                await self.send_trade_only(ctx)
                return

            if args is None:
                await ctx.send(
                    "**Usage:** `!offer <qty> <item> for <qty> <item>`\n"
                    "Examples:\n"
                    "`!offer 1 crystal potion for 1g`\n"
                    "`!offer 3 fish for 2 herb`"
                )
                return

            parsed = parse_trade_args(args, [])
            if parsed["error"]:
                await ctx.send(f"❌ {parsed['error']}")
                return

            if parsed["want_item"] is None:
                await ctx.send("❌ Open listings must specify what you want in return. Example: `!offer 3 fish for 2g`")
                return

            async with user_lock(ctx.author.id, "offer"):
                async with data_lock:
                    data   = load_data()
                    sender = get_player(data, ctx.author)
                    clean_expired(data)
                    listings = get_listings(data)

                    # One active listing per player
                    if any(l["from_uid"] == str(ctx.author.id) for l in listings.values()):
                        await ctx.send("❌ You already have an active listing. Use `!unoffer` to cancel it first.")
                        return

                    # Validate and escrow
                    if parsed["offer_is_gold"]:
                        if round(sender.get("gold", 0), 1) < parsed["offer_qty"]:
                            await ctx.send(f"❌ You only have **{fmt_gold(sender['gold'])}g**.")
                            return
                        spend_gold(sender, parsed["offer_qty"])
                    else:
                        in_bag = sender["inventory"].get(parsed["offer_item"], 0)
                        if in_bag < parsed["offer_qty"]:
                            item = ITEMS.get(parsed["offer_item"], {"name": parsed["offer_item"], "emoji": "❓"})
                            await ctx.send(f"❌ You only have **{in_bag}x {item['emoji']} {item['name']}**.")
                            return
                        remove_item(sender, parsed["offer_item"], int(parsed["offer_qty"]))

                    code = gen_code(set(listings.keys()))
                    listings[code] = {
                        "from_uid":   str(ctx.author.id),
                        "from_name":  ctx.author.display_name,
                        "offer_type": "gold" if parsed["offer_is_gold"] else "item",
                        "offer_item": parsed["offer_item"],
                        "offer_qty":  parsed["offer_qty"],
                        "want_type":  "gold" if parsed["want_is_gold"] else "item",
                        "want_item":  parsed["want_item"],
                        "want_qty":   parsed["want_qty"],
                        "expires_at": time.time() + OFFER_EXPIRY,
                    }
                    save_data(data)

            listing = listings[code]
            giving  = fmt_side(listing["offer_item"], listing["offer_qty"], listing["offer_type"] == "gold")
            wanting = fmt_side(listing["want_item"],  listing["want_qty"],  listing["want_type"]  == "gold")
            await ctx.send(
                f"📋 **{ctx.author.display_name}** offers {giving} for {wanting}\n"
                f"Claim with: `!buy {code}` *(listing expires in 24h)*"
            )

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !market ───────────────────────────────────────────────────────────────
    @commands.command(name="market")
    async def market(self, ctx):
        """Browse all open market listings."""
        try:
            if not self.in_trade_channel(ctx):
                await self.send_trade_only(ctx)
                return

            async with data_lock:
                data = load_data()
                clean_expired(data)
                save_data(data)
                listings = get_listings(data)

            if not listings:
                await ctx.send("📭 No active listings right now. Post one with `!offer`!")
                return

            lines = ["**🏪 Open Market Listings**\n"]
            for code, listing in listings.items():
                giving  = fmt_side(listing["offer_item"], listing["offer_qty"], listing["offer_type"] == "gold")
                wanting = fmt_side(listing["want_item"],  listing["want_qty"],  listing["want_type"]  == "gold")
                expires_in = int(listing["expires_at"] - time.time())
                hours = expires_in // 3600
                lines.append(
                    f"`{code}` — **{listing['from_name']}** offers {giving} for {wanting} "
                    f"*(expires in {hours}h)* — `!buy {code}`"
                )

            await ctx.send("\n".join(lines))

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !buy <code> ───────────────────────────────────────────────────────────
    @commands.command(name="buy")
    async def buy_listing(self, ctx, code: str = None):
        """Claim an open market listing. Usage: !buy A3K"""
        try:
            if not self.in_trade_channel(ctx):
                await self.send_trade_only(ctx)
                return

            if code is None:
                await ctx.send("Usage: `!buy <code>` — find codes with `!market`")
                return

            code = code.upper()

            async with user_lock(ctx.author.id, "buy_listing"):
                async with data_lock:
                    data = load_data()
                    clean_expired(data)
                    listings = get_listings(data)

                    if code not in listings:
                        await ctx.send(f"❌ Listing `{code}` not found or has expired.")
                        return

                    listing = listings[code]

                    if listing["from_uid"] == str(ctx.author.id):
                        await ctx.send("❌ You can't buy your own listing. Use `!unoffer` to cancel it.")
                        return

                    buyer  = get_player(data, ctx.author)
                    seller = data["players"].get(listing["from_uid"])

                    # Buyer must provide what seller wants
                    if listing["want_type"] == "gold":
                        if round(buyer.get("gold", 0), 1) < listing["want_qty"]:
                            await ctx.send(f"❌ You need **{fmt_gold(listing['want_qty'])}g** but only have **{fmt_gold(buyer['gold'])}g**.")
                            return
                        spend_gold(buyer, listing["want_qty"])
                        if seller:
                            add_gold(seller, listing["want_qty"])
                    else:
                        want_id  = listing["want_item"]
                        want_qty = int(listing["want_qty"])
                        if buyer["inventory"].get(want_id, 0) < want_qty:
                            item = ITEMS.get(want_id, {"name": want_id, "emoji": "❓"})
                            await ctx.send(f"❌ You need **{want_qty}x {item['emoji']} {item['name']}** but don't have enough.")
                            return
                        remove_item(buyer, want_id, want_qty)
                        if seller:
                            add_item(seller, want_id, want_qty)

                    # Give buyer what seller offered
                    if listing["offer_type"] == "gold":
                        add_gold(buyer, listing["offer_qty"])
                    else:
                        add_item(buyer, listing["offer_item"], int(listing["offer_qty"]))

                    del listings[code]
                    save_data(data)

            giving  = fmt_side(listing["offer_item"], listing["offer_qty"], listing["offer_type"] == "gold")
            wanting = fmt_side(listing["want_item"],  listing["want_qty"],  listing["want_type"]  == "gold")
            await ctx.send(
                f"✅ **{ctx.author.display_name}** claimed listing `{code}`!\n"
                f"Received {giving} from **{listing['from_name']}** in exchange for {wanting}."
            )

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !unoffer ──────────────────────────────────────────────────────────────
    @commands.command(name="unoffer")
    async def unoffer(self, ctx):
        """Cancel your open market listing and get your items back."""
        try:
            if not self.in_trade_channel(ctx):
                await self.send_trade_only(ctx)
                return

            async with data_lock:
                data = load_data()
                clean_expired(data)
                listings = get_listings(data)

                my_listing = None
                my_code    = None
                for code, listing in listings.items():
                    if listing["from_uid"] == str(ctx.author.id):
                        my_listing = listing
                        my_code    = code
                        break

                if my_listing is None:
                    await ctx.send("📭 You have no active market listing.")
                    return

                # Refund
                sender = get_player(data, ctx.author)
                if my_listing["offer_type"] == "gold":
                    add_gold(sender, my_listing["offer_qty"])
                else:
                    add_item(sender, my_listing["offer_item"], int(my_listing["offer_qty"]))

                del listings[my_code]
                save_data(data)

            await ctx.send("↩️ Listing cancelled. Your items have been returned.")

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")


async def setup(bot):
    await bot.add_cog(TradeCog(bot))
