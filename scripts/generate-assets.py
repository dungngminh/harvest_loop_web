#!/usr/bin/env python3
"""Clean simulator screenshots and regenerate landing-page assets."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SCREENS = ROOT / "public" / "screens"
ASSETS = ROOT / "public" / "assets"

# iPhone landscape captures include the Dynamic Island on the left.
TARGET_W = 1200


def load_screen(name: str) -> Image.Image:
    return Image.open(SCREENS / name).convert("RGBA")


def notch_width(img: Image.Image) -> int:
    """Return pixels to crop from the left where the Dynamic Island sits."""
    w, h = img.size
    px = img.load()
    step = max(1, h // 48)
    samples = h // step
    notch_end = 0
    for x in range(min(w // 3, 220)):
        dark = sum(1 for y in range(0, h, step) if sum(px[x, y][:3]) < 85)
        if dark / samples > 0.15:
            notch_end = x
    return notch_end + 10 if notch_end > 8 else 0


def clean_screen(img: Image.Image) -> Image.Image:
    w, h = img.size
    if h > w:
        img = img.rotate(90, expand=True)
        w, h = img.size
    px = img.load()

    def col_score(x: int) -> int:
        total = 0
        for y in range(0, h, max(1, h // 40)):
            total += sum(px[x, y][:3])
        return total

    left = 0
    while left < w - 1 and col_score(left) < 120:
        left += 1
    right = w - 1
    while right > left + 1 and col_score(right) < 120:
        right -= 1
    img = img.crop((left, 0, right + 1, h))
    w, h = img.size
    cleaned = img.crop((notch_width(img), 0, w, h))
    if cleaned.width > 1200:
        ratio = 1200 / cleaned.width
        cleaned = cleaned.resize(
            (1200, int(cleaned.height * ratio)), Image.Resampling.NEAREST
        )
    return cleaned


def save_clean_screens() -> dict[str, Image.Image]:
    cleaned: dict[str, Image.Image] = {}
    for path in sorted(SCREENS.glob("*.png")):
        img = clean_screen(load_screen(path.name))
        img.save(path, optimize=True)
        cleaned[path.name] = img
        print(f"cleaned screen {path.name} -> {img.size}")
    return cleaned


def crop(img: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
    w, h = img.size
    x1, y1, x2, y2 = box
    x1 = max(0, min(x1, w))
    x2 = max(x1 + 1, min(x2, w))
    y1 = max(0, min(y1, h))
    y2 = max(y1 + 1, min(y2, h))
    return img.crop((x1, y1, x2, y2))


def fit(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.contain(img, size, method=Image.Resampling.NEAREST)


def square_icon(img: Image.Image, size: int = 96) -> Image.Image:
    px = img.load()
    w, h = img.size
    points = [(x, y) for y in range(h) for x in range(w) if px[x, y][3] > 10 and sum(px[x, y][:3]) > 40]
    if points:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        pad = 4
        img = img.crop(
            (
                max(0, min(xs) - pad),
                max(0, min(ys) - pad),
                min(w, max(xs) + pad + 1),
                min(h, max(ys) + pad + 1),
            )
        )
    side = max(img.size)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(img, ((side - img.width) // 2, (side - img.height) // 2), img)
    return sq.resize((size, size), Image.Resampling.NEAREST)


def write_assets(cleaned: dict[str, Image.Image]) -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)

    fresh = cleaned["04-fresh.png"]
    hero = cleaned["01-hero.png"]
    blocks = cleaned["02-blocks.png"]
    loops = cleaned["03-loops.png"]
    harvest = cleaned["05-harvest.png"]
    stars = cleaned["06-stars.png"]
    w, h = fresh.width, fresh.height

    def rel(
        box: tuple[float, float, float, float],
        base: Image.Image | None = None,
    ) -> tuple[int, int, int, int]:
        src = base or fresh
        sw, sh = src.width, src.height
        return tuple(int(v * sw if i % 2 == 0 else v * sh) for i, v in enumerate(box))

    crop(fresh, rel((0.06, 0.02, 0.94, 0.72))).save(ASSETS / "hero-scene.png", optimize=True)
    crop(fresh, rel((0.0, 0.0, 1.0, 1.0))).save(ASSETS / "thumb-observe.png", optimize=True)
    crop(blocks, rel((0.0, 0.0, 1.0, 1.0), blocks)).save(ASSETS / "thumb-build.png", optimize=True)
    crop(harvest, rel((0.0, 0.0, 1.0, 1.0), harvest)).save(ASSETS / "thumb-run.png", optimize=True)
    crop(harvest, rel((0.04, 0.80, 0.96, 1.0), harvest)).save(
        ASSETS / "blocks-palette.png", optimize=True
    )

    subprocess.run([sys.executable, str(ROOT / "scripts" / "render-props.py")], check=True)
    crop(stars, rel((0.22, 0.08, 0.78, 0.72), stars)).save(ASSETS / "stars.png", optimize=True)
    crop(fresh, rel((0.36, 0.30, 0.50, 0.52))).resize((120, 120), Image.Resampling.NEAREST).save(
        ASSETS / "farm-tile.png", optimize=True
    )

    print("wrote assets to", ASSETS)


def main() -> None:
    cleaned = save_clean_screens()
    write_assets(cleaned)


if __name__ == "__main__":
    main()
