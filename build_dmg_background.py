"""Writes a Kojalytics DMG background (660 x 400 pt) as an SVG with outlined text.

Usage: python3 build_dmg_background.py <Inter-Variable.ttf> <out.svg> [<title> <app-icon.png>]
Without a title it is the Kojalytics Launcher's (K mark on the panel); with one, the app's icon
is shown on the panel instead. Finder puts the app icon at (326, 205) and Applications at (574, 205).
"""
import base64
import sys

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

font_path, out = sys.argv[1], sys.argv[2]
name = sys.argv[3] if len(sys.argv) > 3 else "Kojalytics Launcher"
icon_png = sys.argv[4] if len(sys.argv) > 4 else None


def text_path(text, size, x, baseline, weight):
    font = instantiateVariableFont(TTFont(font_path), {"wght": weight})
    scale = size / font["head"].unitsPerEm
    glyphs, cmap = font.getGlyphSet(), font.getBestCmap()
    pen = SVGPathPen(glyphs)
    cursor = 0.0
    for ch in text:
        name = cmap[ord(ch)]
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x + cursor, baseline)))
        cursor += glyphs[name].width * scale
    return pen.getCommands(), cursor


title, title_w = text_path(name, 22, 0, 0, 700)
hint, hint_w = text_path("Zum Installieren in den Programme-Ordner ziehen", 12.5, 0, 0, 500)
# Centre both lines over the icon area (x 252..648).
area_left, area_width = 252, 396
title_x = area_left + (area_width - title_w) / 2
hint_x = area_left + (area_width - hint_w) / 2
title, _ = text_path(name, 22, title_x, 82, 700)
hint, _ = text_path("Zum Installieren in den Programme-Ordner ziehen", 12.5, hint_x, 330, 500)

if icon_png:
    data = base64.b64encode(open(icon_png, "rb").read()).decode()
    panel_art = f'<image href="data:image/png;base64,{data}" x="56" y="140" width="120" height="120"/>'
else:
    panel_art = """<g transform="translate(56 140) scale(1.2)">
<rect width="100" height="100" rx="24" fill="#0c0c12" fill-opacity="0.18"/>
<rect x="27" y="22" width="13" height="56" rx="3" fill="#fff"/>
<polygon points="45,50 66,22 81,22 60,50" fill="#fff"/>
<polygon points="52,56 62,46 81,78 66,78" fill="#fff" fill-opacity="0.72"/>
</g>"""

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="660" height="400" viewBox="0 0 660 400">
<defs>
<linearGradient id="panel" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#818cf8"/><stop offset="1" stop-color="#3730a3"/></linearGradient>
<radialGradient id="glow" cx="0.5" cy="0.45" r="0.6"><stop offset="0" stop-color="#ffffff" stop-opacity="0.18"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></radialGradient>
</defs>
<rect width="660" height="400" fill="#f4f4f8"/>
<rect width="232" height="400" fill="url(#panel)"/>
<rect width="232" height="400" fill="url(#glow)"/>
{panel_art}
<path d="{title}" fill="#0c0c12"/>
<line x1="270" y1="104.5" x2="630" y2="104.5" stroke="#6366f1" stroke-opacity="0.35" stroke-width="1"/>
<path d="M418 205 H486" stroke="#6366f1" stroke-width="3" stroke-linecap="round" stroke-dasharray="1 9"/>
<path d="M500 205 L486 197 L486 213 Z" fill="#6366f1"/>
<path d="{hint}" fill="#4b4b5c"/>
</svg>
"""
with open(out, "w") as f:
    f.write(svg)
print(f"wrote {out}")
