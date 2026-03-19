"""
cogs/help.py — Help command
"""

from discord.ext import commands

class HelpCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_cmd(self, ctx):
        await ctx.send(
            "```\n"
            "🏡  VILLAGE BOT COMMANDS\n"
            "────────────────────────────────────────\n"
            "CHARACTER\n"
            "  !join                  → See all guilds\n"
            "  !join <guild>          → Join a guild (resets daily at 00:00)\n"
            "  !character             → Your character sheet\n"
            "  !character @user       → View someone else's sheet\n"
            "  !inventory             → Your item bag\n"
            "\n"
            "GATHERING & CRAFTING\n"
            "  !gather                → Collect your guild's resources (1hr cooldown)\n"
            "  !craft                 → See craft recipes\n"
            "  !craft <item>          → Craft an item\n"
            "\n"
            "ITEMS\n"
            "  !use                   → See your usable items\n"
            "  !use <item>            → Use a consumable\n"
            "\n"
            "GUILDS & UPGRADES\n"
            "  !guilds                → See all guilds and upgrade tiers\n"
            "  !guildstatus           → Your guild's upgrade progress\n"
            "  !contribute <r> <qty>  → Donate resources to your guild upgrade\n"
            "\n"
            "ECONOMY 💰\n"
            "  !gold                  → Check your gold balance\n"
            "  !sell                  → See resource sell prices\n"
            "  !sell <item> <qty>     → Sell resources for gold\n"
            "  !sell <item> all       → Sell your entire stack\n"
            "  !shop                  → Browse the shop\n"
            "  !buy <item>            → Buy something from the shop\n"
            "  !equip <item>          → Equip a tool or cosmetic\n"
            "\n"
            "TRADING 🤝\n"
            "  !trade 3 fish @user    → Gift items to a player\n"
            "  !trade 3 fish @user for 3 herb → Exchange offer\n"
            "  !accept                → Accept incoming trade offer\n"
            "  !decline               → Decline incoming trade offer\n"
            "  !canceltrade           → Cancel your outgoing offer\n"
            "  !offer 3 fish for 2g  → Post a market listing\n"
            "  !market                → Browse market listings\n"
            "  !claim <code>          → Claim a market listing\n"
            "  !unoffer <code>          → Cancel a specific market listing\n"
            "\n"
            "STREAM LOOT  🔴\n"
            "  !loot                  → Claim loot during a live drop\n"
            "\n"
            "MOD ONLY\n"
            "  !startloot             → Open the loot window\n"
            "  !endloot               → Close the loot window early\n"
            "  !addgold [amount]      → Add gold for testing\n"
            "```"
        )

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
