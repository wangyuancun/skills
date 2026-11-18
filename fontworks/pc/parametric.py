"""Parametric variable font: every design control becomes a live axis.

Besides the weight axis, the family is built with axes for width, x-height,
thin strokes, squareness, softness, aperture and slant, following David
Berlow's parametric approach (one measurable property per axis). Each axis is
one pair of extra masters drawn from the Regular design with a single
parameter changed, so the axes add up independently and the Studio can move
any of them live in the browser.
"""
from __future__ import annotations

import os
import subprocess
import sys

from .build import (WEIGHT_STEM, draw_master, features, kern_classes, kern_matrix, kern_names, kerning_tables,
                    write_ufo)
from .finish import finish_masters


def _stem_factor(w):
    keys = sorted(WEIGHT_STEM)
    if w <= keys[0]:
        return WEIGHT_STEM[keys[0]]
    for a, b in zip(keys, keys[1:]):
        if a <= w <= b:
            t = (w - a) / (b - a)
            return WEIGHT_STEM[a] + (WEIGHT_STEM[b] - WEIGHT_STEM[a]) * t
    return WEIGHT_STEM[keys[-1]]


def _weight(d, base, v):
    m = _stem_factor(v)
    d["stem"] = base["stem"] * m
    d["hratio"] = min(max(base["hratio"] - 0.1 * (m - 1), 0.7), 0.98)
    d["join"] = min(max(base["join"] - 0.14 * (m - 1), 0.5), 0.92)


def axes_for(design, weights):
    """(tag, name, min, default, max, apply) for every axis this design supports."""
    xh = design["xh"]
    sq = round((design["roundness"] - 0.5523) / (0.78 - 0.5523) * 100)
    sq = max(0, min(100, sq))
    out = [
        ("wght", "Weight", min(weights[0], 300), 400, max(weights[-1], 800), _weight),
        ("wdth", "Width", 75, 100, 125, lambda d, b, v: d.__setitem__("width", b["width"] * v / 100)),
        ("YTLC", "Lowercase height", xh - 70, xh, xh + 70, lambda d, b, v: d.__setitem__("xh", v)),
        ("YOPQ", "Thin stroke", 60, round(design["hratio"] * 100), 100,
         lambda d, b, v: d.__setitem__("hratio", v / 100)),
        ("SQAR", "Squareness", 0, sq, 100,
         lambda d, b, v: d.__setitem__("roundness", 0.5523 + (0.78 - 0.5523) * v / 100)),
        ("SOFT", "Softness", 0, round(design["soften"] / 0.32 * 100), 100,
         lambda d, b, v: d.__setitem__("soften", 0.01 + 0.31 * v / 100)),
        ("APRT", "Aperture", 0, round(design["aperture"] * 100), 100,
         lambda d, b, v: d.__setitem__("aperture", v / 100)),
        ("slnt", "Slant", -12, 0, 0, lambda d, b, v: d.__setitem__("slant", -v)),
    ]
    # an axis whose default sits on an end only gets the other end
    return [a for a in out if a[2] < a[4]]


def master_set(design, weights):
    """[(key, location, design)]: the default plus one master per axis end."""
    axes = axes_for(design, weights)
    base = dict(design)
    if base["soften"] <= 0:
        base["soften"] = 0.01          # keep the corner structure every master shares
    default = {a[0]: a[3] for a in axes}
    out = [("default", dict(default), dict(base))]
    for tag, name, lo, df, hi, fn in axes:
        for v in (lo, hi):
            if v == df:
                continue
            d = dict(base)
            fn(d, base, v)
            loc = dict(default)
            loc[tag] = v
            out.append((f"{tag}{v}", loc, d))
    return axes, out


def build_parametric(spec, design, out_path, work, log=None):
    """Draw every master, finish, kern and compile one parametric variable font."""
    from fontTools.designspaceLib import AxisDescriptor, DesignSpaceDocument, SourceDescriptor
    weights = sorted(int(w) for w in spec.get("weights", [400]))
    axes, masters = master_set(design, weights)
    drawn, meta, designs = {}, {}, {}
    for key, loc, d in masters:
        drawn[key], meta[key] = draw_master(d)
        designs[key] = d
    finish_masters(drawn, designs)
    any_m = drawn["default"]
    names = kern_names(any_m)
    groups, tables = {}, [{} for _ in masters]
    if design["kerning"] > 0:
        mats = [kern_matrix(drawn[k], names, designs[k], 2 * meta[k]["target"]["lc"]) for k, _, _ in masters]
        mats, first, second = kern_classes(names, mats)
        groups, tables = kerning_tables(names, mats, first, second)
    fea = features(any_m, design)
    fam = spec["family"] + " Flex"
    fam_id = fam.replace(" ", "")
    os.makedirs(work, exist_ok=True)
    doc = DesignSpaceDocument()
    for tag, name, lo, df, hi, _ in axes:
        ax = AxisDescriptor()
        ax.name, ax.tag, ax.minimum, ax.default, ax.maximum = name, tag, lo, df, hi
        doc.addAxis(ax)
    tagname = {a[0]: a[1] for a in axes}
    for (key, loc, d), table in zip(masters, tables):
        path = os.path.join(work, f"{fam_id}-{key}.ufo")
        write_ufo(path, drawn[key], d, dict(spec, family=fam), key, 400, groups, table, fea)
        s = SourceDescriptor()
        s.filename = os.path.basename(path)
        s.familyName, s.styleName = fam, key
        s.location = {tagname[t]: v for t, v in loc.items()}
        doc.addSource(s)
    ds = os.path.join(work, f"{fam_id}.designspace")
    doc.write(ds)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    r = subprocess.run([sys.executable, "-m", "fontmake", "-m", ds, "-o", "variable", "--output-path", out_path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("fontmake (parametric) failed:\n" + "\n".join((r.stdout + r.stderr).splitlines()[-20:]))
    if log:
        log.note(f"parametric font: {len(axes)} axes ({', '.join(a[0] for a in axes)}), {len(masters)} masters")
    return out_path, axes
