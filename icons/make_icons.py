#!/usr/bin/env python3
"""Kojalytics app icons: a squircle tile per Koja app with a layered, lit glyph.

    python3 make_icons.py      writes <id>.svg (full tile) and <id>-macos.svg (macOS icon grid:
                               824/1024 tile with a soft shadow) next to this file

Pure SVG (gradients, one drop-shadow filter), a few KB per icon. Every id inside an icon is
prefixed with the app id, so several icons can sit inline on one page.
"""
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def squircle(n: float = 5.0, samples: int = 72) -> str:
    """Apple-like continuous-corner tile on 0..100 (superellipse), smoothed with Catmull-Rom."""
    pts = []
    for i in range(samples):
        t = 2 * math.pi * i / samples
        c, s = math.cos(t), math.sin(t)
        pts.append((50 + 50 * math.copysign(abs(c) ** (2 / n), c), 50 + 50 * math.copysign(abs(s) ** (2 / n), s)))
    d = f"M{pts[0][0]:.2f} {pts[0][1]:.2f}"
    for i in range(samples):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % samples], pts[(i + 2) % samples]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {p2[0]:.2f} {p2[1]:.2f}"
    return d + "Z"


SQ = squircle()


def _stops(stops):
    return "".join(f'<stop offset="{o}" stop-color="{c}"' + (f' stop-opacity="{a}"' if a != 1 else "") + "/>" for o, c, a in stops)


def lin(id_, stops, x1=0, y1=0, x2=0, y2=1):
    return f'<linearGradient id="{id_}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{_stops(stops)}</linearGradient>'


def rad(id_, stops, cx=0.5, cy=0.5, r=0.5):
    return f'<radialGradient id="{id_}" cx="{cx}" cy="{cy}" r="{r}">{_stops(stops)}</radialGradient>'


def icon(a, c1, c2, tint, shade, glyph_defs, glyph, xf="", backdrop=""):
    """Tile + sheen + edge, then the glyph. `{a}` in the glyph text is the app's id prefix."""
    defs = (
        lin(f"{a}-bg", [(0, c1, 1), (1, c2, 1)], 0, 0, 1, 1)
        + lin(f"{a}-sheen", [(0, "#FFFFFF", 0.28), (1, "#FFFFFF", 0)])
        + lin(f"{a}-edge", [(0, "#FFFFFF", 0.55), (0.45, "#FFFFFF", 0.06), (1, "#000000", 0.18)])
        + lin(f"{a}-w", [(0, "#FFFFFF", 1), (1, tint, 1)])
        + f'<filter id="{a}-s" x="-30%" y="-30%" width="160%" height="160%">'
        f'<feDropShadow dx="0" dy="1.4" stdDeviation="1.6" flood-color="{shade}" flood-opacity="0.38"/></filter>'
        + f'<path id="{a}-q" d="{SQ}"/><clipPath id="{a}-c"><use href="#{a}-q"/></clipPath>'
        + glyph_defs.replace("{a}", a)
    )
    body = (
        f'<g clip-path="url(#{a}-c)">'
        f'<use href="#{a}-q" fill="url(#{a}-bg)"/>'
        f'<path d="M0 0H100V44C68 36 32 36 0 44Z" fill="url(#{a}-sheen)"/>'
        + backdrop.replace("{a}", a)
        + (f'<g transform="{xf}">' if xf else "<g>") + glyph.replace("{a}", a) + "</g>"
        + "</g>"
        f'<use href="#{a}-q" fill="none" stroke="url(#{a}-edge)" stroke-width="1.1"/>'
    )
    return f"<defs>{defs}</defs>{body}"


def poly(points):
    return "M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in points) + "Z"


def star(cx, cy, r_out, r_in, n):
    return poly([(cx + (r_out if i % 2 == 0 else r_in) * math.cos(math.pi * i / n - math.pi / 2),
                  cy + (r_out if i % 2 == 0 else r_in) * math.sin(math.pi * i / n - math.pi / 2)) for i in range(2 * n)])


def ticks(cx, cy, r1, r2, n, start=0.0):
    d = ""
    for i in range(n):
        t = 2 * math.pi * i / n + start
        d += f"M{cx + r1 * math.cos(t):.2f} {cy + r1 * math.sin(t):.2f}L{cx + r2 * math.cos(t):.2f} {cy + r2 * math.sin(t):.2f}"
    return d


def page(x0, y0, x1, y1, f=10, r=5):
    """A sheet with a folded top-right corner."""
    return (f"M{x0 + r} {y0}H{x1 - f}L{x1} {y0 + f}V{y1 - r}A{r} {r} 0 0 1 {x1 - r} {y1}"
            f"H{x0 + r}A{r} {r} 0 0 1 {x0} {y1 - r}V{y0 + r}A{r} {r} 0 0 1 {x0 + r} {y0}Z")


