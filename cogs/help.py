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
            "  !join                 → See all guilds\n"
            "  !join <guild>         → Join a guild & get your class\n"
            "  !character            → Your character sheet\n"
            "  !character @user      → View someone else's sheet\n"
            "  !inventory            → Your item bag\n"
            "\n"
            "GATHERING & CRAFTING\n"
            "  !gather               → Collect resources (2min cooldown)\n"
            "  !craft                → See craft recipes\n"
            "  !craft <item>         → Craft an item\n"
            "\n"
            "ECONOMY 💰\n"
            "  !gold                 → Check your gold balance\n"
            "  !sell                 → See resource sell prices\n"
            "  !sell <item> <qty>    → Sell resources for gold\n"
            "  !sell <item> all      → Sell your entire stack\n"
            "  !shop                 → Browse the shop\n"
            "  !buy <item>           → Buy something from the shop\n"
            "  !equip <item>         → Equip a tool or cosmetic\n"
            "\n"
            "STREAM LOOT  🔴\n"
            "  !loot                 → Claim loot during a live drop\n"
            "\n"
            "MOD ONLY\n"
            "  !startloot            → Open the loot window\n"
            "  !endloot              → Close the loot window early\n"
            "```"
        )

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
