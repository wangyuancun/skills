"""The foundry pipeline: spec -> drawings -> spacing -> kerning -> features -> font files."""
from __future__ import annotations

import datetime
import json
import math
import os
import runpy
import shutil
import subprocess
import sys
import unicodedata

import numpy as np

from . import glyphs_latin, glyphs_extra  # noqa: F401  (registers the glyphs)
from .context import DEFAULTS, G, Shape
from .geometry import polygon
from .glyphs_latin import GLYPHS
from .presets import PRESETS, WEIGHT_NAME, WEIGHT_STEM
from .spacing import KernProfile, bounds, kern_pair, sidebearings

FIGS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
CASE_PUNCT = ["parenleft", "parenright", "bracketleft", "bracketright", "braceleft", "braceright",
              "endash", "emdash", "guilsinglleft", "guilsinglright", "guillemetleft", "guillemetright",
              "exclamdown", "questiondown", "periodcentered", "bullet"]
NO_KERN_CASES = ("fig", "accent", "sym")


class Log:
    def __init__(self, quiet=False):
        self.quiet = quiet
        self.n = 0
        self.report = []

    def stage(self, title):
        self.n += 1
        self.report.append({"stage": title, "notes": []})
        if not self.quiet:
            print(f"\n[{self.n}] {title}")

    def note(self, text):
        self.report[-1]["notes"].append(text)
        if not self.quiet:
            print(f"      {text}")


# ------------------------------------------------------------------ spec
def load_spec(path):
    with open(path) as f:
        spec = json.load(f)
    spec["_dir"] = os.path.dirname(os.path.abspath(path))
    return spec


def resolve_design(spec):
    design = dict(DEFAULTS)
    preset = spec.get("preset")
    if preset:
        if preset not in PRESETS:
            raise SystemExit(f"Unknown preset '{preset}'. Choose from: {', '.join(PRESETS)}")
        design.update(PRESETS[preset])
    unknown = [k for k in spec.get("design", {}) if k not in DEFAULTS]
    if unknown:
        raise SystemExit(f"Unknown design parameter(s): {', '.join(unknown)}. See references/parameters.md")
    design.update(spec.get("design", {}))
    return design


def master_designs(spec, design, traced=None):
    """Return {wght: design dict}. Explicit masters win; otherwise masters are
    derived from the Regular design for the lightest and heaviest weight."""
    weights = sorted(int(w) for w in spec.get("weights", [400]))
    if traced:
        out = {}
        for w, t in sorted(traced["weights"].items(), key=lambda kv: int(kv[0])):
            d = dict(design)
            d["stem"] = t["stem"]
            out[int(w)] = d
        return out, sorted(out)
    explicit = spec.get("masters")
    if explicit:
        out = {}
        for w, over in explicit.items():
            d = dict(design)
            d.update(over)
            out[int(w)] = d
        return dict(sorted(out.items())), weights
    locs = sorted({weights[0], weights[-1]} | ({400} if weights[0] < 400 < weights[-1] else set()))
    out = {}
    for w in locs:
        m = WEIGHT_STEM[w]
        d = dict(design)
        d["stem"] = design["stem"] * m
        # heavy weights thin their horizontals and joins to keep counters open
        d["hratio"] = min(max(design["hratio"] - 0.1 * (m - 1), 0.7), 0.98)
        d["join"] = min(max(design["join"] - 0.14 * (m - 1), 0.5), 0.92)
        d["overshoot"] = design["overshoot"]
        out[w] = d
    return out, weights


def load_overrides(spec):
    """Run the spec's custom glyph file, which may redefine any glyph."""
    path = spec.get("glyphs")
    if not path:
        return []
    full = path if os.path.isabs(path) else os.path.join(spec["_dir"], path)
    before = {k: v[0] for k, v in GLYPHS.items()}
    runpy.run_path(full, init_globals={"glyph": glyphs_latin.glyph, "L": glyphs_latin, "X": glyphs_extra})
    return sorted(k for k, v in GLYPHS.items() if before.get(k) is not v[0])