def fold(x1, y0, f=10):
    return f"M{x1 - f} {y0}V{y0 + f - 3}A3 3 0 0 0 {x1 - f + 3} {y0 + f}H{x1}Z"


def spark(cx, cy, r, k=0.18):
    i = r * k
    return (f"M{cx} {cy - r}C{cx + i} {cy - i} {cx + i} {cy - i} {cx + r} {cy}"
            f"C{cx + i} {cy + i} {cx + i} {cy + i} {cx} {cy + r}"
            f"C{cx - i} {cy + i} {cx - i} {cy + i} {cx - r} {cy}"
            f"C{cx - i} {cy - i} {cx - i} {cy - i} {cx} {cy - r}Z")


# id: (name, colour top-left, colour bottom-right, glyph paper tint, shadow colour, extra defs, glyph)
ICONS = {}

# WordKoja: a manuscript page with a fountain-pen nib writing on it
ICONS["wordcraft"] = ("WordKoja", "#4F9BFF", "#1747C9", "#E3ECFB", "#0B2A7A",
    lin("{a}-nib", [(0, "#3B82F6", 1), (1, "#1E3A8A", 1)]),
    f'<g filter="url(#{{a}}-s)"><path d="{page(27, 18, 71, 81, 11)}" fill="url(#{{a}}-w)"/>'
    f'<path d="{fold(71, 18, 11)}" fill="#C7D7F5"/></g>'
    '<rect x="33" y="31" width="22" height="4.6" rx="2.3" fill="#1D4ED8"/>'
    '<rect x="33" y="40" width="31" height="2.8" rx="1.4" fill="#A9BFE6"/>'
    '<rect x="33" y="46.5" width="31" height="2.8" rx="1.4" fill="#A9BFE6"/>'
    '<rect x="33" y="53" width="26" height="2.8" rx="1.4" fill="#A9BFE6"/>'
    '<rect x="33" y="59.5" width="17" height="2.8" rx="1.4" fill="#A9BFE6"/>'
    '<path d="M33 70.5C36 67 38 73 41 69.5S46 68 48 70" fill="none" stroke="#1D4ED8" stroke-width="1.4" stroke-linecap="round"/>'
    '<g transform="translate(65 64) rotate(225)" filter="url(#{a}-s)">'
    '<path d="M0 -16L7.5 -3C8.6 2.5 6.5 7.5 4.2 10.5H-4.2C-6.5 7.5 -8.6 2.5 -7.5 -3Z" fill="url(#{a}-nib)"/>'
    '<path d="M0 -15V-3.5" stroke="#FFFFFF" stroke-width="1.1" stroke-linecap="round"/>'
    '<circle cx="0" cy="-2" r="1.9" fill="#FFFFFF"/>'
    '<rect x="-5.2" y="10" width="10.4" height="6" rx="1.4" fill="#172554"/>'
    '<path d="M-3.5 -5L-5.5 -1" stroke="#FFFFFF" stroke-opacity="0.45" stroke-width="1" stroke-linecap="round"/></g>')

# GridKoja: a sheet with a selected range and a floating chart card
ICONS["gridcraft"] = ("GridKoja", "#3DD68C", "#0B7A43", "#E5F6EC", "#064E2B",
    lin("{a}-bar", [(0, "#34D399", 1), (1, "#059669", 1)]),
    '<g filter="url(#{a}-s)"><rect x="18" y="22" width="52" height="50" rx="5" fill="url(#{a}-w)"/></g>'
    '<path d="M23 22H65A5 5 0 0 1 70 27V31H18V27A5 5 0 0 1 23 22Z" fill="#C9EEDA"/>'
    '<path d="M18 31H26V72H23A5 5 0 0 1 18 67Z" fill="#DDF4E7"/>'
    '<path d="M26 22V72M40 22V72M54 22V72M18 31H70M18 41H70M18 51H70M18 61H70" stroke="#BFE3CF" stroke-width="0.8"/>'
    '<rect x="26" y="41" width="28" height="10" fill="#16A34A" fill-opacity="0.16" stroke="#15803D" stroke-width="1.3"/>'
    '<rect x="52.6" y="49.6" width="2.8" height="2.8" fill="#15803D"/>'
    '<g filter="url(#{a}-s)"><rect x="48" y="48" width="33" height="31" rx="5.5" fill="url(#{a}-w)"/></g>'
    '<rect x="54" y="63" width="5" height="10" rx="1.4" fill="url(#{a}-bar)"/>'
    '<rect x="62" y="58" width="5" height="15" rx="1.4" fill="url(#{a}-bar)"/>'
    '<rect x="70" y="53" width="5" height="20" rx="1.4" fill="url(#{a}-bar)"/>'
    '<path d="M53 73.5H76.5" stroke="#9CC9B0" stroke-width="0.9"/>'
    '<path d="M56.5 59L64.5 54.5L72.5 50.5" fill="none" stroke="#F59E0B" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
    '<circle cx="56.5" cy="59" r="1.5" fill="#F59E0B"/><circle cx="64.5" cy="54.5" r="1.5" fill="#F59E0B"/>'
    '<circle cx="72.5" cy="50.5" r="1.5" fill="#F59E0B"/>')

