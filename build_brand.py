"""Writes the Kojalytics brand SVGs (Facetten-K mark + wordmark) into the given folder.

The wordmark is "Kojalytics" set in Inter Bold (SIL OFL 1.1), converted to outlines so it renders
without fonts installed. Usage: python3 build_brand.py <inter.ttf> <out-dir>
"""
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

font_path, out = sys.argv[1], Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)

GRADIENT = (
    '<linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0" stop-color="#818cf8"/><stop offset="1" stop-color="#4f46e5"/></linearGradient>'
)
K_SHAPES = (
    '<rect x="27" y="22" width="13" height="56" rx="3" fill="{c}"/>'
    '<polygon points="45,50 66,22 81,22 60,50" fill="{c}"/>'
    '<polygon points="52,56 62,46 81,78 66,78" fill="{c}" opacity="{o}"/>'
)


def mark(tile: bool, color: str = "#fff", lower_opacity: str = "0.72") -> str:
    body = K_SHAPES.format(c=color, o=lower_opacity)
    if tile:
        body = f'<defs>{GRADIENT}</defs><rect width="100" height="100" rx="24" fill="url(#g)"/>' + body
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">{body}</svg>\n'


def wordmark_path(text: str, size: float, x0: float, baseline: float, weight: int) -> tuple[str, float]:
    font = TTFont(font_path)
    if "fvar" in font:
        from fontTools.varLib.instancer import instantiateVariableFont

        font = instantiateVariableFont(font, {"wght": weight})
    upm = font["head"].unitsPerEm
    scale = size / upm
    glyphs = font.getGlyphSet()
    cmap = font.getBestCmap()
    pen = SVGPathPen(glyphs)
    x = 0.0
    for ch in text:
        name = cmap[ord(ch)]
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x0 + x, baseline)))
        x += glyphs[name].width * scale
    return pen.getCommands(), x


# Mark: tile (app icon), and black-only (macOS menu-bar template).
(out / "kojalytics-mark.svg").write_text(mark(tile=True))
(out / "kojalytics-mark-black.svg").write_text(mark(tile=False, color="#000", lower_opacity="0.6"))

# Logo: tile mark + wordmark, ink for light backgrounds and white for dark ones.
path, width = wordmark_path("Kojalytics", 78, 128, 80, 700)
total = 128 + width + 4
for name, ink in (("kojalytics-logo.svg", "#0c0c12"), ("kojalytics-logo-white.svg", "#f0f0f5")):
    tile = f'<defs>{GRADIENT}</defs><rect width="100" height="100" rx="24" fill="url(#g)"/>' + K_SHAPES.format(c="#fff", o="0.72")
    (out / name).write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total:.2f} 100">{tile}'
        f'<path d="{path}" fill="{ink}"/></svg>\n'
    )
print(f"logo view box: {total:.2f} x 100")