# ------------------------------------------------------------------ master
class Glyph:
    def __init__(self, name, uni, case):
        self.name, self.uni, self.case = name, uni, case
        self.contours, self.components = [], []
        self.advance = 0.0
        self.center = 0.0


def _move(contours, dx, dy=0.0):
    return [c.transformed(lambda p: (p[0] + dx, p[1] + dy)) for c in contours]


def _traced_glyph(name, design, traced, case):
    """Contours for a glyph that came from a photo, or None."""
    from .handwriting import contours_from_json
    if name in traced:
        return contours_from_json(traced[name]["contours"])
    base = {"dotlessi": "i", "dotlessj": "j"}.get(name)
    if base and base in traced:
        cons = contours_from_json(traced[base]["contours"])
        # drop the dot: contours that sit entirely above the x-height
        keep = [c for c in cons if (bounds([c]) or (0, 0, 0, 0))[1] < design["xh"] * 0.9]
        return keep or cons
    if name == "zero.zero" and "zero" in traced:
        cons = contours_from_json(traced["zero"]["contours"])
        b = bounds(cons)
        g = G(design, "fig")
        w, h = b[2] - b[0], b[3] - b[1]
        g.add(g.P(0.8).m(b[0] + w * 0.3, b[1] + h * 0.22).l(b[0] + w * 0.7, b[1] + h * 0.78), "round", "round")
        return cons + g.shape.contours
    return None


