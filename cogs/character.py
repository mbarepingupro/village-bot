"""
cogs/character.py — Character commands
========================================
Commands: !join, !character, !inventory
"""

import time
import discord
from discord.ext import commands
from config import GUILDS, ITEMS, XP_PER_LEVEL
from cogs.data import load_data, save_data, get_player, fmt_time

GUILD_SWITCH_COOLDOWN = 60 * 60 * 24 * 7   # 7 days in seconds

class CharacterCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ── !join ─────────────────────────────────────────────────────────────────
    @commands.command(name="join")
    async def join(self, ctx, *, guild_name: str = None):
        """Join a guild and get your class. Usage: !join <guild name>"""
        data = load_data()
        player = get_player(data, ctx.author)

        # Show guild list if no argument
        if guild_name is None:
            lines = ["**🏛️ Available Guilds — type `!join <name>` to join one:**\n"]
            for key, g in GUILDS.items():
                lines.append(
                    f"{g['emoji']} **{g['display_name']}** → class: *{g['class_name']}*\n"
                    f"   {g['description']}\n"
                    f"   ✨ *{g['special']}*\n"
                )
            await ctx.send("\n".join(lines))
            return

        # Match guild by display_name or key (case insensitive)
        matched_key = None
        for key, g in GUILDS.items():
            if (guild_name.lower() == key.lower() or
                    guild_name.lower() == g["display_name"].lower()):
                matched_key = key
                break

        if matched_key is None:
            await ctx.send(
                f"❌ Guild `{guild_name}` not found. Type `!join` to see the list."
            )
            return

        # Cooldown on switching
        if player["guild"] is not None:
            last_join = player["cooldowns"].get("guild_switch", 0)
            remaining = GUILD_SWITCH_COOLDOWN - (time.time() - last_join)
            if remaining > 0:
                days = int(remaining // 86400)
                hrs  = int((remaining % 86400) // 3600)
                await ctx.send(
                    f"⏳ You can switch guilds again in **{days}d {hrs}h**."
                )
                return

        g = GUILDS[matched_key]
        player["guild"]  = matched_key
        player["class"]  = g["class_name"]
        player["cooldowns"]["guild_switch"] = time.time()
        save_data(data)

        await ctx.send(
            f"{g['emoji']} **{ctx.author.display_name}** has joined **{g['display_name']}** "
            f"and is now a **{g['class_name']}**!\n"
            f"✨ Class perk: *{g['special']}*"
        )

    #test command
    @commands.command(name="test123")
    async def test123(self, ctx):
        await ctx.send("character cog is working!")

    # ── !character ────────────────────────────────────────────────────────────
    @commands.command(name="profile", aliases=["stats", "mychar"])
    async def character(self, ctx, member: discord.Member = None):
        try:
            """Show your character sheet. Usage: !profile or !profile @user"""
            target = member or ctx.author
            data   = load_data()
            player = get_player(data, target)
    
            guild_info = "None — use `!join` to pick one"
            if player["guild"] and player["guild"] in GUILDS:
                g = GUILDS[player["guild"]]
                guild_info = f"{g['emoji']} {g['display_name']} ({player['class']})"
    
            xp_needed = player["level"] * XP_PER_LEVEL
            xp_bar_filled = int((player["xp"] / xp_needed) * 10)
            xp_bar = "█" * xp_bar_filled + "░" * (10 - xp_bar_filled)
    
            # Equipped cosmetics
            equipped = player.get("cosmetics", {})
            cosmetic_lines = []
            for slot, item_id in equipped.items():
                item = ITEMS.get(item_id, {})
                cosmetic_lines.append(f"  {item.get('emoji','?')} {item.get('name', item_id)} [{slot}]")
            cosmetics_str = "\n".join(cosmetic_lines) if cosmetic_lines else "  None equipped"
    
            embed = discord.Embed(
                title=f"📋 {target.display_name}",
                color=discord.Color.blurple()
            )
            embed.add_field(name="Guild / Class", value=guild_info, inline=False)
            embed.add_field(
                name=f"Level {player['level']}",
                value=f"`{xp_bar}` {player['xp']}/{xp_needed} XP",
                inline=False
            )
            embed.add_field(
                name="Stats",
                value=f"💰 Gold: {player['gold']}  |  🪓 Gathers: {player['stats']['total_gathers']}  |  🎁 Loots: {player['stats']['total_loots']}",
                inline=False
            )
            # Equipped tool
            tool_id = player.get("equipped_tool")
            if tool_id:
                from config import ITEMS as ALL_ITEMS
                t = ALL_ITEMS.get(tool_id, {"name": tool_id, "emoji": "🔧"})
                tool_str = f"{t['emoji']} {t['name']}"
            else:
                tool_str = "None — buy one with `!shop`"
            embed.add_field(name="Equipped Tool", value=tool_str, inline=False)
            embed.add_field(name="Equipped", value=cosmetics_str, inline=False)
            embed.set_footer(text="Use !inventory to see your items")
    
            await ctx.send(embed=embed)
            save_data(data)  # persist auto-created player record
            
        except:
             await ctx.send(f"Error: {e}")

    # ── !inventory ────────────────────────────────────────────────────────────
    @commands.command(name="inventory", aliases=["inv", "bag"])
    async def inventory(self, ctx):
        """Show your inventory."""
        data   = load_data()
        player = get_player(data, ctx.author)
        inv    = player["inventory"]

        if not inv:
            await ctx.send(
                f"🎒 **{ctx.author.display_name}'s** bag is empty. "
                f"Try `!gather` to collect some resources!"
            )
            return

        lines = [f"🎒 **{ctx.author.display_name}'s Inventory:**\n"]
        for item_id, qty in sorted(inv.items()):
            item = ITEMS.get(item_id, {"name": item_id, "emoji": "❓", "description": ""})
            lines.append(
                f"{item['emoji']} **{item['name']}** x{qty} — *{item['description']}*"
            )

        await ctx.send("\n".join(lines))
        save_data(data)

async def setup(bot):
    await bot.add_cog(CharacterCog(bot))
