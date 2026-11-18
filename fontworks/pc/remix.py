"""Remix route: start from an open-source (SIL OFL) variable font with wide script coverage
and reshape it into a new family.

The result is a derivative under the OFL: it ships with the OFL, credits the original
authors and is renamed (the OFL forbids reusing a Reserved Font Name). The person owns
their changes but not the base design, so the from-scratch route stays the default for
fonts that must be fully owned.
"""
from __future__ import annotations

import copy
import math
import os
import re

# No network in this build. Base fonts must be local files (bundled under
# bases/ or an absolute path the user supplies). See fetch() below.
OFL_URL = "https://openfontlicense.org"
OFL_TEXT = ("This Font Software is licensed under the SIL Open Font License, Version 1.1. "
            "This license is available with a FAQ at: https://openfontlicense.org")

# Directory that ships with the skill, holding OFL base fonts (incl. CJK).
_HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLED = os.path.normpath(os.path.join(_HERE, "..", "bases"))

BASES = {
    "noto-sans-cjk-sc": ("NotoSansSC-VF.ttf", "Noto Sans CJK SC Subset",
                         "3,000 most frequent Chinese characters plus Latin; wght 100-900 (bundled subset)"),
    "roboto-flex": ("robotoflex/RobotoFlex[GRAD,XOPQ,XTRA,YOPQ,YTAS,YTDE,YTFI,YTLC,YTUC,opsz,slnt,wdth,wght].ttf",
                    "Roboto Flex", "grotesque with 13 parametric axes; Latin, Greek, Cyrillic"),
    "noto-sans": ("notosans/NotoSans[wdth,wght].ttf", "Noto Sans",
                  "humanist sans; Latin, Greek, Cyrillic, Vietnamese (3,000+ glyphs)"),
    "noto-serif": ("notoserif/NotoSerif[wdth,wght].ttf", "Noto Serif", "text serif; Latin, Greek, Cyrillic"),
    "noto-sans-mono": ("notosansmono/NotoSansMono[wdth,wght].ttf", "Noto Sans Mono", "monospace for code"),
    "inter": ("inter/Inter[opsz,wght].ttf", "Inter", "screen grotesque with optical sizes"),
    "fraunces": ("fraunces/Fraunces[SOFT,WONK,opsz,wght].ttf", "Fraunces", "soft display serif with a SOFT axis"),
    "recursive": ("recursive/Recursive[CASL,CRSV,MONO,slnt,wght].ttf", "Recursive",
                  "sans to casual, proportional to mono"),
    "noto-sans-devanagari": ("notosansdevanagari/NotoSansDevanagari[wdth,wght].ttf", "Noto Sans Devanagari",
                             "Hindi, Marathi, Nepali, Sanskrit plus Latin"),
    "noto-sans-gujarati": ("notosansgujarati/NotoSansGujarati[wdth,wght].ttf", "Noto Sans Gujarati",
                           "Gujarati plus Latin"),
}

# friendly names for the axes people meet in the Design lab
AXIS_NAMES = {"wght": "Weight", "wdth": "Width", "opsz": "Optical size", "slnt": "Slant", "ital": "Italic",
              "GRAD": "Grade", "XOPQ": "Thick stroke", "YOPQ": "Thin stroke", "XTRA": "Counter width",
              "YTUC": "Cap height", "YTLC": "Lowercase height", "YTAS": "Ascenders", "YTDE": "Descenders",
              "YTFI": "Figure height", "SOFT": "Softness", "WONK": "Wonky", "CASL": "Casual", "CRSV": "Cursive",
              "MONO": "Monospace"}


def fetch(base):
    """Resolve a base font to a LOCAL file. No network access.

    Accepts: an absolute/relative path to an OFL .ttf, or the filename of a
    font bundled under bases/. Never downloads — this build is offline.
    """
    if os.path.exists(base):
        return base
    bundled = os.path.join(BUNDLED, base)
    if os.path.exists(bundled):
        return bundled
    available = sorted(f for f in os.listdir(BUNDLED) if f.endswith(".ttf")) if os.path.isdir(BUNDLED) else []
    raise SystemExit(
        f"base font {base!r} not found. Pass a local OFL .ttf path, or one of the "
        f"bundled fonts: {', '.join(available) or '(none bundled yet)'}. "
        f"This build does not download fonts."
    )


def _base_info(f):
    names = {n.nameID: n.toUnicode() for n in f["name"].names if n.platformID == 3}
    return names.get(1, "the base font"), names.get(0, ""), names.get(13, "")


