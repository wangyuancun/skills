"""FontWorks identity.

Look: a naive, hand-drawn white mark sitting small in a wide, grainy,
sun-washed field. Ink black, cinnabar red, warm paper.
Generous space; the mark never fights for attention.

Type: bundled open fonts for the wordmark and text.

Based on Punchcutter by Rishi Shah (MIT). All original branding replaced.
"""
from __future__ import annotations

import html
import math
import os
import random
import sys

NAME = "FontWorks"
VERSION = "1.0.0"
TAGLINE = "说一句话，得到一套字体。"
SITE = "fontworks.local"
REPO = "local/fontworks"

# palette — ink, cinnabar, paper (distinct from the upstream olive/sage scheme)
CREAM = "#f5f2ec"     # paper
INK = "#1a1a1a"       # text
MEADOW = "#b23a2e"    # cinnabar red: the accent (was olive)
SAGE = "#d4a89f"      # soft red-green neutral
STRAW = "#e3d4c4"     # warm paper tone
MOSS = "#2a1916"      # deep ink, dark mode
SKY = "#d9dde0"       # cool grey
MUTE = "#8a8378"
GUIDE = "#c0392b"     # drop-out red on the handwriting sheet
ACCENT = MEADOW
PAPER, SIGNAL = CREAM, ACCENT   # older names

# UI tokens: the one source for every page, proof and image FontWorks makes
TOKENS = {
    "light": dict(bg=CREAM, fg=INK, mute=MUTE, line="#ddd5c4", card="#fbf8f1", acc=MEADOW, acc_fg="#ffffff", sage=SAGE, straw=STRAW, sky=SKY),
    "dark": dict(bg="#161b10", fg=CREAM, mute="#9a9886", line="#2e3824", card="#1d2416", acc="#b5c27a", acc_fg="#161b10", sage=SAGE, straw=STRAW, sky=SKY),
}
RADIUS = 26          # cards and hero panels, px
LINE = TOKENS["light"]["line"]
CARD = TOKENS["light"]["card"]


def css_vars():
    """CSS custom properties for light and dark themes."""
    def block(t):
        return ";".join(f"--{k}:{v}" for k, v in t.items())
    return (f":root{{{block(TOKENS['light'])};--r:{RADIUS}px}}\n"
            f"[data-theme=dark]{{{block(TOKENS['dark'])}}}\n"
            f"@media(prefers-color-scheme:dark){{:root:not([data-theme=light]){{{block(TOKENS['dark'])}}}}}")


def label(s, x, y, size=12, fill=MUTE, anchor="start"):
    """Small uppercase spaced label, the brand's caption style."""
    return text(s.upper(), x, y, size, "Regular", fill, tracking=0.12, anchor=anchor)[0]

HERE = os.path.dirname(os.path.abspath(__file__))
_faces = {}


def font_path(style="Regular"):
    """Brand fonts. Styles: Light Regular Bold ExtraBold (Burin Grotesk), Round, RoundBold (Pomelo Round)."""
    name = {"Round": "PomeloRound-Regular", "RoundBold": "PomeloRound-Bold"}.get(style, f"BurinGrotesk-{style}")
    return os.path.join(HERE, "..", "brand_fonts", name + ".ttf")


def face(style="Regular"):
    if style not in _faces:
        from .proof import Face
        _faces[style] = Face(font_path(style))
    return _faces[style]


def text(s, x, y, size, style="Regular", fill=INK, tracking=0.0, anchor="start"):
    """Text set in a brand face as SVG paths. y is the baseline. Returns (svg, width)."""
    f = face(style)
    infos, pos = f.shape(s)
    k = size / f.upm
    pen, parts = 0.0, []
    for info, p in zip(infos, pos):
        d = f.path(info.codepoint)
        if d:
            parts.append(f'<path transform="translate({pen + p.x_offset:.1f} 0)" d="{d}"/>')
        pen += p.x_advance + tracking * f.upm
    width = pen * k
    if anchor == "middle":
        x -= width / 2
    elif anchor == "end":
        x -= width
    return (f'<g fill="{fill}" transform="translate({x:.3f} {y:.3f}) scale({k:.6f} {-k:.6f})">{"".join(parts)}</g>', width)


# ---------------------------------------------------------------- the mark
_MARK = None


