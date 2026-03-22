"""
cogs/village.py — Community overview
======================================
Command: !village — see who's playing, what they're wearing, how active they are.
"""

import discord
from discord.ext import commands
from config import GUILDS, ITEMS
from cogs.data import load_data, save_data, get_player


class VillageCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="village", aliases=["town", "who"])
    async def village(self, ctx):
        """See all villagers — who's playing, their level, and what they're wearing."""
        try:
            data = load_data()
            save_data(data)

            players = data.get("players", {})
            if not players:
                await ctx.send(
                    "🏡 The village is empty! Be the first to join with `!join`."
                )
                return

            # Group players by guild
            guilded   = {}   # guild_key -> list of player dicts
            guildless = []

            for uid, p in players.items():
                guild_key = p.get("guild")
                if guild_key and guild_key in GUILDS:
                    guilded.setdefault(guild_key, []).append(p)
                else:
                    guildless.append(p)

            total = len(players)
            lines = [f"🏡 **Penguin Village** — {total} villager{'s' if total != 1 else ''}\n"]

            # Top streamers (by total_streams)
            top = sorted(
                players.values(),
                key=lambda p: p.get("stats", {}).get("total_streams", 0),
                reverse=True,
            )[:3]
            top_with_streams = [p for p in top if p.get("stats", {}).get("total_streams", 0) > 0]

            if top_with_streams:
                lines.append("🏆 **Most Active Streamgoers**")
                for p in top_with_streams:
                    streams = p.get("stats", {}).get("total_streams", 0)
                    tokens  = p.get("inventory", {}).get("loot_token", 0)
                    lines.append(
                        f"  {p['name']} — {streams} stream{'s' if streams != 1 else ''} attended, "
                        f"🎟️{tokens} tokens"
                    )
                lines.append("")

            # Each guild
            for guild_key, g in GUILDS.items():
                members = guilded.get(guild_key, [])
                if not members:
                    lines.append(f"{g['emoji']} **{g['display_name']}** — *empty*\n")
                    continue

                lines.append(f"{g['emoji']} **{g['display_name']}** ({len(members)} member{'s' if len(members) != 1 else ''})")
                # Sort by level descending
                members.sort(key=lambda p: p.get("level", 1), reverse=True)

                for p in members:
                    level  = p.get("level", 1)
                    tokens = p.get("inventory", {}).get("loot_token", 0)

                    # Equipped cosmetics
                    cosmetics = p.get("cosmetics", {})
                    if cosmetics:
                        cos_str = "  ".join(
                            f"{ITEMS.get(cid, {}).get('emoji', '✨')}"
                            for cid in cosmetics.values()
                            if cid in ITEMS
                        )
                    else:
                        cos_str = "—"

                    lines.append(
                        f"  {p['name']} [Lv.{level}] 🎟️{tokens} — {cos_str}"
                    )
                lines.append("")

            if guildless:
                lines.append(f"🏠 **No Guild** ({len(guildless)})")
                for p in guildless:
                    lines.append(f"  {p['name']} [Lv.{p.get('level', 1)}] — use `!join` to pick a guild")
                lines.append("")

            # Send in chunks if too long for Discord's 2000 char limit
            message = "\n".join(lines)
            if len(message) <= 2000:
                await ctx.send(message)
            else:
                # Split by guild sections
                chunk = ""
                for line in lines:
                    if len(chunk) + len(line) + 1 > 1900:
                        await ctx.send(chunk)
                        chunk = ""
                    chunk += line + "\n"
                if chunk:
                    await ctx.send(chunk)

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")


async def setup(bot):
    await bot.add_cog(VillageCog(bot))
