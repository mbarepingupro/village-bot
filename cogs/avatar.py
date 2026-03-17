"""
cogs/avatar.py — Character card image generation
==================================================
Generates a character card PNG when !character is called.

File structure:
  assets/
    base_penguin.png          — base penguin sprite
    cosmetics/
      penguin_helmet.png      — hat layer
      jester_hat.png          — hat layer (add when ready)
      inmate_outfit.png       — outfit layer (add when ready)
      ... etc

To add a new cosmetic image:
  1. Create the PNG at 1024x1024 with transparent background
  2. Name it exactly matching the item_id in config.py (e.g. jester_hat.png)
  3. Drop it in assets/cosmetics/
  That's it — the system picks it up automatically.
"""

import io
import os
import discord
from PIL import Image, ImageDraw, ImageFont

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR     = os.path.join(BASE_DIR, "assets")
BASE_PENGUIN   = os.path.join(ASSETS_DIR, "base_penguin.png")
COSMETICS_DIR  = os.path.join(ASSETS_DIR, "cosmetics")

# ── Card dimensions ───────────────────────────────────────────────────────────
CARD_W, CARD_H = 800, 500
PENGUIN_SIZE   = 380

# ── Colors ────────────────────────────────────────────────────────────────────
BG       = (18,  20,  30)
PANEL    = (28,  32,  48)
ACCENT   = (80,  140, 200)
WHITE    = (240, 240, 245)
MUTED    = (140, 145, 160)
GOLD_COL = (220, 175, 60)
BAR_BG   = (45,  50,  70)
BAR_FG   = (80,  140, 200)
DIVIDER  = (60,  65,  90)

# ── Guild accent colors ───────────────────────────────────────────────────────
GUILD_COLORS = {
    "horny_jail":     (150, 50,  50),
    "sea_lion_pit":   (50,  100, 180),
    "club_soda":      (50,  160, 120),
    "the_circus":     (180, 100, 50),
    "the_barracks":   (100, 80,  50),
    "cursed_temple":  (100, 50,  150),
    "the_guillotine": (80,  80,  80),
}


def load_fonts():
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    bold   = paths[0] if os.path.exists(paths[0]) else None
    normal = paths[1] if os.path.exists(paths[1]) else None

    try:
        return {
            "xl":  ImageFont.truetype(bold,   36) if bold else ImageFont.load_default(),
            "lg":  ImageFont.truetype(bold,   28) if bold else ImageFont.load_default(),
            "md":  ImageFont.truetype(normal, 20) if normal else ImageFont.load_default(),
            "sm":  ImageFont.truetype(normal, 16) if normal else ImageFont.load_default(),
        }
    except Exception:
        f = ImageFont.load_default()
        return {"xl": f, "lg": f, "md": f, "sm": f}