# DeckKoja: a stack of slides, the front one with a donut chart and legend
_c = 2 * math.pi * 8.5
ICONS["deckcraft"] = ("DeckKoja", "#FFAE4A", "#D9480F", "#FDEFE3", "#7C2D12", "",
    '<rect x="31" y="18" width="50" height="34" rx="4.5" fill="#FFFFFF" fill-opacity="0.38"/>'
    '<rect x="25.5" y="24" width="51" height="35" rx="4.5" fill="#FFFFFF" fill-opacity="0.62"/>'
    '<g filter="url(#{a}-s)"><rect x="19" y="31" width="56" height="38" rx="5" fill="url(#{a}-w)"/></g>'
    '<rect x="25" y="37" width="22" height="4" rx="2" fill="#EA580C"/>'
    '<g transform="rotate(-90 35 56)" fill="none" stroke-width="5">'
    f'<circle cx="35" cy="56" r="8.5" stroke="#EA580C" stroke-dasharray="{_c * 0.55:.2f} {_c:.2f}"/>'
    f'<circle cx="35" cy="56" r="8.5" stroke="#FBBF24" stroke-dasharray="0 {_c * 0.56:.2f} {_c * 0.24:.2f} {_c:.2f}"/>'
    f'<circle cx="35" cy="56" r="8.5" stroke="#9A3412" stroke-dasharray="0 {_c * 0.81:.2f} {_c * 0.18:.2f} {_c:.2f}"/></g>'
    '<circle cx="50" cy="50.5" r="1.7" fill="#EA580C"/><rect x="53.5" y="49.3" width="14" height="2.4" rx="1.2" fill="#E7C9B4"/>'
    '<circle cx="50" cy="56" r="1.7" fill="#FBBF24"/><rect x="53.5" y="54.8" width="11" height="2.4" rx="1.2" fill="#E7C9B4"/>'
    '<circle cx="50" cy="61.5" r="1.7" fill="#9A3412"/><rect x="53.5" y="60.3" width="8" height="2.4" rx="1.2" fill="#E7C9B4"/>'
    '<rect x="41" y="73" width="12" height="3" rx="1.5" fill="#FFFFFF" fill-opacity="0.9"/>'
    '<rect x="55.5" y="73" width="3" height="3" rx="1.5" fill="#FFFFFF" fill-opacity="0.55"/>'
    '<rect x="61" y="73" width="3" height="3" rx="1.5" fill="#FFFFFF" fill-opacity="0.55"/>')

# PdfKoja: a bookmarked document sealed with a signature stamp
ICONS["pdfcraft"] = ("PdfKoja", "#FF6B6E", "#C0192F", "#FBE7EA", "#7F1020",
    lin("{a}-seal", [(0, "#F43F5E", 1), (1, "#9F1239", 1)]),
    f'<g filter="url(#{{a}}-s)"><path d="{page(24, 17, 68, 80, 11)}" fill="url(#{{a}}-w)"/>'
    f'<path d="{fold(68, 17, 11)}" fill="#F1C4CB"/></g>'
    '<path d="M30 17H38V31L34 28L30 31Z" fill="#E11D48"/>'
    '<rect x="42" y="25" width="14" height="3.4" rx="1.7" fill="#E11D48" fill-opacity="0.75"/>'
    '<rect x="30" y="37" width="31" height="2.6" rx="1.3" fill="#EDB9C2"/>'
    '<rect x="30" y="43" width="31" height="2.6" rx="1.3" fill="#EDB9C2"/>'
    '<rect x="30" y="49" width="24" height="2.6" rx="1.3" fill="#EDB9C2"/>'
    '<rect x="30" y="55" width="16" height="2.6" rx="1.3" fill="#EDB9C2"/>'
    '<path d="M30 70C33 66 35 72 38 68.5" fill="none" stroke="#9F1239" stroke-width="1.3" stroke-linecap="round"/>'
    f'<g filter="url(#{{a}}-s)"><path d="{star(65, 64, 13.5, 11.6, 16)}" fill="url(#{{a}}-seal)"/></g>'
    '<circle cx="65" cy="64" r="8.6" fill="none" stroke="#FFFFFF" stroke-opacity="0.55" stroke-width="0.9"/>'
    '<path d="M60.6 64.2L63.6 67.2L69.6 60.8" fill="none" stroke="#FFFFFF" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>')