def draw_master(design, log=None, traced=None):
    glyphs = {}
    traced = traced or {}
    g0 = G(design)
    s, xh, cap = design["stem"], design["xh"], design["cap"]
    counter = g0.nw - 2 * s
    base = max(0.30 * counter - 0.10 * s, s * 0.3) * design["spacing"]
    target = {"lc": base, "uc": base * 1.25, "fig": base * 1.22, "punct": base * 0.8, "sym": base * 0.95, "accent": base * 0.7}
    depth = xh * 0.115

    filled = []
    for name, (fn, uni, case) in GLYPHS.items():
        g = G(design, case)
        if traced:
            if name.endswith(".ss01"):
                continue  # one form of each letter from the writer; no engine alternates
            cons = _traced_glyph(name, design, traced, case)
            if cons:
                g.shape.contours = cons
            else:
                fn(g)
                if case in ("lc", "uc", "fig", "punct", "sym"):
                    filled.append(name)
        else:
            fn(g)
        gl = Glyph(name, uni, case)
        b = bounds(g.shape.contours)
        if b is None:
            raise RuntimeError(f"glyph '{name}' drew nothing")
        if case == "accent":
            gl.contours, gl.center = _move(g.shape.contours, -b[0] + target[case]), -b[0] + target[case]
            gl.advance = (b[2] - b[0]) + 2 * target[case]
        else:
            if case in ("lc", "uc", "fig"):
                zone = (0, xh) if case == "lc" else (0, cap)
                shift, adv = sidebearings(g.shape.contours, zone, target[case], depth)
            else:  # punctuation and symbols: plain sidebearings from the bounding box
                shift, adv = target[case] - b[0], (b[2] - b[0]) + 2 * target[case]
            gl.contours, gl.advance = _move(g.shape.contours, shift), adv
            gl.center = (b[0] + b[2]) / 2 + shift
        glyphs[name] = gl

    # fixed-width glyphs
    sp = Glyph("space", 0x20, "space")
    sp.advance = (g0.nw * 0.5 + base * 0.6)
    glyphs["space"] = sp
    nb = Glyph("nbspace", 0xA0, "space")
    nb.advance = sp.advance
    glyphs["nbspace"] = nb

    # tabular figures: one shared width, each figure centred
    tw = max(glyphs[f].advance for f in FIGS)
    for f in FIGS + ["zero.zero"]:
        src = glyphs[f]
        t = Glyph(f + ".tf", None, "fig")
        t.contours, t.advance = _move(src.contours, (tw - src.advance) / 2), tw
        glyphs[t.name] = t

    # accented letters
    cmap = {gl.uni: gl.name for gl in glyphs.values() if gl.uni}
    from fontTools.agl import UV2AGL
    made = 0
    extra = [0x1E80, 0x1E81, 0x1E82, 0x1E83, 0x1E84, 0x1E85, 0x1EF2, 0x1EF3,      # Welsh w and y
             0x218, 0x219, 0x21A, 0x21B,                                          # Romanian s and t comma
             0x1EB8, 0x1EB9, 0x1ECC, 0x1ECD, 0x1E62, 0x1E63]                      # Yoruba dot below
    for cp in list(range(0xC0, 0x180)) + extra:
        if cp in cmap:
            continue
        dec = unicodedata.normalize("NFD", chr(cp))
        if len(dec) != 2 or ord(dec[1]) not in glyphs_extra.MARKS or ord(dec[0]) not in cmap:
            continue
        bch, mark = dec[0], glyphs_extra.MARKS[ord(dec[1])]
        if mark == "cedilla" and bch in "GKLNRgklnr":
            mark = "commaturnedabove" if bch == "g" else "commaaccentcomb"   # Latvian uses a comma
        elif mark == "cedilla" and bch not in "CcSsTt":
            continue
        vert = mark == "caron" and bch in "dltL"
        if vert:
            mark = "caronvert"
        if mark not in glyphs:
            continue
        variants = [("", cmap[ord(bch)])]
        if bch == "a" and "a.ss01" in glyphs:
            variants.append((".ss01", "a.ss01"))
        for suffix, bname in variants:
            draw_base = {"i": "dotlessi", "j": "dotlessj"}.get(bch, bname) if mark not in glyphs_extra.BELOW else bname
            if bch == "i" and mark == "ogonek":
                draw_base = bname
            bg, mg = glyphs[draw_base], glyphs[mark]
            dx = bg.center - mg.center
            adv = bg.advance
            if mark in glyphs_extra.BELOW:
                dy = 0.0
                if mark == "ogonek":   # hangs from the right foot of the letter
                    bb, mb = bounds(bg.contours), bounds(mg.contours)
                    dx = (bb[2] - s * 0.55) - mb[0] if bb and mb else dx
            elif vert:
                bb, mb = bounds(bg.contours), bounds(mg.contours)
                top = cap if bch == "L" else design["asc"]
                if bch == "L":
                    x = bb[0] + s * 1.5
                elif bch == "t":
                    x = bb[2] - s * 0.1
                else:
                    x = bb[2] + s * 0.45
                dx, dy = x - mb[0], top - mb[3]
                if bch in "dl":
                    adv += max(0.0, (x + (mb[2] - mb[0])) - bb[2]) * 0.8
            elif bch.isupper():
                dy = cap - xh
            elif bch in "bdfhklt":
                dy = design["asc"] - xh
            else:
                dy = 0.0
            name = UV2AGL.get(cp, "uni%04X" % cp) + suffix
            c = Glyph(name, None if suffix else cp, "uc" if bch.isupper() else "lc")
            c.components = [(draw_base, 0.0, 0.0), (mark, dx, dy)]
            c.advance, c.center = adv, bg.center
            glyphs[name] = c
            made += 1

    nd = Glyph(".notdef", None, "space")
    w, t = cap * 0.6, s * 0.7
    nd.contours = [polygon([(60, 0), (60 + w, 0), (60 + w, cap), (60, cap)]),
                   polygon([(60 + t, t), (60 + w - t, t), (60 + w - t, cap - t), (60 + t, cap - t)]).reversed()]
    nd.advance = w + 120
    glyphs[".notdef"] = nd
    return glyphs, dict(target=target, composites=made, tab=tw, filled=filled)


def flat_contours(glyphs, gl):
    out = list(gl.contours)
    for base, dx, dy in gl.components:
        out.extend(_move(flat_contours(glyphs, glyphs[base]), dx, dy))
    return out


# ------------------------------------------------------------------ kerning
def kern_names(glyphs):
    return [n for n, gl in glyphs.items()
            if gl.case in ("lc", "uc", "punct") and not n.endswith(".tf") and n != ".notdef"]


