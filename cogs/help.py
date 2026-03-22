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
            "🏡  PENGUIN VILLAGE\n"
            "────────────────────────────────────────\n"
            "Join a guild → Gather resources → Watch the stream\n"
            "→ Earn loot tokens → Craft cosmetics → Show off!\n"
            "────────────────────────────────────────\n"
            "\n"
            "  !join              See all guilds\n"
            "  !join <guild>      Join a guild (resets daily)\n"
            "  !gather            Collect your guild's resources\n"
            "  !craft             See all cosmetic recipes\n"
            "  !craft <item>      Craft a cosmetic\n"
            "  !equip <item>      Put a cosmetic on your penguin\n"
            "  !character         Your character sheet\n"
            "  !inventory         Your item bag\n"
            "  !village           See all villagers\n"
            "\n"
            "STREAM LOOT  🔴\n"
            "  !loot              Claim loot tokens when stream is live\n"
            "\n"
            "HOW IT WORKS\n"
            "  1. !join a guild to start gathering resources\n"
            "  2. !gather every hour to collect materials\n"
            "  3. Watch the stream and !loot to earn tokens\n"
            "  4. !craft cosmetics using resources + tokens\n"
            "  5. !equip your cosmetics, then wear them\n"
            "     on stream with Stream Avatars!\n"
            "```"
        )


async def setup(bot):
    await bot.add_cog(HelpCog(bot))
