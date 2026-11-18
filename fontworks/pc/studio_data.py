"""Everything the Studio knows about a family, measured from the font files.

Outlines with every point, metrics, kerning pairs, language coverage, file
sizes. Kept apart from the page template so the numbers can be tested.
"""
from __future__ import annotations

import os
import unicodedata

# Latin-script languages and the letters each needs beyond a to z.
LANGUAGES = [
    ("English", ""), ("Afrikaans", "êëîïôû"), ("Albanian", "çë"), ("Basque", "ñ"), ("Catalan", "àçéèíïòóúü"),
    ("Croatian", "čćđšž"), ("Czech", "áčďéěíňóřšťúůýž"), ("Danish", "æøå"), ("Dutch", "éëïóöü"),
    ("Esperanto", "ĉĝĥĵŝŭ"), ("Estonian", "äõöüšž"), ("Faroese", "áæðíóøúý"), ("Filipino", "ñ"),
    ("Finnish", "äöå"), ("French", "àâæçéèêëîïôœùûüÿ"), ("Galician", "áéíñóú"), ("German", "äöüß"),
    ("Hungarian", "áéíóöőúüű"), ("Icelandic", "áæðéíóöúýþ"), ("Indonesian", ""), ("Irish", "áéíóú"),
    ("Italian", "àèéìíîòóùú"), ("Latvian", "āčēģīķļņšūž"), ("Lithuanian", "ąčęėįšųūž"), ("Luxembourgish", "äéë"),
    ("Malay", ""), ("Maltese", "ċġħż"), ("Norwegian", "æøåéèêóòô"), ("Polish", "ąćęłńóśźż"),
    ("Portuguese", "àáâãçéêíóôõú"), ("Romanian", "ăâîșț"), ("Slovak", "áäčďéíĺľňóôŕšťúýž"),
    ("Slovenian", "čšž"), ("Spanish", "áéíñóúü¡¿"), ("Swahili", ""), ("Swedish", "åäöé"),
    ("Turkish", "çğıöşü"), ("Welsh", "âêîôûŵŷäëïöüÿáéíóúẁẃẅỳý"), ("Zulu", ""), ("Xhosa", ""),
    ("Somali", ""), ("Hausa (Boko, basic)", ""), ("Yoruba (basic)", "ẹọṣ"), ("Vietnamese (basic)", "ăâđêôơư"),
]


def category(ch):
    c = unicodedata.category(ch)
    if c == "Lu":
        return "upper"
    if c == "Ll":
        return "lower"
    if c == "Nd":
        return "figures"
    if c.startswith("P"):
        return "punctuation"
    if c.startswith("L") or c.startswith("M"):
        return "letters"
    return "symbols"


def _accented(ch):
    d = unicodedata.normalize("NFD", ch)
    return len(d) > 1 and d[0].isalpha()


def outlines(ttf, cmap_names):
    """{glyph name: [path d, points [[x,y,on],...], bounds]} in font units (y up)."""
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    from fontTools.ttLib import TTFont
    f = TTFont(ttf)
    gs = f.getGlyphSet()
    out = {}
    for name in cmap_names:
        if name not in gs:
            continue
        rec = DecomposingRecordingPen(gs)
        gs[name].draw(rec)
        d, pts = [], []
        for op, args in rec.value:
            if op == "moveTo":
                (x, y), = args
                d.append(f"M{x:.0f} {y:.0f}")
                pts.append([round(x), round(y), 2])   # 2: first point of a contour
            elif op == "lineTo":
                (x, y), = args
                d.append(f"L{x:.0f} {y:.0f}")
                pts.append([round(x), round(y), 1])
            elif op == "qCurveTo":
                ps = list(args)
                # implied on-curve points between consecutive off-curve points
                for i, (x, y) in enumerate(ps[:-1]):
                    pts.append([round(x), round(y), 0])
                    nx, ny = ps[i + 1]
                    if i < len(ps) - 2:
                        mx, my = (x + nx) / 2, (y + ny) / 2
                        d.append(f"Q{x:.0f} {y:.0f} {mx:.0f} {my:.0f}")
                    else:
                        d.append(f"Q{x:.0f} {y:.0f} {nx:.0f} {ny:.0f}")
                last = ps[-1]
                if last is not None:
                    pts.append([round(last[0]), round(last[1]), 1])
            elif op == "curveTo":
                (a, b, c) = args
                d.append(f"C{a[0]:.0f} {a[1]:.0f} {b[0]:.0f} {b[1]:.0f} {c[0]:.0f} {c[1]:.0f}")
                pts += [[round(a[0]), round(a[1]), 0], [round(b[0]), round(b[1]), 0], [round(c[0]), round(c[1]), 1]]
            elif op in ("closePath", "endPath"):
                d.append("Z")
        out[name] = ["".join(d), pts]
    return out