# ------------------------------------------------------------------ outline transforms
def _shift(f, dx):
    """Add dx units of tracking: widen every advance and centre the outline in it."""
    if not dx:
        return
    glyf, hmtx = f["glyf"], f["hmtx"]
    half = round(dx / 2)
    for name in f.getGlyphOrder():
        g = glyf[name]
        adv, lsb = hmtx[name]
        if adv == 0:          # combining marks keep zero width
            continue
        if g.numberOfContours > 0:
            g.coordinates.translate((half, 0))
        elif g.isComposite():
            for c in g.components:
                c.x += half
        hmtx[name] = (max(0, adv + round(dx)), lsb + half)
    if "gvar" in f:  # outline deltas are relative, so tracking needs no change there
        pass


def _skew(f, deg):
    """Oblique: lean every outline (and every variation delta) by deg degrees."""
    if not deg:
        return
    t = math.tan(math.radians(deg))
    glyf = f["glyf"]
    for name in f.getGlyphOrder():
        g = glyf[name]
        if g.numberOfContours > 0:
            g.coordinates.transform(((1, 0), (t, 1)))
        elif g.isComposite():
            for c in g.components:
                c.x += round(c.y * t)
    if "gvar" in f:
        for name, vs in f["gvar"].variations.items():
            for v in vs:
                v.coordinates = [None if p is None else (p[0] + p[1] * t, p[1]) for p in v.coordinates]
    f["post"].italicAngle = -deg
    f["hhea"].caretSlopeRise, f["hhea"].caretSlopeRun = 1000, round(1000 * t)


def _round_corners(f, amount):
    """Round straight-to-straight corners of a static TrueType font (amount 0..1)."""
    if amount <= 0:
        return 0
    glyf = f["glyf"]
    upm = f["head"].unitsPerEm
    rmax = upm * 0.06 * amount
    n_round = 0
    for name in f.getGlyphOrder():
        g = glyf[name]
        if g.numberOfContours <= 0:
            continue
        coords, flags, ends = list(g.coordinates), list(g.flags), list(g.endPtsOfContours)
        nc, nf, ne, start = [], [], [], 0
        for end in ends:
            pts = coords[start:end + 1]
            fl = [x & 1 for x in flags[start:end + 1]]
            n = len(pts)
            for i in range(n):
                p, on = pts[i], fl[i]
                a, b = pts[i - 1], pts[(i + 1) % n]
                if on and fl[i - 1] and fl[(i + 1) % n] and n > 2:
                    v1 = (a[0] - p[0], a[1] - p[1])
                    v2 = (b[0] - p[0], b[1] - p[1])
                    l1, l2 = math.hypot(*v1), math.hypot(*v2)
                    if l1 > 1 and l2 > 1:
                        cosang = (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)
                        ang = math.degrees(math.acos(max(-1, min(1, cosang))))
                        if ang < 150:
                            r = min(rmax, l1 * 0.45, l2 * 0.45)
                            if r >= 2:
                                p1 = (round(p[0] + v1[0] / l1 * r), round(p[1] + v1[1] / l1 * r))
                                p2 = (round(p[0] + v2[0] / l2 * r), round(p[1] + v2[1] / l2 * r))
                                nc += [p1, p, p2]
                                nf += [1, 0, 1]
                                n_round += 1
                                continue
                nc.append(p)
                nf.append(1 if on else 0)
            ne.append(len(nc) - 1)
            start = end + 1
        from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
        g.coordinates = GlyphCoordinates(nc)
        g.flags = bytearray(nf)
        g.endPtsOfContours = ne
        g.program = None
        from fontTools.ttLib.tables import ttProgram
        g.program = ttProgram.Program()
        g.program.fromBytecode(b"")
    return n_round


def _metrics(f):
    """One line height everywhere: typo = hhea, no line gap, win covers every glyph."""
    hhea, os2, head = f["hhea"], f["OS/2"], f["head"]
    asc, desc = hhea.ascent, hhea.descent
    gap = hhea.lineGap
    asc += gap // 2
    desc -= gap - gap // 2
    hhea.ascent, hhea.descent, hhea.lineGap = asc, desc, 0
    os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = asc, desc, 0
    os2.fsSelection |= 1 << 7
    if os2.version < 4:
        os2.version = 4
    os2.usWinAscent = max(os2.usWinAscent, head.yMax, asc)
    os2.usWinDescent = max(os2.usWinDescent, -head.yMin, -desc)


