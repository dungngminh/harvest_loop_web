#!/usr/bin/env python3
"""Regenerate public/og.png from game assets. Requires Pillow."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "public" / "assets"
SCREENS = ROOT / "public" / "screens"
OUT = ROOT / "public" / "og.png"
FONT_PIXEL = ROOT / "public" / "fonts" / "PressStart2P.ttf"
FONT_BODY = "/System/Library/Fonts/Supplemental/Arial.ttf"

W, H = 1200, 630
MINT = (158, 230, 214)
CREAM = (250, 248, 235)
INK = (41, 64, 71)
TEAL = (26, 158, 143)
CTA = (250, 153, 20)
BLOCKS = [
    ("STEP", (115, 191, 51)),
    ("TURN", (51, 140, 230)),
    ("HARVEST", (242, 153, 26)),
    ("REPEAT", (250, 120, 26)),
]


def paste_rgba(base: Image.Image, overlay: Image.Image, xy: tuple[int, int]) -> None:
    base.paste(overlay, xy, overlay)


def paste_carrot(base: Image.Image, path: Path, x: int, y: int, size: int) -> None:
    carrot = Image.open(path).convert("RGBA")
    carrot = carrot.resize((size, int(size * carrot.height / carrot.width)), Image.Resampling.NEAREST)
    paste_rgba(base, carrot, (x, y))


def main() -> None:
    img = Image.new("RGBA", (W, H), MINT + (255,))
    draw = ImageDraw.Draw(img)
    pad = 36
    draw.rounded_rectangle((pad, pad, W - pad, H - pad), radius=10, fill=CREAM, outline=INK, width=8)

    left_x = pad + 48
    top_y = pad + 56
    f_title = ImageFont.truetype(FONT_PIXEL, 34)
    f_sub = ImageFont.truetype(FONT_PIXEL, 14)
    f_body = ImageFont.truetype(FONT_BODY, 28)
    f_btn = ImageFont.truetype(FONT_PIXEL, 10)

    draw.text((left_x, top_y), "HARVEST", font=f_title, fill=INK)
    draw.text((left_x, top_y + 52), "LOOP", font=f_title, fill=INK)
    draw.text((left_x, top_y + 122), "Learn Coding", font=f_sub, fill=TEAL)
    draw.text((left_x, top_y + 146), "Through Farming", font=f_sub, fill=TEAL)
    draw.text((left_x, top_y + 192), "Code a clever path.", font=f_body, fill=INK)
    draw.text((left_x, top_y + 228), "Grow the farm.", font=f_body, fill=INK)

    bx = left_x
    by = top_y + 278
    for label, color in BLOCKS:
        tw = draw.textlength(label, font=f_btn)
        bw = int(tw) + 22
        draw.rounded_rectangle((bx, by, bx + bw, by + 34), radius=4, fill=color, outline=INK, width=3)
        draw.text((bx + 11, by + 10), label, font=f_btn, fill=(255, 255, 255))
        bx += bw + 8

    btn_y = by + 58
    draw.rounded_rectangle((left_x, btn_y, left_x + 320, btn_y + 52), radius=6, fill=CTA, outline=INK, width=4)
    draw.text((left_x + 18, btn_y + 18), "DOWNLOAD ON APP STORE", font=f_btn, fill=(255, 255, 255))

    scene = Image.open(SCREENS / "04-fresh.png").convert("RGBA")
    frame_w, frame_h = 520, 292
    scene = ImageOps.fit(scene, (frame_w, frame_h), method=Image.Resampling.NEAREST)
    fx = W - pad - 48 - frame_w
    fy = pad + 48
    draw.rounded_rectangle((fx - 8, fy - 8, fx + frame_w + 8, fy + frame_h + 8), radius=8, fill=MINT, outline=INK, width=5)
    paste_rgba(img, scene, (fx, fy))

    pip = Image.open(ASSETS / "pip-icon.png").convert("RGBA").resize((64, 64), Image.Resampling.NEAREST)
    paste_rgba(img, pip, (fx + frame_w - 76, fy + 12))

    img.convert("RGB").save(OUT, optimize=True, quality=92)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
