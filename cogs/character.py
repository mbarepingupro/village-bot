"""
cogs/character.py — Character commands
========================================
Commands: !join, !profile, !inventory

Guild switching resets daily at 00:00 Berlin time.
"""

import time
from datetime import datetime
import discord
from discord.ext import commands

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from config import GUILDS, ITEMS, XP_PER_LEVEL, DAILY_RESET_TZ
from cogs.data import load_data, save_data, get_player, fmt_time, fmt_gold, is_super


def next_reset_timestamp() -> float:
    """Return the Unix timestamp of the next 00:00 in Berlin time."""
    tz    = ZoneInfo(DAILY_RESET_TZ)
    now   = datetime.now(tz)
    reset = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # If we're past midnight already, next reset is tomorrow
    if now >= reset:
        from datetime import timedelta
        reset += timedelta(days=1)
    return reset.timestamp()


def can_switch_guild(player: dict) -> tuple[bool, str]:
    """
    Returns (True, "") if the player can switch guilds today,
    or (False, "time remaining message") if not.
    """
    last_switch = player["cooldowns"].get("guild_switch", 0)
    if last_switch == 0:
        return True, ""

    tz          = ZoneInfo(DAILY_RESET_TZ)
    last_dt     = datetime.fromtimestamp(last_switch, tz)
    now_dt      = datetime.now(tz)

    # Same calendar day in Berlin = can't switch yet
    if last_dt.date() == now_dt.date():
        next_reset = next_reset_timestamp()
        remaining  = int(next_reset - time.time())
        hrs        = remaining // 3600
        mins       = (remaining % 3600) // 60
        return False, f"**{hrs}h {mins}m** until daily reset"

    return True, ""


class CharacterCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ── !join ─────────────────────────────────────────────────────────────────
    @commands.command(name="join")
    async def join(self, ctx, *, guild_name: str = None):
        """Join a guild and get your class. Usage: !join <guild name>"""
        try:
            data   = load_data()
            player = get_player(data, ctx.author)

            if guild_name is None:
                lines = ["**🏛️ Available Guilds — type `!join <name>` to join:**\n"]
                for key, g in GUILDS.items():
                    resources = " ".join(
                        ITEMS.get(r, {}).get("emoji", "❓")
                        for r in g.get("resources", [])
                    )
                    lines.append(
                        f"{g['emoji']} **{g['display_name']}** → *{g['class_name']}* {resources}\n"
                        f"   {g['description']}\n"
                        f"   ✨ *{g['special']}*\n"
                    )
                await ctx.send("\n".join(lines))
                save_data(data)
                return

            # Match guild
            matched_key = None
            for key, g in GUILDS.items():
                if guild_name.lower() in [key.lower(), g["display_name"].lower()]:
                    matched_key = key
                    break

            if matched_key is None:
                await ctx.send(f"❌ Guild `{guild_name}` not found. Type `!join` to see the list.")
                return

            # Daily cooldown check
            if player["guild"] is not None and not is_super(ctx):
                can_switch, reason = can_switch_guild(player)
                if not can_switch:
                    await ctx.send(
                        f"⏳ You already switched guilds today. "
                        f"Come back in {reason}."
                    )
                    return

            g = GUILDS[matched_key]
            player["guild"] = matched_key
            player["class"] = g["class_name"]
            player["cooldowns"]["guild_switch"] = time.time()
            save_data(data)

            resources = " ".join(
                f"{ITEMS.get(r, {}).get('emoji', '❓')} {ITEMS.get(r, {}).get('name', r)}"
                for r in g.get("resources", [])
            )
            await ctx.send(
                f"{g['emoji']} **{ctx.author.display_name}** joined **{g['display_name']}** "
                f"and is now a **{g['class_name']}**!\n"
                f"You gather: {resources}\n"
                f"✨ *{g['special']}*"
            )

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !character ────────────────────────────────────────────────────────────
    @commands.command(name="character", aliases=["profile", "stats", "mychar"])
    async def character(self, ctx, member: discord.Member = None):
        """Show your character. Usage: !character or !character @user"""
        try:
            target = member or ctx.author
            data   = load_data()
            player = get_player(data, target)
            save_data(data)

            # ── Build penguin image with cosmetic layers ────────────────────
            import io, os
            from PIL import Image

            base_dir    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            base_path   = os.path.join(base_dir, "assets", "base_penguin.png")
            cos_dir     = os.path.join(base_dir, "assets", "cosmetics")

            img = Image.open(base_path).convert("RGBA")

            for slot in ["outfit", "hat", "accessory"]:
                item_id = player.get("cosmetics", {}).get(slot)
                if not item_id:
                    continue
                layer_path = os.path.join(cos_dir, f"{item_id}.png")
                if os.path.exists(layer_path):
                    layer = Image.open(layer_path).convert("RGBA")
                    layer = layer.resize(img.size, Image.NEAREST)
                    img.paste(layer, (0, 0), layer)

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            await ctx.send(file=discord.File(buf, filename="character.png"))

            # ── Text stats ─────────────────────────────────────────────────
            guild_info = "None — use `!join` to pick one"
            if player["guild"] and player["guild"] in GUILDS:
                g          = GUILDS[player["guild"]]
                guild_info = f"{g['emoji']} {g['display_name']} ({player['class']})"

            xp_needed     = player["level"] * XP_PER_LEVEL
            xp_bar_filled = int((player["xp"] / xp_needed) * 10)
            xp_bar        = "█" * xp_bar_filled + "░" * (10 - xp_bar_filled)

            tool_id  = player.get("equipped_tool")
            tool_str = ITEMS[tool_id]["name"] if tool_id and tool_id in ITEMS else "None"

            cosmetics = player.get("cosmetics", {})
            cosmetic_lines = "  ".join(
                f"{ITEMS.get(item_id, {}).get('emoji', '✨')} {ITEMS.get(item_id, {}).get('name', item_id)}"
                for item_id in cosmetics.values()
            ) if cosmetics else "None"

            await ctx.send(
                f"**{target.display_name}**\n"
                f"Guild: {guild_info}\n"
                f"Level {player['level']} — `{xp_bar}` {player['xp']}/{xp_needed} XP\n"
                f"💰 Gold: {fmt_gold(player['gold'])}g\n"
                f"🔨 Gathers: {player['stats']['total_gathers']} | 🎁 Loots: {player['stats']['total_loots']}\n"
                f"⚒️ Tool: {tool_str}\n"
                f"🎭 Cosmetics: {cosmetic_lines}"
            )

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !inventory ────────────────────────────────────────────────────────────
    @commands.command(name="inventory", aliases=["inv", "bag"])
    async def inventory(self, ctx):
        """Show your inventory."""
        try:
            data   = load_data()
            player = get_player(data, ctx.author)
            inv    = player["inventory"]

            if not inv:
                await ctx.send(
                    f"🎒 **{ctx.author.display_name}'s** bag is empty. "
                    f"Use `!gather` to collect resources!"
                )
                save_data(data)
                return

            lines = [f"🎒 **{ctx.author.display_name}'s Inventory:**\n"]
            for item_id, qty in sorted(inv.items()):
                item = ITEMS.get(item_id, {"name": item_id, "emoji": "❓", "description": ""})
                lines.append(
                    f"{item['emoji']} **{item['name']}** x{qty} — *{item['description']}*"
                )

            await ctx.send("\n".join(lines))
            save_data(data)

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")


async def setup(bot):
    await bot.add_cog(CharacterCog(bot))