def _rename(f, fam, style, version, designer, base_name, base_copy, weight=None, variable=False):
    """Give the derivative its own names and the OFL, crediting the original."""
    fid = fam.replace(" ", "")
    name = f["name"]
    name.names = [n for n in name.names if n.nameID > 255]
    ribbi = style in ("Regular", "Bold", "Italic", "Bold Italic")
    fam1 = fam if ribbi else f"{fam} {style}"
    sub = style if ribbi else "Regular"
    cp = (f"{base_copy.strip()} " if base_copy else "") + f"Remix {fam} by {designer or 'its designer'}, based on {base_name}."
    recs = {0: cp, 1: fam1, 2: sub, 3: f"{version};FONTWORKS;{fid}-{style.replace(' ', '')}",
            4: f"{fam} {style}" if style != "Regular" or not variable else fam, 5: f"Version {version}",
            6: f"{fid}-{style.replace(' ', '')}", 11: "https://openfontlicense.org", 13: OFL_TEXT, 14: OFL_URL}
    if designer:
        recs[9] = designer
    if not ribbi:
        recs[16], recs[17] = fam, style
    if variable:
        recs[1], recs[2], recs[4], recs[6] = fam, "Regular", fam, f"{fid}-Regular"
        recs[25] = fid
        recs.pop(16, None)
        recs.pop(17, None)
    for nid, s in recs.items():
        name.setName(s, nid, 3, 1, 0x409)
    if "fvar" in f:
        for inst in f["fvar"].instances:
            inst.postscriptNameID = 0xFFFF
    if weight is not None:
        os2 = f["OS/2"]
        os2.usWeightClass = int(weight)
        os2.fsSelection &= ~((1 << 0) | (1 << 5) | (1 << 6))
        if style == "Bold":
            os2.fsSelection |= 1 << 5
        elif style == "Regular":
            os2.fsSelection |= 1 << 6
        f["head"].macStyle = 1 if style == "Bold" else 0
    f["head"].fontRevision = float(version)