def kern_matrix(glyphs, names, design, nn_gap):
    ys = np.arange(design["desc"] - 30 + 7.0, design["asc"] + 260, 22.0)
    profs = [KernProfile(flat_contours(glyphs, glyphs[n]), glyphs[n].advance, ys) for n in names]
    n = len(names)
    K = np.zeros((n, n))
    d_air, d_touch = nn_gap * 0.62, nn_gap * 0.28
    strength = design["kerning"]
    for i, a in enumerate(profs):
        for j, b in enumerate(profs):
            k = kern_pair(a, b, d_air, d_touch, 0.34)
            K[i, j] = k * (0.86 * strength if k < 0 else 1.0)
    return K


def kern_classes(names, mats, threshold=14):
    """Zero out small values, then merge glyphs that kern identically."""
    keep = np.max(np.abs(np.stack(mats)), axis=0) >= threshold
    mats = [np.round(np.where(keep, m, 0.0) / 2) * 2 for m in mats]

    def classes(rows):
        seen, out = {}, []
        for i, key in enumerate(rows):
            if key not in seen:
                seen[key] = len(out)
                out.append([])
            out[seen[key]].append(i)
        return out

    first = classes([b"".join(m[i].tobytes() for m in mats) for i in range(len(names))])
    red = [m[[c[0] for c in first], :] for m in mats]
    second = classes([b"".join(m[:, j].tobytes() for m in red) for j in range(len(names))])
    return mats, first, second


def kerning_tables(names, mats, first, second):
    groups = {}

    def ref(cls, side):
        if len(cls) == 1:
            return names[cls[0]]
        gname = f"public.kern{side}.{names[cls[0]]}"
        groups[gname] = [names[i] for i in cls]
        return gname

    f_ref = [ref(c, 1) for c in first]
    s_ref = [ref(c, 2) for c in second]
    tables = []
    for m in mats:
        t = {}
        for a, ca in enumerate(first):
            for b, cb in enumerate(second):
                v = m[ca[0], cb[0]]
                if v:
                    t[(f_ref[a], s_ref[b])] = int(v)
        tables.append(t)
    # every master must carry the same pairs
    keys = set().union(*[t.keys() for t in tables])
    for t in tables:
        for k in keys:
            t.setdefault(k, 0)
    return groups, tables


# ------------------------------------------------------------------ features
def features(glyphs, design):
    cap, xh = design["cap"], design["xh"]
    lift = round((cap - xh) / 2)
    figs = " ".join(FIGS)
    figs_tf = " ".join(f + ".tf" for f in FIGS)
    a_alts = sorted(n for n in glyphs if n.endswith(".ss01"))
    a_from = " ".join(n[:-5] for n in a_alts)
    a_to = " ".join(a_alts)
    case = " ".join(n for n in CASE_PUNCT if n in glyphs)
    ss01 = f"""
feature ss01 {{
    featureNames {{ name "Alternate a"; }};
    sub [{a_from}] by [{a_to}];
}} ss01;
""" if a_alts else ""
    return f"""languagesystem DFLT dflt;
languagesystem latn dflt;

@figures = [{figs}];
@figures_tf = [{figs_tf}];

feature case {{
    sub hyphen by hyphen.case;
    pos [{case}] <0 {lift} 0 0>;
}} case;

feature tnum {{
    sub @figures by @figures_tf;
    sub zero.zero by zero.zero.tf;
}} tnum;

feature zero {{
    sub zero by zero.zero;
    sub zero.tf by zero.zero.tf;
}} zero;
{ss01}"""