def mark_path():
    """The mark: a carved seal-style glyph — three horizontal strokes crossed
    by one vertical, evoking 活 (water + tongue) without copying any typeface.
    Hand-drawn with a little wobble, in a 100 x 100 box (SVG space, y down)."""
    global _MARK
    if _MARK:
        return _MARK
    from .geometry import Pen, Stroke
    rnd = random.Random(23)
    pen = Pen(hratio=1.0, roundness=0.4)

    def j(v, a=1.0):
        return v + rnd.uniform(-a, a)

    cons = []
    # three horizontal strokes (the 氵water radical, abstracted as bars)
    for cy, x0, x1 in ((36, 26, 74), (52, 30, 70), (68, 24, 76)):
        st = Stroke(pen, 9)
        st.m(j(x0), j(cy)).l(j(x1), j(cy))
        cons += st.outline("round", "round")
    # one vertical stroke crossing them (the seal's spine)
    st = Stroke(pen, 9.5)
    st.m(j(50), j(20)).l(j(50), j(84))
    cons += st.outline("round", "round")
    d = []
    for c in cons:
        cmd = f"M{c.start[0]:.2f} {100 - c.start[1]:.2f}"
        for sg in c.segs:
            if sg[0] == "l":
                cmd += f"L{sg[1][0]:.2f} {100 - sg[1][1]:.2f}"
            else:
                cmd += "C" + " ".join(f"{p[0]:.2f} {100 - p[1]:.2f}" for p in sg[1:])
        d.append(cmd + "Z")
    _MARK = " ".join(d)
    return _MARK


def mark(x, y, size, color="#ffffff", bg=MEADOW, radius=0.24):
    """The mark on a rounded tile. bg=None draws the mark alone."""
    k = size / 100
    tile = f'<rect x="{x:.3f}" y="{y:.3f}" width="{size:.3f}" height="{size:.3f}" rx="{size * radius:.3f}" fill="{bg}"/>' if bg else ""
    pad = 0.16 if bg else 0.0
    inner = size * (1 - 2 * pad) / 100
    return (tile + f'<path transform="translate({x + size * pad:.3f} {y + size * pad:.3f}) scale({inner:.5f})" '
            f'd="{mark_path()}" fill="{color}" fill-rule="nonzero"/>')


def favicon_svg():
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">{mark(0, 0, 100)}</svg>'


def wordmark(x, y, size, fill="#ffffff", anchor="start"):
    return text("fontworks", x, y, size, "RoundBold", fill, tracking=-0.01, anchor=anchor)


