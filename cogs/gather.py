"""
cogs/gather.py — Gathering
============================
Command: !gather

Each guild gathers its own 2 resources.
Class gimmicks are always active (no upgrade system).
"""

import random
import discord
from discord.ext import commands
from config import GUILDS, ITEMS, BASE_GATHER, COOLDOWNS, XP_PER_GATHER, XP_PER_LEVEL, LEVEL_GATHER_BONUS
from cogs.data import (
    load_data, save_data, get_player,
    add_item, cooldown_remaining, set_cooldown,
    add_xp, fmt_time, data_lock, user_lock, is_super
)


class GatherCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="gather")
    async def gather(self, ctx):
        """Gather your guild's resources."""
        try:
            if user_lock(ctx.author.id, "gather").locked():
                return

            async with user_lock(ctx.author.id, "gather"):
                async with data_lock:
                    data   = load_data()
                    player = get_player(data, ctx.author)

                    if player["guild"] is None:
                        await ctx.send(f"⚠️ {ctx.author.mention} Join a guild first with `!join`.")
                        return

                    guild_key = player["guild"]
                    guild_cfg = GUILDS[guild_key]

                    # ── Cooldown check ────────────────────────────────────────
                    cooldown = COOLDOWNS["gather"]
                    if guild_key == "the_barracks":
                        cooldown = 2700   # 45 min for Soldiers

                    remaining = cooldown_remaining(player, "gather", cooldown)
                    if remaining > 0 and not is_super(ctx):
                        await ctx.send(
                            f"⏳ {ctx.author.mention} Rest for **{fmt_time(remaining)}** before gathering again."
                        )
                        return

                    # ── Build bonuses from class ──────────────────────────────
                    bonuses = dict(guild_cfg.get("gather_bonus", {}))

                    # Mixologist brew bonus (always active for Club Soda)
                    if guild_key == "club_soda":
                        for res in ["herb", "alcohol"]:
                            bonuses[res] = bonuses.get(res, 1.0) + 0.3

                    # Level bonus — +2% per level
                    level_bonus = 1.0 + (player.get("level", 1) - 1) * LEVEL_GATHER_BONUS
                    for res in list(bonuses.keys()):
                        bonuses[res] = bonuses[res] * level_bonus

                    # ── Class-specific mechanics ──────────────────────────────
                    multiplier  = 1.0
                    special_msg = ""

                    if player["class"] == "Performer":
                        # Wild Roll: 0x to 3x
                        wild_options = [0, 0.5, 1, 1, 1.5, 2, 3]
                        multiplier = random.choice(wild_options)
                        if multiplier == 0:
                            special_msg = "\n🎪 *The crowd was not impressed...*"
                        elif multiplier >= 2:
                            special_msg = f"\n🎪 **STANDING OVATION! {multiplier}x haul!**"

                    elif player["class"] == "Inmate":
                        # Chaos Roll: 20% chance to double
                        if random.random() < 0.2:
                            multiplier  = 2.0
                            special_msg = "\n🎲 **CHAOS ROLL! 2x resources!**"

                    elif player["class"] == "Cultist":
                        # Ritual: 15% chance for random resource from any guild
                        if random.random() < 0.15:
                            all_resources = []
                            for g_cfg in GUILDS.values():
                                all_resources.extend(g_cfg.get("resources", []))
                            all_resources = list(set(all_resources))

                            ritual_resource = random.choice(all_resources)
                            mn, mx = BASE_GATHER.get(ritual_resource, (1, 3))
                            ritual_qty = random.randint(mn, mx)
                            add_item(player, ritual_resource, ritual_qty)

                            r_name  = ITEMS.get(ritual_resource, {}).get("name", ritual_resource)
                            r_emoji = ITEMS.get(ritual_resource, {}).get("emoji", "✨")
                            special_msg = f"\n🕯️ **RITUAL!** Dark forces grant you {ritual_qty}x {r_emoji} {r_name}!"

                    elif player["class"] == "Executioner":
                        special_msg = "\n⚙️ *Precision strike!*"

                    # ── Roll resources ────────────────────────────────────────
                    resources = guild_cfg.get("resources", [])
                    gained    = {}

                    for i, item_id in enumerate(resources):
                        mn, mx = BASE_GATHER.get(item_id, (1, 4))
                        bonus  = bonuses.get(item_id, 1.0)

                        if player["class"] == "Executioner" and i == 0:
                            base_qty = mx   # Precision: max roll on first resource
                        else:
                            base_qty = random.randint(mn, mx)

                        qty = max(0, int(base_qty * bonus * multiplier))
                        if qty > 0:
                            gained[item_id] = qty
                            add_item(player, item_id, qty)

                    # ── Sea Lion splash ───────────────────────────────────────
                    splash_msg = ""
                    if player["class"] == "Sea Lion" and gained.get("fish", 0) > 0:
                        all_others = [
                            (uid, p) for uid, p in data["players"].items()
                            if p.get("guild") and uid != str(ctx.author.id)
                        ]
                        random.shuffle(all_others)
                        for uid, sp in all_others[:1]:
                            add_item(sp, "fish", 2)
                            splash_msg = f"\n🦭 Splash! <@{uid}> got +2 fish!"

                    set_cooldown(player, "gather")
                    player["stats"]["total_gathers"] += 1
                    levelled = add_xp(player, XP_PER_GATHER, XP_PER_LEVEL)
                    save_data(data)

                # ── Build response ────────────────────────────────────────────
                if not gained:
                    result_str = "Nothing this time..."
                else:
                    result_str = "  ".join(
                        f"{ITEMS[k]['emoji']} {v} {ITEMS[k]['name']}"
                        for k, v in gained.items()
                    )

                msg = (
                    f"{guild_cfg['emoji']} **{ctx.author.display_name}** "
                    f"({player['class']}) gathered: **{result_str}**"
                    f"{special_msg}"
                )
                if splash_msg:
                    msg += splash_msg
                if levelled:
                    level     = player['level']
                    bonus_pct = round((level - 1) * LEVEL_GATHER_BONUS * 100)
                    msg += (
                        f"\n⬆️ **LEVEL UP! You are now Level {level}!**\n"
                        f"📈 Gather bonus: **+{bonus_pct}% to all resources**"
                    )

                await ctx.send(msg)

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")


async def setup(bot):
    await bot.add_cog(GatherCog(bot))