# ------------------------------------------------------------------ UFO output
def write_ufo(path, glyphs, design, spec, style, wght, groups, kerning, fea):
    import ufoLib2
    font = ufoLib2.Font()
    info = font.info
    fam = spec["family"]
    tan = math.tan(math.radians(design["slant"]))
    year = datetime.date.today().year
    info.familyName, info.styleName = fam, style
    info.unitsPerEm = design["upm"]
    info.ascender, info.descender = design["asc"], design["desc"]
    info.xHeight, info.capHeight = design["xh"], design["cap"]
    info.italicAngle = -design["slant"]
    info.versionMajor, info.versionMinor = [int(x) for x in str(spec.get("version", "1.000")).split(".")][:2]
    info.openTypeNameVersion = "Version %s" % spec.get("version", "1.000")
    info.openTypeOS2WeightClass = wght
    designer = spec.get("designer", "")
    info.copyright = spec.get("copyright") or f"Copyright {year} {designer or 'the ' + fam + ' authors'}."
    if designer:
        info.openTypeNameDesigner = designer
    if spec.get("designer_url"):
        info.openTypeNameDesignerURL = spec["designer_url"]
    if spec.get("license"):
        info.openTypeNameLicense = spec["license"]
    if spec.get("license_url"):
        info.openTypeNameLicenseURL = spec["license_url"]
    info.openTypeOS2VendorID = (spec.get("vendor", "PNCH") + "    ")[:4]
    info.openTypeNameDescription = spec.get("description", "")
    # vertical metrics: one line height everywhere, nothing clipped
    ymax = max((bounds(flat_contours(glyphs, g)) or (0, 0, 0, 0))[3] for g in glyphs.values())
    ymin = min((bounds(flat_contours(glyphs, g)) or (0, 0, 0, 0))[1] for g in glyphs.values())
    span = design["asc"] - design["desc"]
    total = max(1.2 * design["upm"], span)
    asc = round(design["asc"] + (total - span) * design["asc"] / span)
    desc = round(asc - total)
    info.openTypeOS2TypoAscender = info.openTypeHheaAscender = asc
    info.openTypeOS2TypoDescender = info.openTypeHheaDescender = desc
    info.openTypeOS2TypoLineGap = info.openTypeHheaLineGap = 0
    # sampled bounds can miss a curve's true extreme by a unit or two
    info.openTypeOS2WinAscent = max(math.ceil(ymax) + 6, asc)
    info.openTypeOS2WinDescent = max(math.ceil(-ymin) + 6, -desc)
    info.openTypeOS2Selection = [7]
    info.openTypeOS2Type = []
    info.openTypeGaspRangeRecords = [{"rangeMaxPPEM": 65535, "rangeGaspBehavior": [0, 1, 2, 3]}]
    info.postscriptUnderlinePosition = round(design["desc"] * 0.5)
    info.postscriptUnderlineThickness = round(design["stem"] * design["hratio"] * 0.8)
    info.postscriptBlueValues = [-design["overshoot"], 0, design["xh"], design["xh"] + design["overshoot"],
                                 design["cap"], design["cap"] + design["overshoot"]]

    order = [".notdef", "space"] + [n for n in glyphs if n not in (".notdef", "space")]
    for name in order:
        gl = glyphs[name]
        ug = font.newGlyph(name)
        ug.width = round(gl.advance)
        if gl.uni:
            ug.unicodes = [gl.uni]
        pen = ug.getPen()
        for con in gl.contours:
            (con.transformed(lambda p: (p[0] + p[1] * tan, p[1])) if tan else con).draw(pen)
        for base, dx, dy in gl.components:
            pen.addComponent(base, (1, 0, 0, 1, round(dx + dy * tan), round(dy)))
    font.lib["public.glyphOrder"] = order
    for k, v in groups.items():
        font.groups[k] = v
    for k, v in kerning.items():
        font.kerning[k] = v
    font.features.text = fea
    if os.path.exists(path):
        shutil.rmtree(path)
    font.save(path)


def write_designspace(path, fam, masters, weights):
    from fontTools.designspaceLib import AxisDescriptor, DesignSpaceDocument, InstanceDescriptor, SourceDescriptor
    doc = DesignSpaceDocument()
    locs = sorted(masters)
    ax = AxisDescriptor()
    ax.name, ax.tag = "Weight", "wght"
    ax.minimum, ax.maximum = locs[0], locs[-1]
    ax.default = 400 if 400 in locs else locs[0]
    doc.addAxis(ax)
    for w in locs:
        s = SourceDescriptor()
        s.filename = os.path.basename(masters[w])
        s.familyName, s.styleName = fam, WEIGHT_NAME.get(w, str(w))
        s.location = {"Weight": w}
        doc.addSource(s)
    for w in weights:
        i = InstanceDescriptor()
        style = WEIGHT_NAME.get(w, str(w))
        i.familyName, i.styleName = fam, style
        i.filename = f"instances/{fam.replace(' ', '')}-{style}.ufo"
        i.location = {"Weight": w}
        i.postScriptFontName = f"{fam.replace(' ', '')}-{style}"
        doc.addInstance(i)
    doc.write(path)