# PhotoKoja: two stacked prints, the front one a lit landscape
ICONS["photocraft"] = ("PhotoKoja", "#3FDDF3", "#0369A1", "#E6F5FB", "#073B5A",
    lin("{a}-sky", [(0, "#E0F2FE", 1), (1, "#7DD3FC", 1)])
    + lin("{a}-sun", [(0, "#FDE68A", 1), (1, "#F59E0B", 1)])
    + '<clipPath id="{a}-p"><rect x="30" y="31" width="40" height="29" rx="2"/></clipPath>',
    '<g transform="rotate(-9 50 50)"><rect x="24" y="24" width="50" height="44" rx="4" fill="#FFFFFF" fill-opacity="0.5"/></g>'
    '<g transform="rotate(5 50 52)">'
    '<g filter="url(#{a}-s)"><rect x="25" y="26" width="50" height="47" rx="4" fill="url(#{a}-w)"/></g>'
    '<rect x="30" y="31" width="40" height="29" rx="2" fill="url(#{a}-sky)"/>'
    '<g clip-path="url(#{a}-p)">'
    '<circle cx="60" cy="39" r="4.6" fill="url(#{a}-sun)"/>'
    '<path d="M30 60L41 44L48 51L55 43L70 60Z" fill="#38BDF8"/>'
    '<path d="M41 44L44.5 49L41.8 48.2L39.6 50Z" fill="#FFFFFF" fill-opacity="0.85"/>'
    '<path d="M30 60C39 52 46 53 53 56.5C59 59.5 64 55 70 53.5V60Z" fill="#0369A1"/></g>'
    '<rect x="30" y="64.5" width="14" height="2.6" rx="1.3" fill="#B9D6E6"/></g>')

# LightKoja: a lens barrel with aperture blades and glass reflections
_hx = [(50 + 7.5 * math.cos(math.radians(60 * i - 90)), 50 + 7.5 * math.sin(math.radians(60 * i - 90))) for i in range(6)]
_blades = ""
for _i, (_x, _y) in enumerate(_hx):
    _t = math.radians(60 * _i)
    _dx, _dy = math.cos(_t), math.sin(_t)
    _b = 2 * ((_x - 50) * _dx + (_y - 50) * _dy)
    _cc = (_x - 50) ** 2 + (_y - 50) ** 2 - 19.5 ** 2
    _k = (-_b + math.sqrt(_b * _b - 4 * _cc)) / 2
    _blades += f"M{_x:.2f} {_y:.2f}L{_x + _dx * _k:.2f} {_y + _dy * _k:.2f}"
ICONS["lightcraft"] = ("LightKoja", "#FFC93C", "#E2660A", "#FFF4DD", "#7A3405",
    rad("{a}-glass", [(0, "#1E3A8A", 1), (0.7, "#0F172A", 1), (1, "#020617", 1)], 0.42, 0.38, 0.62)
    + rad("{a}-iris", [(0, "#BAE6FD", 1), (1, "#2563EB", 1)]),
    '<g filter="url(#{a}-s)"><circle cx="50" cy="50" r="29" fill="url(#{a}-w)"/></g>'
    '<circle cx="50" cy="50" r="25.3" fill="#E9DCC3"/>'
    f'<path d="{ticks(50, 50, 25.6, 28, 36)}" stroke="#B9935A" stroke-width="0.7"/>'
    f'<path d="{ticks(50, 50, 25.6, 28.4, 4, math.pi / 4)}" stroke="#D97706" stroke-width="1.6" stroke-linecap="round"/>'
    '<circle cx="50" cy="50" r="22" fill="url(#{a}-glass)"/>'
    f'<path d="{poly(_hx)}" fill="url(#{{a}}-iris)"/>'
    f'<path d="{_blades}" stroke="#64748B" stroke-width="1.2" stroke-linecap="round"/>'
    '<circle cx="50" cy="50" r="19.5" fill="none" stroke="#334155" stroke-width="1"/>'
    '<path d="M35.5 41A16.5 16.5 0 0 1 44 34.2" fill="none" stroke="#FFFFFF" stroke-opacity="0.75" stroke-width="2.2" stroke-linecap="round"/>'
    '<circle cx="47.6" cy="33.2" r="1.1" fill="#FFFFFF" fill-opacity="0.8"/>'
    '<path d="M66 56A16.5 16.5 0 0 1 60 63.6" fill="none" stroke="#FFFFFF" stroke-opacity="0.22" stroke-width="1.8" stroke-linecap="round"/>')

