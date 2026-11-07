#!/usr/bin/env python3
"""Renders preview sheets of the icons (needs resvg and Pillow): preview/Koja-Logos-Vorschau.png"""
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import make_icons as m

HERE = Path(__file__).resolve().parent
OUT = HERE / "preview"
OUT.mkdir(exist_ok=True)
FONT = ImageFont.truetype("/System/Library/Fonts/SFNS.ttf", 30)


def render(name, px):
    png = OUT / f"{name}-{px}.png"
    subprocess.run(["resvg", "-w", str(px), "-h", str(px), str(HERE / f"{name}.svg"), str(png)], check=True)
    return Image.open(png).convert("RGBA")


def sheet(suffix, bg, label_light):
    ids = list(m.ICONS)
    cols, cell = 7, 300
    img = Image.new("RGB", (cols * cell, 2 * cell), bg)
    d = ImageDraw.Draw(img)
    for i, a in enumerate(ids):
        x, y = (i % cols) * cell, (i // cols) * cell
        ic = render(a + suffix, 400).resize((210, 210), Image.LANCZOS)
        img.paste(ic, (x + 45, y + 15), ic)
        name, colour = m.APPS[a]
        w = d.textlength(name, font=FONT)
        d.text((x + (cell - w) / 2, y + 240), name, fill="#E5E5E5" if label_light else colour, font=FONT)
    return img


if __name__ == "__main__":
    m.main()
    top, bottom = sheet("", "white", False), sheet("-macos", "#1D1D1F", True)
    both = Image.new("RGB", (top.width, top.height * 2), "white")
    both.paste(top, (0, 0))
    both.paste(bottom, (0, top.height))
    both.save(OUT / "Koja-Logos-Vorschau.png")
    # small sizes, as in Finder lists and the menu bar
    small = Image.new("RGB", (13 * 44 + 8, 52), "white")
    for i, a in enumerate(m.ICONS):
        ic = render(a, 64).resize((32, 32), Image.LANCZOS)
        small.paste(ic, (8 + i * 44, 10), ic)
    small.save(OUT / "klein-32px.png")
    print("ok")