# ---------------------------------------------------------------- film fields
def field(w, h, scene="haze", seed=4, grain=16.0):
    """A grainy, out-of-focus landscape made from noise: no photographs used.
    scene: 'haze' (wild grass and pale flowers under a hazy sky) or 'meadow' (olive hills in mist).
    Returns an RGB numpy array."""
    import numpy as np
    import cv2
    rng = np.random.default_rng(seed)
    yy = np.linspace(0, 1, h)[:, None]
    img = np.zeros((h, w, 3), np.float32)
    hex2 = lambda c: np.array([int(c[i:i + 2], 16) for i in (5, 3, 1)], np.float32)  # noqa: E731  (BGR)
    if scene == "haze":
        horizon = 0.36
        sky = hex2(SKY) * (1 - yy * 0.3) + hex2(CREAM) * (yy * 0.3)
        img[:] = sky[:, None, :] if sky.ndim == 2 else sky
        ground = np.zeros((h, w, 3), np.float32)
        base = hex2("#3c4a22")
        ground[:] = base
        cols = [hex2("#8a9452"), hex2("#b3a66a"), hex2(MEADOW), hex2("#9fb3b9"), hex2("#4c5626"), hex2("#7b864a")]
        for _ in range(int(w * 0.9)):
            x = rng.uniform(0, w)
            y0 = rng.uniform(horizon * h, h)
            ln = rng.uniform(0.08, 0.45) * h
            c = cols[rng.integers(len(cols))] * rng.uniform(0.8, 1.1)
            wd = rng.uniform(2, 9) * (0.6 + (y0 / h))
            cv2.line(ground, (int(x), int(y0 - ln)), (int(x), int(y0)), c.tolist(), int(max(1, wd)))
        for _ in range(int(w / 9)):
            x, y = rng.uniform(0, w), rng.uniform(horizon * h + 0.1 * h, h)
            r = rng.uniform(0.015, 0.06) * w * (y / h)
            c = cols[rng.integers(4)] * rng.uniform(0.85, 1.05)
            cv2.circle(ground, (int(x), int(y)), int(r), c.tolist(), -1)
        ground = cv2.GaussianBlur(ground, (0, 0), sigmaX=w * 0.004, sigmaY=h * 0.03)
        t = np.clip((yy - horizon) / 0.12, 0, 1)[..., None]
        img = img * (1 - t) + ground * t
    else:
        horizon = 0.3
        sky = hex2("#e8e2d6") * (1 - yy) + hex2(SKY) * yy
        img[:] = sky[:, None, :]
        xs = np.linspace(0, 1, w)[None, :]
        layers = [(0.30, "#a9ab8c"), (0.40, "#8b9358"), (0.52, "#6f7a35"), (0.66, "#55601f"), (0.82, "#3b4417")]
        for i, (lvl, col) in enumerate(layers):
            ph = rng.uniform(0, 6.3)
            edge = lvl + 0.05 * np.sin(xs * rng.uniform(3, 7) + ph) + 0.025 * np.sin(xs * rng.uniform(9, 15) + ph * 2)
            m = (yy >= edge).astype(np.float32)[..., None]
            shade = hex2(col) * (1.0 + 0.12 * np.sin(xs * 5 + ph))[..., None]
            img = img * (1 - m) + shade * m
        img = cv2.GaussianBlur(img, (0, 0), w * 0.004)
        haze = np.clip(1 - yy / 0.55, 0, 1)[..., None] * 0.35
        img = img * (1 - haze) + hex2("#eae6dc") * haze
    # soft light leak, vignette and film grain
    xx = np.linspace(-1, 1, w)[None, :]
    yv = np.linspace(-1, 1, h)[:, None]
    vig = 1 - 0.28 * (xx ** 2 + yv ** 2)
    img *= vig[..., None]
    img += rng.normal(0, grain, img.shape).astype(np.float32)
    img += cv2.GaussianBlur(rng.normal(0, grain * 1.4, (h, w)).astype(np.float32), (0, 0), 1.2)[..., None]
    return cv2.cvtColor(np.clip(img, 0, 255).astype(np.uint8), cv2.COLOR_BGR2RGB)


def grain_css(opacity=0.22):
    """A CSS background layer of film grain (SVG noise), for the Studio and pages."""
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence type='fractalNoise' "
           "baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 .9 0'/>"
           f"</filter><rect width='100%' height='100%' filter='url(#n)' opacity='{opacity}'/></svg>")
    return 'url("data:image/svg+xml;utf8,' + svg.replace('"', "'").replace("#", "%23") + '")'


# ---------------------------------------------------------------- terminal + menu
def banner(stage=None, stream=None):
    stream = stream or sys.stdout
    tty = hasattr(stream, "isatty") and stream.isatty()
    red, dim, rst = ("\033[38;2;140;160;80m", "\033[2m", "\033[0m") if tty else ("", "", "")
    line = f"{red}✦ fontworks{rst}  {dim}type foundry  v{VERSION}{rst}"
    if stage:
        line += f"  {dim}/{rst} {stage}"
    print(line, file=stream)


MENU = [
    ("describe", "Describe it", "One sentence about the feeling you want. Get a full family."),
    ("handwriting", "Your handwriting", "Print the sheet, write on it, send a photo. The best photo route."),
    ("quick-photo", "Quick photo", "A photo of any writing or lettering. No sheet needed."),
    ("mood", "Match a mood", "Send a picture you love. Get an original family with that feeling."),
    ("remix", "Remix", "Change a FontWorks font: weight, width, spacing, single letters."),
    ("open", "Open base", "Start from a free font with wide script coverage and reshape it."),
]


def menu_text():
    out = ["✦ fontworks  ·  type foundry", ""]
    for i, (_, title, desc) in enumerate(MENU, 1):
        out.append(f"  {i}  {title:17s} {desc}")
    out += ["", "  Pick a number, or just tell me what you want."]
    return "\n".join(out)


def esc(s):
    return html.escape(str(s))