# VectorKoja: a pen nib on a bézier curve with anchors and handles
ICONS["vectorcraft"] = ("VectorKoja", "#B197FC", "#5B21B6", "#EFE9FE", "#2E1065", "",
    '<path d="M21 70C30 36 60 78 79 30" fill="none" stroke="#FFFFFF" stroke-opacity="0.92" stroke-width="2.6" stroke-linecap="round"/>'
    '<path d="M21 70L30 36M79 30L60 78" stroke="#FFFFFF" stroke-opacity="0.45" stroke-width="1.2"/>'
    '<circle cx="30" cy="36" r="2.4" fill="#FFFFFF"/><circle cx="60" cy="78" r="2.4" fill="#FFFFFF"/>'
    '<rect x="17" y="66" width="8" height="8" rx="1.6" fill="#FFFFFF" stroke="#6D28D9" stroke-width="1"/>'
    '<rect x="75" y="26" width="8" height="8" rx="1.6" fill="#6D28D9" stroke="#FFFFFF" stroke-width="1.4"/>'
    '<g transform="translate(51 41) rotate(-18)" filter="url(#{a}-s)">'
    '<rect x="-6" y="-21" width="12" height="6.5" rx="2" fill="#EDE9FE"/>'
    '<path d="M0 17L-10.5 -1C-9.6 -7.5 -6.5 -12 -4.5 -14.5H4.5C6.5 -12 9.6 -7.5 10.5 -1Z" fill="url(#{a}-w)"/>'
    '<path d="M0 16.5V2.5" stroke="#5B21B6" stroke-width="1.3" stroke-linecap="round"/>'
    '<circle cx="0" cy="0.5" r="2.5" fill="#5B21B6"/>'
    '<path d="M-6 -9.5L-8 -3" stroke="#FFFFFF" stroke-width="1.2" stroke-linecap="round"/></g>')

# DesignKoja: an open magazine spread in perspective
ICONS["designcraft"] = ("DesignKoja", "#FF7EB6", "#B0124F", "#FBE8F1", "#6B0A31",
    lin("{a}-img", [(0, "#FBCFE8", 1), (1, "#EC4899", 1)], 0, 0, 1, 1)
    + lin("{a}-spine", [(0, "#831843", 0), (0.5, "#831843", 0.28), (1, "#831843", 0)], 0, 0, 1, 0),
    '<g filter="url(#{a}-s)"><path d="M50 30L19 25.5V73L50 77.5Z" fill="url(#{a}-w)"/>'
    '<path d="M50 30L81 25.5V73L50 77.5Z" fill="#FFFFFF"/></g>'
    '<g transform="matrix(1 0.1452 0 1 0 -2.76)">'
    '<rect x="23" y="31" width="23" height="15" rx="1.5" fill="url(#{a}-img)"/>'
    '<circle cx="40" cy="35.5" r="2.6" fill="#FFFFFF" fill-opacity="0.8"/>'
    '<path d="M23 46L30 39L35 43L38.5 40L46 46Z" fill="#BE185D" fill-opacity="0.75"/>'
    '<rect x="23" y="50" width="23" height="2.2" rx="1.1" fill="#F2C3D8"/>'
    '<rect x="23" y="55" width="23" height="2.2" rx="1.1" fill="#F2C3D8"/>'
    '<rect x="23" y="60" width="15" height="2.2" rx="1.1" fill="#F2C3D8"/></g>'
    '<g transform="matrix(1 -0.1452 0 1 0 11.76)">'
    '<rect x="54" y="31" width="20" height="4.4" rx="2.2" fill="#DB2777"/>'
    '<rect x="54" y="39.5" width="9.5" height="2" rx="1" fill="#F2C3D8"/><rect x="65.5" y="39.5" width="9.5" height="2" rx="1" fill="#F2C3D8"/>'
    '<rect x="54" y="44" width="9.5" height="2" rx="1" fill="#F2C3D8"/><rect x="65.5" y="44" width="9.5" height="2" rx="1" fill="#F2C3D8"/>'
    '<rect x="54" y="48.5" width="9.5" height="2" rx="1" fill="#F2C3D8"/><rect x="65.5" y="48.5" width="9.5" height="2" rx="1" fill="#F2C3D8"/>'
    '<rect x="54" y="55" width="1.6" height="9" rx="0.8" fill="#DB2777"/>'
    '<rect x="57.5" y="56" width="17" height="2.4" rx="1.2" fill="#E9A1C2"/><rect x="57.5" y="61" width="12" height="2.4" rx="1.2" fill="#E9A1C2"/></g>'
    '<path d="M46 30.6H54V77H46Z" fill="url(#{a}-spine)"/>')

