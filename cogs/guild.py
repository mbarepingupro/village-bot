"""
cogs/guild.py — Guild contribution and upgrade system
=======================================================
Commands:
  !contribute <resource> <qty>  → donate resources to your guild's upgrade pool
  !guildstatus                  → show your guild's upgrade progress
  !guilds                       → show all guilds and their current upgrade tier
"""

import discord
from discord.ext import commands
from config import GUILDS, GUILD_UPGRADES, ITEMS
from cogs.data import (
    load_data, save_data, get_player,
    add_item, remove_item, data_lock, user_lock, is_super
)


def get_guild_data(data: dict, guild_key: str) -> dict:
    """Get or create shared guild state."""
    guilds = data.setdefault("guilds", {})
    if guild_key not in guilds:
        guilds[guild_key] = {
            "upgrade_tier": 0,        # current completed tier (0 = no upgrades)
            "pool":         {},        # resource_id -> qty donated toward next tier
            "effects":      [],        # list of active effect tags
        }
    return guilds[guild_key]


def check_and_unlock(guild_key: str, guild_state: dict) -> str | None:
    """
    Check if the pool meets the cost for the next upgrade tier.
    If yes, deduct resources, increment tier, add effect, return announcement.
    Returns None if not enough resources yet.
    """
    upgrades = GUILD_UPGRADES.get(guild_key, [])
    next_tier = guild_state["upgrade_tier"]

    if next_tier >= len(upgrades):
        return None   # already max tier

    upgrade = upgrades[next_tier]
    cost    = upgrade["cost"]
    pool    = guild_state["pool"]

    # Check if all costs are met
    for item_id, qty_needed in cost.items():
        if pool.get(item_id, 0) < qty_needed:
            return None

    # Deduct and unlock
    for item_id, qty_needed in cost.items():
        pool[item_id] -= qty_needed
        if pool[item_id] <= 0:
            del pool[item_id]

    guild_state["upgrade_tier"] += 1
    guild_state["effects"].append(upgrade["effect"])

    g = GUILDS[guild_key]
    return (
        f"🎉 **{g['emoji']} {g['display_name']}** just unlocked "
        f"**{upgrade['name']}**!\n"
        f"*{upgrade['description']}*\n"
        f"All {g['class_name']}s now benefit from this upgrade!"
    )


class GuildCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ── !guildstatus ──────────────────────────────────────────────────────────
    @commands.command(name="guildstatus", aliases=["gs"])
    async def guildstatus(self, ctx):
        """Show your guild's upgrade pool and progress."""
        try:
            data   = load_data()
            player = get_player(data, ctx.author)
            save_data(data)

            if not player["guild"]:
                await ctx.send("⚠️ You're not in a guild yet. Use `!join` first.")
                return

            guild_key   = player["guild"]
            g           = GUILDS[guild_key]
            guild_state = get_guild_data(data, guild_key)
            upgrades    = GUILD_UPGRADES.get(guild_key, [])
            tier        = guild_state["upgrade_tier"]
            pool        = guild_state["pool"]

            lines = [f"**{g['emoji']} {g['display_name']} — Guild Status**\n"]

            # Completed upgrades
            if tier > 0:
                lines.append("✅ **Completed upgrades:**")
                for i in range(tier):
                    lines.append(f"  • {upgrades[i]['name']}")
                lines.append("")

            # Current upgrade in progress
            if tier < len(upgrades):
                next_up = upgrades[tier]
                lines.append(f"🔨 **Next upgrade: {next_up['name']}**")
                lines.append(f"*{next_up['description']}*")
                lines.append("**Progress:**")
                for item_id, qty_needed in next_up["cost"].items():
                    item     = ITEMS.get(item_id, {"name": item_id, "emoji": "❓"})
                    donated  = pool.get(item_id, 0)
                    bar_fill = int((donated / qty_needed) * 10)
                    bar      = "█" * bar_fill + "░" * (10 - bar_fill)
                    lines.append(
                        f"  {item['emoji']} {item['name']}: `{bar}` {donated}/{qty_needed}"
                    )
                lines.append(f"\nUse `!contribute <resource> <qty>` to donate.")
            else:
                lines.append("🏆 **Max tier reached! All upgrades unlocked.**")

            await ctx.send("\n".join(lines))

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !contribute ───────────────────────────────────────────────────────────
    @commands.command(name="contribute", aliases=["donate"])
    async def contribute(self, ctx, item_name: str = None, qty: int = None, *, guild_name: str = None):
        """
        Donate resources to any guild's upgrade pool.
        Usage:
          !contribute                         → see all guilds and what they need
          !contribute fish 10                 → donate to YOUR guild
          !contribute fish 10 sea lion pit    → donate to a specific guild
        """
        try:
            if item_name is None:
                # Show all guilds and what they currently need
                data  = load_data()
                lines = ["**🔨 Guild Upgrade Needs — what each guild is working toward:**\n"]
                any_in_progress = False

                for key, g in GUILDS.items():
                    guild_state  = get_guild_data(data, key)
                    tier         = guild_state["upgrade_tier"]
                    upgrades     = GUILD_UPGRADES.get(key, [])

                    if tier >= len(upgrades):
                        lines.append(f"{g['emoji']} **{g['display_name']}** — 🏆 Max tier reached!")
                        continue

                    any_in_progress = True
                    next_up  = upgrades[tier]
                    pool     = guild_state["pool"]
                    cost_str = "  ".join(
                        f"{ITEMS.get(k, {}).get('emoji', '❓')} {pool.get(k, 0)}/{v} {ITEMS.get(k, {}).get('name', k)}"
                        for k, v in next_up["cost"].items()
                    )
                    lines.append(
                        f"{g['emoji']} **{g['display_name']}** — Tier {tier+1}: *{next_up['name']}*\n"
                        f"   Needs: {cost_str}"
                    )

                save_data(data)
                if any_in_progress:
                    lines.append("\nUse `!contribute <resource> <qty>` to donate to your guild")
                    lines.append("or `!contribute <resource> <qty> <guild name>` for any guild.")
                await ctx.send("\n".join(lines))
                return

            if user_lock(ctx.author.id, "contribute").locked():
                return

            async with user_lock(ctx.author.id, "contribute"):
                async with data_lock:
                    data   = load_data()
                    player = get_player(data, ctx.author)

                    if not player["guild"]:
                        await ctx.send("⚠️ Join a guild first with `!join`.")
                        return

                    # Determine target guild — player's own or specified
                    guild_key = player["guild"]
                    if guild_name:
                        for key, g_cfg in GUILDS.items():
                            if guild_name.lower() in [key.lower(), g_cfg["display_name"].lower()]:
                                guild_key = key
                                break
                        else:
                            await ctx.send(f"❌ Guild `{guild_name}` not found.")
                            return

                    g           = GUILDS[guild_key]
                    guild_state = get_guild_data(data, guild_key)
                    upgrades    = GUILD_UPGRADES.get(guild_key, [])
                    tier        = guild_state["upgrade_tier"]

                    if tier >= len(upgrades):
                        await ctx.send(f"🏆 **{g['display_name']}** is already at max tier!")
                        return

                    # Match item
                    matched_id = None
                    for item_id in ITEMS:
                        item = ITEMS[item_id]
                        if item_name.lower() in [item_id.lower(), item["name"].lower()]:
                            matched_id = item_id
                            break

                    if matched_id is None:
                        await ctx.send(f"❌ Unknown resource `{item_name}`.")
                        return

                    # Check it's needed for the current upgrade
                    next_up  = upgrades[tier]
                    cost     = next_up["cost"]
                    if matched_id not in cost:
                        needed = ", ".join(
                            f"{ITEMS[k]['emoji']} {ITEMS[k]['name']}"
                            for k in cost
                        )
                        await ctx.send(
                            f"❌ **{g['display_name']}** doesn't need `{item_name}` right now.\n"
                            f"Current upgrade needs: {needed}"
                        )
                        return

                    # Validate qty
                    if qty is None or qty <= 0:
                        await ctx.send("❌ Please provide a quantity greater than 0.")
                        return

                    in_bag = player["inventory"].get(matched_id, 0)
                    if in_bag == 0:
                        item_def = ITEMS[matched_id]
                        await ctx.send(
                            f"❌ You don't have any "
                            f"{item_def['emoji']} {item_def['name']} to donate."
                        )
                        return

                    # Clamp qty to what player has and what's still needed
                    still_needed = cost[matched_id] - guild_state["pool"].get(matched_id, 0)
                    qty = min(qty, in_bag, still_needed)

                    if qty <= 0:
                        await ctx.send(
                            f"✅ The pool already has enough "
                            f"{ITEMS[matched_id]['emoji']} {ITEMS[matched_id]['name']}!"
                        )
                        return

                    # Deduct from player using safe helper, add to pool
                    if not remove_item(player, matched_id, qty):
                        await ctx.send("❌ Inventory changed unexpectedly. Please try again.")
                        return

                    guild_state["pool"][matched_id] = (
                        guild_state["pool"].get(matched_id, 0) + qty
                    )

                    # Check for unlock
                    unlock_msg = check_and_unlock(guild_key, guild_state)
                    save_data(data)

                item_def = ITEMS[matched_id]
                msg = (
                    f"🤝 **{ctx.author.display_name}** donated "
                    f"**{qty}x {item_def['emoji']} {item_def['name']}** "
                    f"to **{g['display_name']}**!"
                )
                if unlock_msg:
                    msg += f"\n\n{unlock_msg}"

                await ctx.send(msg)

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !guilds ───────────────────────────────────────────────────────────────
    @commands.command(name="guilds")
    async def guilds_overview(self, ctx):
        """Show all guilds, their resources and special powers."""
        try:
            data = load_data()
            save_data(data)

            lines = ["**🏛️ All Guilds**\n"]
            for key, g in GUILDS.items():
                guild_state = get_guild_data(data, key)
                tier        = guild_state["upgrade_tier"]
                max_tier    = len(GUILD_UPGRADES.get(key, []))
                tier_str    = f"Tier {tier}/{max_tier}" if max_tier > 0 else "No upgrades"
                resources   = " ".join(
                    f"{ITEMS.get(r, {}).get('emoji', '❓')} {ITEMS.get(r, {}).get('name', r)}"
                    for r in g.get("resources", [])
                )
                lines.append(
                    f"{g['emoji']} **{g['display_name']}** — *{g['class_name']}* — {tier_str}\n"
                    f"   Resources: {resources}\n"
                    f"   ✨ *{g['special']}*\n"
                )

            lines.append("Use `!upgrades <guild>` to see upgrade costs.")
            await ctx.send("\n".join(lines))

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── !upgrades ─────────────────────────────────────────────────────────────
    @commands.command(name="upgrades")
    async def upgrades(self, ctx, *, guild_name: str = None):
        """Show upgrade tiers and costs for a guild. Usage: !upgrades horny jail"""
        try:
            if guild_name is None:
                # Show all guilds with full upgrade detail — split into multiple messages if needed
                data = load_data()
                messages = []

                for key, g in GUILDS.items():
                    upgrades_list = GUILD_UPGRADES.get(key, [])
                    max_tier      = len(upgrades_list)
                    guild_state   = get_guild_data(data, key)
                    current_tier  = guild_state["upgrade_tier"]
                    pool          = guild_state["pool"]

                    lines = [f"{g['emoji']} **{g['display_name']}** — Tier {current_tier}/{max_tier}\n"]

                    for i, upgrade in enumerate(upgrades_list):
                        if i < current_tier:
                            status = "✅"
                        elif i == current_tier:
                            status = "🔨"
                        else:
                            status = "🔒"

                        cost_str = "  ".join(
                            f"{ITEMS.get(k, {}).get('emoji', '❓')} {qty}x {ITEMS.get(k, {}).get('name', k)}"
                            for k, qty in upgrade["cost"].items()
                        )
                        lines.append(f"   {status} **Tier {i+1}: {upgrade['name']}**")
                        lines.append(f"   *{upgrade['description']}*")
                        lines.append(f"   Cost: {cost_str}")

                        # Show progress bar for current tier
                        if i == current_tier:
                            for item_id, qty_needed in upgrade["cost"].items():
                                item     = ITEMS.get(item_id, {"name": item_id, "emoji": "❓"})
                                donated  = pool.get(item_id, 0)
                                bar_fill = int((donated / qty_needed) * 10)
                                bar      = "█" * bar_fill + "░" * (10 - bar_fill)
                                lines.append(f"   {item['emoji']} `{bar}` {donated}/{qty_needed}")
                        lines.append("")

                    messages.append("\n".join(lines))

                save_data(data)

                # Send each guild as a separate message to avoid Discord 2000 char limit
                await ctx.send("**🔨 Guild Upgrade Board**\n")
                for msg in messages:
                    await ctx.send(msg)
                return

            # Match guild
            matched_key = None
            for key, g in GUILDS.items():
                if guild_name.lower() in [key.lower(), g["display_name"].lower()]:
                    matched_key = key
                    break

            if matched_key is None:
                await ctx.send(f"❌ Guild `{guild_name}` not found. Type `!upgrades` to see the list.")
                return

            data        = load_data()
            g           = GUILDS[matched_key]
            guild_state = get_guild_data(data, matched_key)
            upgrades    = GUILD_UPGRADES.get(matched_key, [])
            current_tier = guild_state["upgrade_tier"]
            save_data(data)

            if not upgrades:
                await ctx.send(f"**{g['display_name']}** has no upgrades yet.")
                return

            lines = [f"**{g['emoji']} {g['display_name']} — Upgrade Tree**\n"]
            for i, upgrade in enumerate(upgrades):
                tier_num = i + 1
                if i < current_tier:
                    status = "✅ Unlocked"
                elif i == current_tier:
                    status = "🔨 **In progress**"
                else:
                    status = "🔒 Locked"

                cost_str = "  ".join(
                    f"{ITEMS.get(k, {}).get('emoji', '❓')} {qty}x {ITEMS.get(k, {}).get('name', k)}"
                    for k, qty in upgrade["cost"].items()
                )
                lines.append(
                    f"**Tier {tier_num} — {upgrade['name']}** {status}\n"
                    f"   *{upgrade['description']}*\n"
                    f"   Cost: {cost_str}\n"
                )

                # Show pool progress if this is the current tier
                if i == current_tier:
                    pool = guild_state["pool"]
                    lines.append("   **Progress:**")
                    for item_id, qty_needed in upgrade["cost"].items():
                        item     = ITEMS.get(item_id, {"name": item_id, "emoji": "❓"})
                        donated  = pool.get(item_id, 0)
                        bar_fill = int((donated / qty_needed) * 10)
                        bar      = "█" * bar_fill + "░" * (10 - bar_fill)
                        lines.append(
                            f"   {item['emoji']} {item['name']}: `{bar}` {donated}/{qty_needed}"
                        )
                    lines.append("")

            await ctx.send("\n".join(lines))

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")


async def setup(bot):
    await bot.add_cog(GuildCog(bot))
