"""Automatic sidebearings and kerning, computed from the outlines.

Spacing follows the area method used by HT Letterspacer: within a reference
zone, the white space between a glyph's edge and its extreme (capped at a
fixed depth) is averaged, and the sidebearing is whatever is needed to bring
that average to a target. Straight stems therefore get the full target, round
and open shapes get less, the way a type designer spaces by eye.

Kerning measures the closest approach between two outlines in 2D and pulls
pairs with too much air (AV, To, LT) together, or pushes collisions apart.
"""
from __future__ import annotations

import math

import numpy as np


def profile(contours, ys):
    """Left-most and right-most outline x at each scan line (nan when empty)."""
    lo = np.full(len(ys), np.nan)
    hi = np.full(len(ys), np.nan)
    y0, step = ys[0], ys[1] - ys[0]
    for con in contours:
        pts = con.flat(8)
        for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
            if y1 == y2:
                continue
            a, b = (y1, y2) if y1 < y2 else (y2, y1)
            i0 = max(int(math.ceil((a - y0) / step)), 0)
            i1 = min(int(math.floor((b - y0) / step)), len(ys) - 1)
            for i in range(i0, i1 + 1):
                x = x1 + (x2 - x1) * (ys[i] - y1) / (y2 - y1)
                if not lo[i] <= x:
                    lo[i] = x
                if not hi[i] >= x:
                    hi[i] = x
    return lo, hi


def bounds(contours):
    xs, ys = [], []
    for con in contours:
        for p in con.flat(6):
            xs.append(p[0])
            ys.append(p[1])
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def sidebearings(contours, zone, target, depth, optical=0.5):
    """Return (shift, advance): how far to move the outline and its width.

    optical is how much of the measured white a side gives back. A type
    designer gives a round side about two thirds of a straight side's
    sidebearing, not the full difference in white, or rounds crowd their
    neighbours (bc, ck, eo). 0.5 lands there for most designs.
    """
    ys = np.arange(zone[0] + 5.5, zone[1], 10.0)
    if len(ys) < 2:
        ys = np.array([zone[0] + 1.0, zone[0] + 2.0])
    lo, hi = profile(contours, ys)
    if np.all(np.isnan(lo)):
        b = bounds(contours)
        return float(target - b[0]), float((b[2] - b[0]) + 2 * target)
    xmin, xmax = np.nanmin(lo), np.nanmax(hi)
    ml = np.where(np.isnan(lo), depth, np.minimum(lo - xmin, depth))
    mr = np.where(np.isnan(hi), depth, np.minimum(xmax - hi, depth))
    lsb, rsb = target - optical * ml.mean(), target - optical * mr.mean()
    lsb, rsb = max(lsb, target * 0.38), max(rsb, target * 0.38)
    shift = lsb - xmin
    return float(shift), float((xmax + shift) + rsb)


class KernProfile:
    def __init__(self, contours, advance, ys):
        lo, hi = profile(contours, ys)
        ok = ~np.isnan(lo)
        self.y = ys[ok]
        self.left = lo[ok]                 # distance from origin to ink
        self.right = advance - hi[ok]      # distance from ink to advance
        self.empty = not ok.any()
        if not self.empty:
            self.lsb, self.rsb = self.left.min(), self.right.min()
        self.advance = advance


def kern_pair(a, b, d_air, d_touch, limit):
    """Kern value for glyph a followed by glyph b (0 when the pair is fine)."""
    if a.empty or b.empty:
        return 0.0
    dy = a.y[:, None] - b.y[None, :]
    gap = a.right[:, None] + b.left[None, :]
    d0 = max(a.rsb + b.lsb, d_air)
    k = np.max(np.sqrt(np.maximum(d0 * d0 - dy * dy, 0.0)) - gap)
    if k < 0:
        return float(max(k, -limit * min(a.advance, b.advance)))
    k2 = np.max(np.sqrt(np.maximum(d_touch * d_touch - dy * dy, 0.0)) - gap)
    return min(float(k2), 80.0) if k2 > 0 else 0.0