# FigKoja: an artboard selection, shapes and a live collaborator cursor
ICONS["figcraft"] = ("FigKoja", "#7C83FF", "#3426B8", "#ECEBFF", "#1E1B4B",
    lin("{a}-o1", [(0, "#67E8F9", 1), (1, "#06B6D4", 1)]) + lin("{a}-o2", [(0, "#FDE68A", 1), (1, "#F59E0B", 1)]),
    '<rect x="17" y="19" width="56" height="50" rx="4" fill="#FFFFFF" fill-opacity="0.12" stroke="#FFFFFF" stroke-opacity="0.35" stroke-width="0.9"/>'
    '<rect x="21" y="15" width="12" height="2.4" rx="1.2" fill="#FFFFFF" fill-opacity="0.55"/>'
    '<g filter="url(#{a}-s)"><circle cx="38" cy="45" r="10" fill="url(#{a}-o1)"/>'
    '<rect x="42" y="31" width="17" height="17" rx="4.5" fill="url(#{a}-o2)" fill-opacity="0.95"/></g>'
    '<rect x="26" y="29" width="37" height="30" fill="none" stroke="#FFFFFF" stroke-width="1.2"/>'
    '<g fill="#FFFFFF" stroke="#4338CA" stroke-width="0.9"><rect x="24.2" y="27.2" width="3.6" height="3.6"/>'
    '<rect x="61.2" y="27.2" width="3.6" height="3.6"/><rect x="24.2" y="57.2" width="3.6" height="3.6"/>'
    '<rect x="61.2" y="57.2" width="3.6" height="3.6"/></g>'
    '<g transform="translate(55 52) scale(0.92)" filter="url(#{a}-s)">'
    '<path d="M0 0V18.5L5 14L8.6 21.6L11.8 20.2L8.4 12.9H15Z" fill="#FFFFFF" stroke="#1E1B4B" stroke-width="1.1" stroke-linejoin="round"/>'
    '<rect x="12" y="17.5" width="17" height="7" rx="3.5" fill="#F97316"/>'
    '<rect x="15" y="20.1" width="11" height="1.8" rx="0.9" fill="#FFFFFF"/></g>')

# FilmKoja: a clapperboard with its arm open, on a dark stage with a red glow
_stripes = "".join(f"M{x} 0H{x + 5.5}L{x + 1.5} 8H{x - 4}Z" for x in range(7, 62, 11))
ICONS["filmcraft"] = ("FilmKoja", "#4B4B55", "#0B0B0F", "#E8E8EC", "#000000",
    rad("{a}-glow", [(0, "#F43F5E", 0.55), (1, "#F43F5E", 0)], 0.8, 0.85, 0.55),
    '<rect width="100" height="100" fill="url(#{a}-glow)"/>'
    '<g filter="url(#{a}-s)">'
    '<rect x="21" y="43" width="58" height="34" rx="4" fill="url(#{a}-w)"/>'
    '<g transform="translate(21 43)"><path d="M4 0H54A4 4 0 0 1 58 4V8H0V4A4 4 0 0 1 4 0Z" fill="#FFFFFF"/>'
    f'<path d="{_stripes}" fill="#18181B"/></g>'
    '<g transform="rotate(-15 23 41)"><rect x="21" y="33" width="58" height="8" rx="2" fill="#FFFFFF"/>'
    f'<path d="{_stripes}" fill="#F43F5E" transform="translate(21 33)"/></g></g>'
    '<circle cx="24.5" cy="41.5" r="2.3" fill="#A1A1AA" stroke="#FFFFFF" stroke-width="0.8"/>'
    '<path d="M25 59.5H75M25 68.5H75M50 51V68.5" stroke="#D4D4D8" stroke-width="0.9"/>'
    '<rect x="26" y="54" width="15" height="2.4" rx="1.2" fill="#A1A1AA"/>'
    '<rect x="55" y="54" width="10" height="2.4" rx="1.2" fill="#A1A1AA"/>'
    '<rect x="26" y="63" width="18" height="2.4" rx="1.2" fill="#A1A1AA"/>'
    '<rect x="55" y="63" width="14" height="2.4" rx="1.2" fill="#A1A1AA"/>'
    '<circle cx="71" cy="72.6" r="1.8" fill="#EF4444"/><rect x="26" y="71.6" width="9" height="2" rx="1" fill="#D4D4D8"/>')

# EffectKoja: a glowing spark with an orbit and satellites
ICONS["effectcraft"] = ("EffectKoja", "#F28CFF", "#7E22CE", "#FBE6FF", "#3B0764",
    rad("{a}-halo", [(0, "#FFFFFF", 0.55), (1, "#FFFFFF", 0)]) + lin("{a}-orb", [(0, "#FFFFFF", 1), (1, "#F0ABFC", 1)]),
    '<circle cx="46" cy="47" r="27" fill="url(#{a}-halo)"/>'
    '<g transform="rotate(-24 50 52)"><ellipse cx="50" cy="52" rx="32" ry="11" fill="none" stroke="#FFFFFF" stroke-opacity="0.5" stroke-width="1.2"/></g>'
    f'<g filter="url(#{{a}}-s)"><path d="{spark(46, 47, 22)}" fill="url(#{{a}}-w)"/></g>'
    f'<path d="{spark(46, 47, 7, 0.2)}" fill="#F5D0FE"/>'
    f'<path d="{spark(71, 68, 7.5)}" fill="#FFFFFF" fill-opacity="0.9"/>'
    f'<path d="{spark(26, 71, 4)}" fill="#FFFFFF" fill-opacity="0.7"/>'
    '<g filter="url(#{a}-s)"><circle cx="78" cy="38.5" r="4" fill="url(#{a}-orb)"/></g>'
    '<circle cx="21.5" cy="62" r="1.6" fill="#FFFFFF" fill-opacity="0.8"/>'
    '<circle cx="74" cy="22" r="1.2" fill="#FFFFFF" fill-opacity="0.7"/>')