# ------------------------------------------------------------------ the route
def build_remix(spec, out_dir, formats, log):
    from fontTools.ttLib import TTFont
    from fontTools.ttLib.scaleUpem import scale_upem
    from fontTools.varLib import instancer

    from .build import _finish_ttf, _woff2
    from .presets import WEIGHT_NAME

    fam = spec["family"]
    fid = fam.replace(" ", "")
    rx = spec.get("remix", {})
    base_key = spec.get("base") or rx.get("base") or "NotoSansSC-VF.ttf"
    version = str(spec.get("version", "1.000"))
    designer = spec.get("designer", "")

    log.stage("Base font")
    path = fetch(base_key)
    vf = TTFont(path)
    base_name, base_copy, _ = _base_info(vf)
    reserved = re.findall(r"Reserved Font Name\s+['\"]([^'\"]+)['\"]", base_copy or "")
    for rfn in reserved:
        if rfn.strip().lower() in fam.lower():
            raise SystemExit(
                f"family name {fam!r} contains the base font's Reserved Font Name {rfn!r}. "
                "Choose a different name: the OFL forbids reusing a reserved name in a derivative."
            )
    if "fvar" not in vf or "glyf" not in vf:
        raise SystemExit("remix needs a TrueType variable font (most open-source families on Google Fonts are)")
    if vf["head"].unitsPerEm != 1000:
        scale_upem(vf, 1000)
    axes = {a.axisTag: a for a in vf["fvar"].axes}
    log.note(f"{base_name}: {len(vf.getGlyphOrder())} glyphs, {len(vf.getBestCmap())} characters, "
             f"axes {', '.join(axes)} (SIL Open Font License)")

    def clamp(tag, v):
        a = axes[tag]
        return max(a.minValue, min(a.maxValue, float(v)))

    fixed = {t: clamp(t, v) for t, v in rx.get("axes", {}).items() if t in axes and t != "wght"}
    weights = sorted(int(w) for w in spec.get("weights", [400, 700]))
    if "wght" in axes:
        weights = sorted({int(clamp("wght", w)) for w in weights})
    track = float(rx.get("tracking", 0))
    slant = float(rx.get("slant", 0))
    rnd = float(rx.get("round", 0))
    log.note("settings: " + ", ".join([f"{t} {v:g}" for t, v in fixed.items()] +
                                      ([f"tracking {track:+g}"] if track else []) + ([f"slant {slant:g}°"] if slant else []) +
                                      ([f"corner rounding {rnd:g}"] if rnd else [])) if (fixed or track or slant or rnd) else "settings: base defaults")

    log.stage("Instances")
    fonts = os.path.join(out_dir, "fonts")
    for d in ("ttf", "webfonts", "variable"):
        os.makedirs(os.path.join(fonts, d), exist_ok=True)
    made = []
    for w in weights:
        loc = dict(fixed)
        if "wght" in axes:
            loc["wght"] = w
        # pin every axis: unlisted ones sit at the base default
        for t, a in axes.items():
            loc.setdefault(t, a.defaultValue)
        f = instancer.instantiateVariableFont(copy.deepcopy(vf), loc)
        _shift(f, track)
        _skew(f, slant)
        nr = _round_corners(f, rnd)
        f["head"].yMax = max(f["glyf"][g].yMax for g in f.getGlyphOrder() if f["glyf"][g].numberOfContours)
        f["head"].yMin = min(f["glyf"][g].yMin for g in f.getGlyphOrder() if f["glyf"][g].numberOfContours)
        _metrics(f)
        style = WEIGHT_NAME.get(w, str(w))
        _rename(f, fam, style, version, designer, base_name, base_copy, weight=w)
        p = os.path.join(fonts, "ttf", f"{fid}-{style}.ttf")
        f.save(p)
        _finish_ttf(p)
        made.append(p)
        log.note(f"{style} {w}: {len(f.getGlyphOrder())} glyphs" + (f", {nr} corners rounded" if nr else ""))

    variable = False
    flex = None
    if "variable" in formats and rnd == 0 and "wght" in axes and len(weights) > 1:
        log.stage("Variable fonts")
        # a weight-only font for everyday use: every other axis pinned to the chosen design
        pin = {t: fixed.get(t, a.defaultValue) for t, a in axes.items() if t != "wght"}
        pin["wght"] = (weights[0], clamp("wght", 400) if weights[0] <= 400 <= weights[-1] else weights[0], weights[-1])
        wf = instancer.instantiateVariableFont(copy.deepcopy(vf), pin)
        _shift(wf, track)
        _skew(wf, slant)
        _metrics(wf)
        _rename(wf, fam, "Regular", version, designer, base_name, base_copy, variable=True)
        p = os.path.join(fonts, "variable", f"{fid}[wght].ttf")
        wf.save(p)
        _finish_ttf(p)
        made.append(p)
        variable = True
        # the whole design space for the Design lab
        ff = copy.deepcopy(vf)
        _shift(ff, track)
        _skew(ff, slant)
        _metrics(ff)
        _rename(ff, f"{fam} Flex", "Regular", version, designer, base_name, base_copy, variable=True)
        tags = [a.axisTag for a in ff["fvar"].axes]
        p = os.path.join(fonts, "variable", f"{fid}Flex[{','.join(tags)}].ttf")
        ff.save(p)
        made.append(p)
        flex = dict(file=os.path.basename(p), remix=True,
                    axes=[[a.axisTag, AXIS_NAMES.get(a.axisTag, a.axisTag), a.minValue,
                           fixed.get(a.axisTag, a.defaultValue) if a.axisTag != "wght" else clamp("wght", 400),
                           a.maxValue] for a in ff["fvar"].axes])
        log.note(f"{os.path.basename(made[-2])} and a {len(tags)}-axis lab font")

    if "woff2" in formats:
        for p in list(made):
            if p.endswith(".ttf"):
                dst = os.path.join(fonts, "webfonts", os.path.basename(p)[:-4] + ".woff2")
                _woff2(p, dst)
                made.append(dst)
    ofl_path = os.path.normpath(os.path.join(_HERE, "..", "..", "OFL.txt"))
    full_ofl = open(ofl_path).read() if os.path.exists(ofl_path) else OFL_TEXT
    with open(os.path.join(fonts, "OFL.txt"), "w") as fh:
        fh.write(f"{base_copy}\n\nThis remix ({fam}) is a modified version of {base_name}, released under the same license.\n\n"
                 f"{full_ofl}\n")
    for p in made:
        log.note(f"{os.path.relpath(p, out_dir)}  {os.path.getsize(p) / 1024:.0f} KB")

    spec = dict(spec)
    spec.setdefault("license", "SIL Open Font License 1.1")
    spec.setdefault("license_url", OFL_URL)
    spec.setdefault("description", f"A remix of {base_name} ({BASES.get(base_key, ('', '', 'open-source'))[2]}).")
    design = dict(base=base_key, base_name=base_name, axes=fixed, tracking=track, slant=slant, round=rnd)
    return dict(family=fam, family_id=fid, out=out_dir, fonts=made, weights=weights,
                masters=[weights[0], weights[-1]], variable=variable, design=design, spec=spec, log=log,
                flex=flex, remix=True)