def kern_pairs(ttf, limit=600):
    """The strongest kerning pairs among letters, figures and common punctuation."""
    import uharfbuzz as hb
    blob = hb.Blob.from_file_path(ttf)
    font = hb.Font(hb.Face(blob))
    chars = [c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,-:;'\"()?!"
             if font.get_nominal_glyph(ord(c))]

    def adv(s, kern):
        buf = hb.Buffer()
        buf.add_str(s)
        buf.guess_segment_properties()
        hb.shape(font, buf, {"kern": kern})
        return sum(p.x_advance for p in buf.glyph_positions)

    single = {c: adv(c, False) for c in chars}
    out = []
    for a in chars:
        for b in chars:
            k = adv(a + b, True) - single[a] - single[b]
            if k:
                out.append([a + b, int(k)])
    out.sort(key=lambda p: -abs(p[1]))
    return out[:limit], len(out)


def languages(cmap):
    have = {chr(c) for c in cmap}
    res = []
    for name, extra in LANGUAGES:
        need = set("abcdefghijklmnopqrstuvwxyz") | set(extra) | {c.upper() for c in extra if c.upper() != c and len(c.upper()) == 1}
        missing = sorted(need - have)
        res.append([name, not missing, "".join(missing[:8])])
    return res


def file_list(fonts_dir):
    out = []
    for root, _, files in os.walk(fonts_dir):
        for fn in sorted(files):
            if fn == "studio.html":
                continue
            full = os.path.join(root, fn)
            out.append([os.path.relpath(full, fonts_dir).replace(os.sep, "/"), os.path.getsize(full)])
    order = {"variable": 0, "ttf": 1, "otf": 2, "webfonts": 3}
    out.sort(key=lambda f: (order.get(f[0].split("/")[0], 9), f[0]))
    return out


def measure(ttfs):
    """ttfs: {weight: path}. Returns the Studio's data block for the glyphs."""
    from fontTools.ttLib import TTFont
    first = next(iter(ttfs.values()))
    f = TTFont(first)
    cmap = f.getBestCmap()
    hmtx = f["hmtx"]
    glyf = f["glyf"] if "glyf" in f else None
    rows = []
    names = []
    for cp, name in sorted(cmap.items()):
        if cp <= 0x20 or cp == 0xA0:
            continue
        ch = chr(cp)
        try:
            uname = unicodedata.name(ch).title()
        except ValueError:
            uname = name
        cat = "accented" if _accented(ch) else category(ch)
        adv, lsb = hmtx[name]
        b = None
        if glyf is not None and name in glyf:
            g = glyf[name]
            g.recalcBounds(glyf)
            if g.numberOfContours != 0:
                b = [g.xMin, g.yMin, g.xMax, g.yMax]
        rows.append([ch, f"U+{cp:04X}", uname, adv, cat, name, b])
        names.append(name)
    # outlines for the inspector: the regular and the heaviest weight keep the page light
    first_w, heavy_w = next(iter(ttfs)), max(ttfs)
    shapes = {w: outlines(p, names) for w, p in ttfs.items() if w in (first_w, heavy_w)}
    os2 = f["OS/2"]
    metrics = dict(upm=f["head"].unitsPerEm, asc=os2.sTypoAscender, desc=os2.sTypoDescender,
                   cap=getattr(os2, "sCapHeight", 700), xh=getattr(os2, "sxHeight", 500),
                   win=[os2.usWinAscent, os2.usWinDescent], gap=os2.sTypoLineGap, glyphs=len(f.getGlyphOrder()))
    feats = set()
    for tag in ("GSUB", "GPOS"):
        if tag in f:
            feats |= {r.FeatureTag for r in f[tag].table.FeatureList.FeatureRecord}
    pairs, npairs = kern_pairs(first)
    return dict(glyphs=rows, shapes=shapes, metrics=metrics, features=sorted(feats), kern=pairs,
                kern_total=npairs, languages=languages(cmap))