# SoundKoja: a record with grooves and a glass waveform strip
_bars = ""
for _i in range(14):
    _x = 22 + _i * 4.3
    _h = 3 + 9.5 * abs(math.sin(_i * 0.9 + 0.4)) * (0.55 + 0.45 * math.sin(math.pi * _i / 13))
    _bars += f'<rect x="{_x:.2f}" y="{68 - _h / 2:.2f}" width="2.4" height="{_h:.2f}" rx="1.2"/>'
ICONS["soundcraft"] = ("SoundKoja", "#3EE6CB", "#0B6B63", "#E2F7F3", "#042F2E",
    rad("{a}-vinyl", [(0, "#1F5F5A", 1), (0.75, "#0B3B38", 1), (1, "#052826", 1)], 0.4, 0.35, 0.7)
    + lin("{a}-label", [(0, "#FDE68A", 1), (1, "#F59E0B", 1)]),
    '<g filter="url(#{a}-s)"><circle cx="50" cy="42" r="25" fill="url(#{a}-vinyl)"/></g>'
    '<g fill="none" stroke="#FFFFFF" stroke-opacity="0.13" stroke-width="0.6">'
    '<circle cx="50" cy="42" r="21.5"/><circle cx="50" cy="42" r="18.5"/><circle cx="50" cy="42" r="15.5"/><circle cx="50" cy="42" r="12.5"/></g>'
    '<path d="M31.5 32A21 21 0 0 1 44 22" fill="none" stroke="#FFFFFF" stroke-opacity="0.35" stroke-width="2" stroke-linecap="round"/>'
    '<circle cx="50" cy="42" r="8" fill="url(#{a}-label)"/><circle cx="50" cy="42" r="1.5" fill="#052826"/>'
    '<g filter="url(#{a}-s)"><rect x="17" y="58" width="66" height="20" rx="10" fill="#FFFFFF" fill-opacity="0.24"/></g>'
    '<rect x="17" y="58" width="66" height="20" rx="10" fill="none" stroke="#FFFFFF" stroke-opacity="0.5" stroke-width="0.8"/>'
    f'<g fill="#FFFFFF">{_bars}</g>')

# CADKoja: an isometric part on a blueprint grid, with dimension lines
_s, _cx, _h, _ty = 22, 51, 22, 21
_P = {"top": (_cx, _ty), "r": (_cx + _s * 0.866, _ty + _s * 0.5), "f": (_cx, _ty + _s), "l": (_cx - _s * 0.866, _ty + _s * 0.5)}
_d = lambda p: (p[0], p[1] + _h)  # noqa: E731
_grid = "".join(f"M{v} 0V100M0 {v}H100" for v in range(10, 100, 10))
_fb, _rb, _lt, _lb = _d(_P["f"]), _d(_P["r"]), _P["l"], _d(_P["l"])
ICONS["cadcraft"] = ("CADKoja", "#4C78B8", "#0E2547", "#EAF2FF", "#020B1C", "",
    f'<path d="{_grid}" stroke="#FFFFFF" stroke-opacity="0.08" stroke-width="0.5"/>'
    '<g filter="url(#{a}-s)" stroke="#0F2A55" stroke-width="0.9" stroke-linejoin="round">'
    f'<path d="{poly([_P["top"], _P["r"], _P["f"], _P["l"]])}" fill="#FFFFFF"/>'
    f'<path d="{poly([_P["l"], _P["f"], _fb, _lb])}" fill="#D6E6FF"/>'
    f'<path d="{poly([_P["f"], _P["r"], _rb, _fb])}" fill="#9CC3FF"/></g>'
    f'<ellipse cx="{_cx}" cy="{_ty + _s * 0.5:.2f}" rx="6.4" ry="3.7" fill="#D6E6FF" stroke="#0F2A55" stroke-width="0.9"/>'
    f'<ellipse cx="{_cx}" cy="{_ty + _s * 0.5:.2f}" rx="2.4" ry="1.4" fill="#0F2A55"/>'
    '<g stroke="#67E8F9" stroke-width="0.9" stroke-linecap="round" fill="none">'
    f'<path d="M{_fb[0] + 3:.2f} {_fb[1] + 5:.2f}L{_rb[0] + 3:.2f} {_rb[1] + 5:.2f}"/>'
    f'<path d="M{_fb[0]:.2f} {_fb[1] + 1.5:.2f}L{_fb[0] + 4.5:.2f} {_fb[1] + 7.5:.2f}M{_rb[0]:.2f} {_rb[1] + 1.5:.2f}L{_rb[0] + 4.5:.2f} {_rb[1] + 7.5:.2f}"/>'
    f'<path d="M{_lt[0] - 6:.2f} {_lt[1]:.2f}V{_lb[1]:.2f}M{_lt[0] - 8.5:.2f} {_lt[1]:.2f}H{_lt[0] - 3.5:.2f}M{_lt[0] - 8.5:.2f} {_lb[1]:.2f}H{_lt[0] - 3.5:.2f}"/></g>'
    f'<g fill="#67E8F9"><circle cx="{(_fb[0] + _rb[0]) / 2 + 3:.2f}" cy="{(_fb[1] + _rb[1]) / 2 + 5:.2f}" r="1.3"/>'
    f'<circle cx="{_lt[0] - 6:.2f}" cy="{(_lt[1] + _lb[1]) / 2:.2f}" r="1.3"/></g>')