def build_character_card(player: dict, display_name: str) -> io.BytesIO:
    """
    Build a character card image and return it as a BytesIO buffer.
    player: the player dict from village_data.json
    display_name: Discord display name
    """
    from config import GUILDS, ITEMS, XP_PER_LEVEL

    fonts = load_fonts()

    # ── Base card ─────────────────────────────────────────────────────────────
    card = Image.new("RGB", (CARD_W, CARD_H), BG)
    d    = ImageDraw.Draw(card)

    # Left panel
    d.rectangle([0, 0, 360, CARD_H], fill=PANEL)

    # ── Penguin sprite ────────────────────────────────────────────────────────
    if os.path.exists(BASE_PENGUIN):
        penguin = Image.open(BASE_PENGUIN).convert("RGBA")
        penguin = penguin.resize((PENGUIN_SIZE, PENGUIN_SIZE), Image.NEAREST)
        px_pos  = (360 - PENGUIN_SIZE) // 2
        py_pos  = (CARD_H - PENGUIN_SIZE) // 2
        card.paste(penguin, (px_pos, py_pos), penguin)

    # ── Cosmetic layers ───────────────────────────────────────────────────────
    equipped = player.get("cosmetics", {})
    # Draw in slot order: outfit first, then hat, then accessory
    for slot in ["outfit", "hat", "accessory"]:
        item_id = equipped.get(slot)
        if not item_id:
            continue
        cosmetic_path = os.path.join(COSMETICS_DIR, f"{item_id}.png")
        if os.path.exists(cosmetic_path):
            layer = Image.open(cosmetic_path).convert("RGBA")
            layer = layer.resize((PENGUIN_SIZE, PENGUIN_SIZE), Image.NEAREST)
            card.paste(layer, (px_pos, py_pos), layer)

    # ── Right panel — stats ───────────────────────────────────────────────────
    rx = 390

    # Name
    d.text((rx, 35), display_name, font=fonts["xl"], fill=WHITE)

    # Guild badge
    guild_key  = player.get("guild")
    guild_color = GUILD_COLORS.get(guild_key, ACCENT)
    if guild_key and guild_key in GUILDS:
        g          = GUILDS[guild_key]
        badge_text = f"{g['display_name']}  •  {player['class']}"
    else:
        badge_text = "No guild — use !join"
        guild_color = (60, 65, 90)

    d.rectangle([rx, 88, rx+370, 116], fill=guild_color)
    d.text((rx+8, 91), badge_text, font=fonts["sm"], fill=WHITE)

    # Divider
    d.line([rx, 128, CARD_W-20, 128], fill=DIVIDER, width=1)

    # Level + XP bar
    level     = player.get("level", 1)
    xp        = player.get("xp", 0)
    xp_needed = level * XP_PER_LEVEL
    xp_pct    = min(xp / xp_needed, 1.0) if xp_needed > 0 else 0

    d.text((rx, 140), f"Level {level}", font=fonts["lg"], fill=WHITE)
    d.rectangle([rx, 178, rx+360, 196], fill=BAR_BG)
    d.rectangle([rx, 178, rx+int(360*xp_pct), 196], fill=BAR_FG)
    d.text((rx, 202), f"{xp} / {xp_needed} XP", font=fonts["sm"], fill=MUTED)

    # Gold
    gold = player.get("gold", 0.0)
    d.text((rx, 230), f"💰  {round(gold, 1)}g", font=fonts["md"], fill=GOLD_COL)

    # Stats divider
    d.line([rx, 265, CARD_W-20, 265], fill=DIVIDER, width=1)

    stats = player.get("stats", {})
    d.text((rx, 278), f"🔨  Gathers: {stats.get('total_gathers', 0)}", font=fonts["md"], fill=MUTED)
    d.text((rx, 306), f"🎁  Loots:   {stats.get('total_loots', 0)}",   font=fonts["md"], fill=MUTED)

    tool_id  = player.get("equipped_tool")
    tool_str = ITEMS[tool_id]["name"] if tool_id and tool_id in ITEMS else "None"
    d.text((rx, 334), f"⚒️   Tool:   {tool_str}", font=fonts["md"], fill=MUTED)

    # Cosmetics divider
    d.line([rx, 368, CARD_W-20, 368], fill=DIVIDER, width=1)

    if equipped:
        y = 380
        for slot, item_id in equipped.items():
            item = ITEMS.get(item_id, {"name": item_id, "emoji": "✨"})
            d.text((rx, y), f"{item['emoji']}  {item['name']}  [{slot}]", font=fonts["md"], fill=WHITE)
            y += 28
    else:
        d.text((rx, 380), "No cosmetics equipped", font=fonts["md"], fill=MUTED)

    # Watermark
    d.text((CARD_W-165, CARD_H-26), "🏡 Penguin Village", font=fonts["sm"], fill=(55, 60, 85))

    # ── Export to buffer ──────────────────────────────────────────────────────
    buf = io.BytesIO()
    card.save(buf, format="PNG")
    buf.seek(0)
    return buf
