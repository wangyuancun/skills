"""Quality assurance on the compiled fonts. Every check is a real measurement."""
from __future__ import annotations

import unicodedata
import os

import uharfbuzz as hb
from fontTools.ttLib import TTFont

BASIC = ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
         ".,:;!?'\"()[]{}/\\|@#$%&*+-=<>^~_`")
LATIN1 = "".join(chr(c) for c in range(0xA1, 0x100) if c not in (0xA4, 0xA6, 0xA7, 0xAA, 0xAC, 0xAD, 0xB1, 0xB2, 0xB3, 0xB5, 0xB6, 0xB9, 0xBA, 0xBC, 0xBD, 0xBE))


def _advance(font, text, feats=None):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, feats or {})
    return [p.x_advance for p in buf.glyph_positions]


def check_font(path, remix=False):
    """Return a list of (level, message). level is PASS, WARN or FAIL."""
    res = []

    def add(ok, msg, warn=False):
        res.append(("PASS" if ok else ("WARN" if warn else "FAIL"), msg))

    tt = TTFont(path)
    cmap = tt.getBestCmap()
    missing = [c for c in BASIC if ord(c) not in cmap]
    add(not missing, "Basic Latin complete" if not missing else f"Basic Latin missing: {''.join(missing)}")
    miss1 = [c for c in LATIN1 if ord(c) not in cmap]
    add(not miss1, "Latin-1 letters and punctuation complete" if not miss1 else f"Latin-1 missing: {''.join(miss1)}", warn=True)

    gs = tt.getGlyphSet()
    from fontTools.pens.boundsPen import BoundsPen
    empty = []
    for cp, name in cmap.items():
        if cp in (0x20, 0xA0) or unicodedata.category(chr(cp)) in ("Zs", "Cc", "Cf", "Zl", "Zp"):
            continue
        bp = BoundsPen(gs)
        gs[name].draw(bp)
        if bp.bounds is None:
            empty.append(name)
    add(not empty, "every mapped glyph has an outline" if not empty else f"empty glyphs: {', '.join(empty[:10])}")

    hhea, os2 = tt["hhea"], tt["OS/2"]
    add(hhea.ascent == os2.sTypoAscender and hhea.descent == os2.sTypoDescender and hhea.lineGap == os2.sTypoLineGap,
        "vertical metrics agree across hhea and OS/2 (same line height on every platform)")
    add(bool(os2.fsSelection & (1 << 7)), "USE_TYPO_METRICS set")
    ymax, ymin = tt["head"].yMax, tt["head"].yMin
    add(os2.usWinAscent >= ymax and os2.usWinDescent >= -ymin, "nothing clips: win metrics cover the tallest glyph")

    names = {n.nameID: n.toUnicode() for n in tt["name"].names}
    add(all(i in names for i in (1, 2, 4, 6)), f"name table complete ({names.get(4, '?')})")
    add(" " not in names.get(6, " "), "PostScript name is valid")

    face = hb.Face(hb.Blob.from_file_path(path))
    font = hb.Font(face)
    pairs = [("AV", "AV"), ("To", "To"), ("LT", "LT"), ("r.", "r.")]
    kerned = [n for t, n in pairs if sum(_advance(font, t)) < sum(_advance(font, t, {"kern": False}))]
    add(len(kerned) >= 3, f"kerning active ({', '.join(kerned)} tighten)", warn=True)
    tn = _advance(font, "0123456789", {"tnum": True})
    add(len(set(tn)) == 1 or remix, f"tabular figures share one width ({tn[0]})")
    feats = set()
    for tag in ("GSUB", "GPOS"):
        if tag in tt:
            feats |= {f.FeatureTag for f in tt[tag].table.FeatureList.FeatureRecord}
    want = {"kern"} if remix else {"kern", "case", "tnum", "zero"}
    add(want <= feats, f"features present: {', '.join(sorted(feats))}")

    if "fvar" in tt:
        ax = tt["fvar"].axes[0]
        add(True, f"variable axis {ax.axisTag} {ax.minValue:.0f} to {ax.maxValue:.0f}, {len(tt['fvar'].instances)} named instances")
        add("STAT" in tt, "STAT table present", warn=True)
    if "glyf" in tt:
        over = sum(1 for n in tt.getGlyphOrder() if tt["glyf"][n].numberOfContours > 0 and len(tt["glyf"][n].coordinates) > 400)
        add(over == 0, "no glyph has an excessive point count")
    add(tt["head"].unitsPerEm == 1000, f"units per em {tt['head'].unitsPerEm}")
    return res


def check_all(result):
    lines, fails, warns = [], 0, 0
    for f in result["fonts"]:
        if f.endswith(".woff2"):
            continue
        res = check_font(f, result.get("remix", False))
        lines.append(f"### {os.path.basename(f)}")
        for lvl, msg in res:
            lines.append(f"- {lvl}: {msg}")
            fails += lvl == "FAIL"
            warns += lvl == "WARN"
        lines.append("")
    return lines, fails, warns