def svg(inner):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">{inner}</svg>\n'


APPS = {k: (v[0], v[2]) for k, v in ICONS.items()}   # id → (name, label colour)


# Parts that stay put behind the glyph (a full-tile glow, a grid), and parts left out when the
# glyph's extent is measured (a soft halo).
BACKDROP = {"filmcraft": r'<rect width="100" height="100" fill="url\(#\{a\}-glow\)"/>',
            "cadcraft": r'<path d="M10 0V100[^>]*/>'}
MEASURE_SKIP = {"effectcraft": r'<circle cx="46" cy="47" r="27" fill="url\(#\{a\}-halo\)"/>'}
FILL = 77.0      # the glyph's larger side, in tile units (the tile is 100)


def split(app_id, glyph):
    import re
    back = ""
    if app_id in BACKDROP:
        m_ = re.search(BACKDROP[app_id], glyph)
        back, glyph = m_.group(0), glyph.replace(m_.group(0), "")
    return back, glyph


def fit(app_id, c1, c2, tint, shade, gdefs, glyph):
    """Scale and centre the glyph so its visible extent fills FILL units of the tile."""
    import re, subprocess, tempfile
    from PIL import Image
    probe = glyph
    if app_id in MEASURE_SKIP:
        probe = re.sub(MEASURE_SKIP[app_id], "", probe)
    inner = icon(app_id, c1, c2, tint, shade, gdefs, probe)
    inner = re.sub(r'<use href="#[^"]+-q" fill="url\(#[^"]+-bg\)"/>', "", inner)        # no tile
    inner = re.sub(r'<path d="M0 0H100V44[^>]*/>', "", inner)                         # no sheen
    inner = re.sub(r'<use href="#[^"]+-q" fill="none"[^>]*/>', "", inner)              # no edge
    inner = re.sub(r' filter="url\(#[^"]+-s\)"', "", inner)                          # no shadows
    inner = inner.replace(f'<g clip-path="url(#{app_id}-c)">', "<g>")
    with tempfile.TemporaryDirectory() as t:
        src, png = Path(t) / "g.svg", Path(t) / "g.png"
        src.write_text(svg(inner))
        subprocess.run(["resvg", "-w", "400", "-h", "400", str(src), str(png)], check=True)
        alpha = Image.open(png).getchannel("A").point(lambda v: 255 if v > 60 else 0)
        x0, y0, x1, y1 = (v / 4 for v in alpha.getbbox())
    k = min(FILL / (x1 - x0), FILL / (y1 - y0), 1.6)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return f"translate(50 50) scale({k:.3f}) translate({-cx:.2f} {-cy:.2f})", k


def main():
    for app_id, (_name, c1, c2, tint, shade, gdefs, glyph) in ICONS.items():
        back, glyph = split(app_id, glyph)
        xf, k = fit(app_id, c1, c2, tint, shade, gdefs, glyph)
        flat = icon(app_id, c1, c2, tint, shade, gdefs, glyph, xf, back)
        (HERE / f"{app_id}.svg").write_text(svg(flat))
        mac = (
            f'<defs><filter id="{app_id}-m" x="-20%" y="-20%" width="140%" height="140%">'
            '<feDropShadow dx="0" dy="1.3" stdDeviation="1.7" flood-color="#000" flood-opacity="0.3"/></filter></defs>'
            f'<g transform="translate(10 9.3) scale(0.8)" filter="url(#{app_id}-m)">{flat}</g>'
        )
        (HERE / f"{app_id}-macos.svg").write_text(svg(mac))
        print(f"{app_id:12} glyph x{k:.2f}")
    print(f"{len(ICONS)} icons written to {HERE}")


if __name__ == "__main__":
    main()