def _fontmake(args, log):
    cmd = [sys.executable, "-m", "fontmake"] + args
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-25:])
        raise SystemExit(f"fontmake failed:\n{tail}")


def _finish_ttf(path):
    """Unhinted TrueType: enable smart dropout control so small sizes render cleanly."""
    from fontTools.ttLib import TTFont, newTable
    f = TTFont(path)
    if "glyf" in f and "prep" not in f:
        prep = newTable("prep")
        from fontTools.ttLib.tables.ttProgram import Program
        prep.program = Program()
        prep.program.fromBytecode(b"\xb8\x01\xff\x85\xb0\x04\x8d")
        f["prep"] = prep
        f["head"].flags |= 1 << 3
        f.save(path)


def _woff2(src, dst):
    from fontTools.ttLib import TTFont
    f = TTFont(src)
    f.flavor = "woff2"
    f.save(dst)


# ------------------------------------------------------------------ pipeline
def build(spec_path, out_dir, quiet=False, formats=("variable", "ttf", "otf", "woff2")):
    log = Log(quiet)
    spec = load_spec(spec_path)
    fam = spec["family"]
    fam_id = fam.replace(" ", "")
    if spec.get("mode") == "remix":
        from .remix import build_remix
        return build_remix(spec, out_dir, formats, log)

    log.stage("Brief")
    from .handwriting import load_traced
    design = resolve_design(spec)
    custom = load_overrides(spec)
    traced = load_traced(spec)
    masters, weights = master_designs(spec, design, traced)
    log.note(f"{fam}: preset {spec.get('preset', 'none')}, {len(weights)} weight(s) {weights}, "
             f"{len(masters)} master(s) at {list(masters)}")
    if custom:
        log.note(f"custom drawings: {', '.join(custom)}")
    if traced:
        log.note("source: handwriting photo (static weights, outlines traced from the writer)")

    log.stage("Drawing")
    drawn, meta = {}, {}
    for w, d in masters.items():
        drawn[w], meta[w] = draw_master(d, traced=traced["weights"][str(w)]["glyphs"] if traced else None)
    from .finish import finish_masters
    if traced:   # the writer's pen already shaped every edge; keep it as written
        for d in masters.values():
            d["soften"] = 0.0
    kept = finish_masters(drawn, masters, static=bool(traced))
    log.note(f"finishing: overlaps merged and corners softened ({len(kept)} glyph(s) kept as overlapping strokes"
             + (f": {', '.join(kept[:12])}" if kept else "") + ")")
    any_m = next(iter(drawn.values()))
    m0 = meta[next(iter(meta))]
    log.note(f"{len(any_m)} glyphs per master ({m0['composites']} accented composites)")
    if traced:
        log.note(f"{len(m0['filled'])} glyphs not on the photo were drawn by the engine at the writer's stroke weight")

    log.stage("Spacing")
    for w, d in masters.items():
        gl = drawn[w]
        log.note(f"wght {w}: stem {d['stem']:.0f}, n {gl['n'].advance:.0f}, o {gl['o'].advance:.0f}, "
                 f"H {gl['H'].advance:.0f}, space {gl['space'].advance:.0f}, tabular figures {meta[w]['tab']:.0f}")

    log.stage("Kerning")
    names = kern_names(any_m)
    groups, tables = {}, [{} for _ in masters]
    if design["kerning"] > 0:
        mats = []
        for w, d in masters.items():
            gl = drawn[w]
            nn = 2 * meta[w]["target"]["lc"]
            mats.append(kern_matrix(gl, names, d, nn))
        mats, first, second = kern_classes(names, mats)
        groups, tables = kerning_tables(names, mats, first, second)
        ref = mats[len(mats) // 2]
        idx = {n: i for i, n in enumerate(names)}
        show = [("A", "V"), ("T", "o"), ("L", "T"), ("V", "a"), ("r", "period"), ("Y", "e")]
        log.note(f"{len(first)} left classes x {len(second)} right classes, {len(tables[0])} pairs")
        log.note("samples: " + ", ".join(f"{a}{b} {int(ref[idx[a], idx[b]])}" for a, b in show))
    else:
        log.note("kerning disabled by spec")

    log.stage("OpenType features")
    fea = features(any_m, design)
    log.note(", ".join(t for t in ("kern", "case", "tnum", "zero", "ss01") if t != "ss01" or "feature ss01" in fea))

    log.stage("Sources")
    work = os.path.join(out_dir, "sources")
    os.makedirs(work, exist_ok=True)
    ufos = {}
    for (w, d), table in zip(masters.items(), tables):
        style = WEIGHT_NAME.get(w, str(w))
        ufos[w] = os.path.join(work, f"{fam_id}-{style}.ufo")
        write_ufo(ufos[w], drawn[w], d, spec, style, w, groups, table, fea)
    ds = os.path.join(work, f"{fam_id}.designspace")
    write_designspace(ds, fam, ufos, weights)
    log.note(f"{len(ufos)} UFO master(s) + designspace in {os.path.relpath(work)}")

    log.stage("Compile")
    fonts = os.path.join(out_dir, "fonts")
    made = []
    for sub in ("variable", "ttf", "otf", "webfonts"):
        shutil.rmtree(os.path.join(fonts, sub), ignore_errors=True)
    variable = len(masters) > 1 and "variable" in formats and not traced
    if variable:
        vf = os.path.join(fonts, "variable", f"{fam_id}[wght].ttf")
        os.makedirs(os.path.dirname(vf), exist_ok=True)
        _fontmake(["-m", ds, "-o", "variable", "--output-path", vf], log)
        _finish_ttf(vf)
        made.append(vf)
    for fmt in ("ttf", "otf"):
        if fmt not in formats:
            continue
        od = os.path.join(fonts, fmt)
        if len(masters) > 1 and not traced:
            _fontmake(["-m", ds, "-o", fmt, "-i", "--output-dir", od], log)
        else:
            _fontmake(["-u"] + list(ufos.values()) + ["-o", fmt, "--output-dir", od], log)
        for f in sorted(os.listdir(od)):
            if fmt == "ttf":
                _finish_ttf(os.path.join(od, f))
            made.append(os.path.join(od, f))
    shutil.rmtree(os.path.join(work, "instances"), ignore_errors=True)
    if "woff2" in formats:
        wd = os.path.join(fonts, "webfonts")
        os.makedirs(wd, exist_ok=True)
        for f in list(made):
            if f.endswith(".ttf"):
                dst = os.path.join(wd, os.path.basename(f)[:-4] + ".woff2")
                _woff2(f, dst)
                made.append(dst)
    flex = None
    if variable and spec.get("parametric", True) and not custom and spec.get("mode") != "handwriting":
        log.stage("Design lab")
        from .parametric import build_parametric
        tmp = os.path.join(fonts, "variable", f"{fam_id}Flex.ttf")
        path, axes = build_parametric(spec, design, tmp, os.path.join(work, "flex"), log)
        named = os.path.join(fonts, "variable", f"{fam_id}Flex[{','.join(a[0] for a in axes)}].ttf")
        os.replace(path, named)
        _finish_ttf(named)
        made.append(named)
        if "woff2" in formats:
            dst = os.path.join(fonts, "webfonts", os.path.basename(named)[:-4] + ".woff2")
            _woff2(named, dst)
            made.append(dst)
        shutil.rmtree(os.path.join(work, "flex"), ignore_errors=True)
        flex = dict(file=os.path.basename(named), axes=[list(a[:5]) for a in axes])
    for f in made:
        log.note(f"{os.path.relpath(f, out_dir)}  {os.path.getsize(f) / 1024:.0f} KB")

    result = dict(family=fam, family_id=fam_id, out=out_dir, fonts=made, weights=weights, masters=list(masters),
                  variable=variable, design=design, spec=spec, log=log, flex=flex)
    return result
