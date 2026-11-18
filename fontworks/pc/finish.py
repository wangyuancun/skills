"""Finishing: soften every corner the way a drawn letter is soft.

A stroke engine produces mathematically sharp corners: knife-edge terminals,
needle-point vertices on V and W, crisp slab ends. Printed and drawn type is
never like that. Ink spread, a worn punch or a designer's hand rounds every
corner a little, and the eye reads the sharp version as synthetic.

This pass finds the corners of each contour (where the outline's direction
jumps) and replaces each with a short curve. The radius scales with the stem,
so it stays proportional across weights, and the same corners are softened in
every master so the variable font still interpolates.
"""
from __future__ import annotations

import math

from .geometry import Contour

THRESHOLD = 28.0   # degrees of direction change that count as a corner
SAMPLES = 24


def _dir(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    return (dx / n, dy / n) if n > 1e-9 else None


def _nodes(con):
    """Closed list of segments as (p0, seg) with explicit start points."""
    out, cur = [], con.start
    for s in con.segs:
        out.append((cur, s))
        cur = s[-1]
    # drop a trailing zero-length closing line
    if out and out[-1][1][0] == "l" and math.hypot(out[-1][0][0] - out[-1][1][1][0], out[-1][0][1] - out[-1][1][1][1]) < 1e-6:
        out.pop()
    return out


def _out_dir(p0, s):
    if s[0] == "l":
        return _dir(p0, s[1])
    for q in (s[1], s[2], s[3]):
        d = _dir(p0, q)
        if d:
            return d
    return None


def _in_dir(p0, s):
    if s[0] == "l":
        return _dir(p0, s[1])
    end = s[3]
    for q in (s[2], s[1], p0):
        d = _dir(q, end)
        if d:
            return d
    return None


def _bez(p0, c1, c2, p1, t):
    m = 1 - t
    return (m ** 3 * p0[0] + 3 * m * m * t * c1[0] + 3 * m * t * t * c2[0] + t ** 3 * p1[0],
            m ** 3 * p0[1] + 3 * m * m * t * c1[1] + 3 * m * t * t * c2[1] + t ** 3 * p1[1])


def _length(p0, s):
    if s[0] == "l":
        return math.hypot(s[1][0] - p0[0], s[1][1] - p0[1])
    pts = [_bez(p0, s[1], s[2], s[3], i / SAMPLES) for i in range(SAMPLES + 1)]
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def _t_at(p0, s, dist, from_end):
    """Parameter t at arc length dist from the start (or the end)."""
    pts = [_bez(p0, s[1], s[2], s[3], i / SAMPLES) for i in range(SAMPLES + 1)]
    if from_end:
        pts = pts[::-1]
    acc = 0.0
    for i in range(SAMPLES):
        L = math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
        if acc + L >= dist and L > 0:
            t = (i + (dist - acc) / L) / SAMPLES
            return 1 - t if from_end else t
        acc += L
    return 0.0 if from_end else 1.0


def _split(p0, c1, c2, p1, t):
    """de Casteljau: return (left, right) as (p0, c1, c2, p) tuples."""
    lerp = lambda a, b: (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)  # noqa: E731
    a, b, c = lerp(p0, c1), lerp(c1, c2), lerp(c2, p1)
    d, e = lerp(a, b), lerp(b, c)
    f = lerp(d, e)
    return (p0, a, d, f), (f, e, c, p1)


def corners(con):
    """Indices of segment starts that are outer (convex) corners, with their turn angle.

    Only corners that stick out of the ink are softened. Inner corners, where
    a bowl meets a stem or an arm leaves a stroke, stay crisp: rounding them
    leaves a nick, and type designers keep joins sharp."""
    ns = _nodes(con)
    sign = 1.0 if con.area() >= 0 else -1.0     # ink is on the left of a counter-clockwise path
    out = {}
    for i in range(len(ns)):
        pin = ns[i - 1]
        din, dout = _in_dir(*pin), _out_dir(*ns[i])
        if din is None or dout is None:
            continue
        ang = math.degrees(math.acos(max(-1.0, min(1.0, din[0] * dout[0] + din[1] * dout[1]))))
        turn = (din[0] * dout[1] - din[1] * dout[0]) * sign
        if ang > THRESHOLD and turn > 0:
            out[i] = ang
    return out


def short_segments(con, tol):
    """Indices of segments shorter than tol: the spurs and steps left where
    strokes overlap almost, but not quite, on the same line."""
    return {i for i, nd in enumerate(_nodes(con)) if _length(*nd) < tol}


def collapse(con, idx):
    """Remove the segments in idx, joining their neighbours at a clean corner:
    where two lines meet, at their intersection; otherwise at the midpoint."""
    if not idx:
        return con
    ns = _nodes(con)
    n = len(ns)
    if n - len(idx) < 3:
        return con
    # never two neighbours at once: their shared point would be moved twice
    picked = set()
    for i in sorted(idx):
        if (i - 1) % n not in picked and (i + 1) % n not in picked:
            picked.add(i)
    idx = picked
    pts = [p0 for p0, _ in ns]          # pts[i] = start of segment i
    segs = [s for _, s in ns]
    for i in sorted(idx):
        a, b = pts[i], segs[i][-1]       # the short segment runs a -> b
        prev_p0, prev = pts[(i - 1) % n], segs[(i - 1) % n]
        nxt_p0, nxt = b, segs[(i + 1) % n]
        q = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if prev[0] == "l" and nxt[0] == "l":
            d1, d2 = _dir(prev_p0, a), _dir(nxt_p0, nxt[1])
            if d1 and d2:
                den = d1[0] * d2[1] - d1[1] * d2[0]
                if abs(den) > 1e-3:
                    t = ((b[0] - a[0]) * d2[1] - (b[1] - a[1]) * d2[0]) / den
                    cand = (a[0] + d1[0] * t, a[1] + d1[1] * t)
                    if math.hypot(cand[0] - q[0], cand[1] - q[1]) < 3 * math.hypot(b[0] - a[0], b[1] - a[1]) + 1:
                        q = cand
        # move the shared points
        if prev[0] == "l":
            segs[(i - 1) % n] = ("l", q)
        else:
            c2 = prev[2]
            segs[(i - 1) % n] = ("c", prev[1], (c2[0] + q[0] - a[0], c2[1] + q[1] - a[1]), q)
        pts[i] = q
        pts[(i + 1) % n] = q
        if nxt[0] == "c":
            c1 = nxt[1]
            segs[(i + 1) % n] = ("c", (c1[0] + q[0] - b[0], c1[1] + q[1] - b[1]), nxt[2], nxt[3])
        segs[i] = None
    keep = [(pts[i], segs[i]) for i in range(n) if segs[i] is not None]
    out = Contour(keep[0][0])
    for _, sg in keep:
        out.segs.append(sg)
    return out.close()


def concave(con, min_angle=62.0):
    """Sharp inner corners (crotches) where ink pools: candidates for ink traps."""
    ns = _nodes(con)
    sign = 1.0 if con.area() >= 0 else -1.0
    out = {}
    for i in range(len(ns)):
        din, dout = _in_dir(*ns[i - 1]), _out_dir(*ns[i])
        if din is None or dout is None:
            continue
        ang = math.degrees(math.acos(max(-1.0, min(1.0, din[0] * dout[0] + din[1] * dout[1]))))
        turn = (din[0] * dout[1] - din[1] * dout[0]) * sign
        if ang > min_angle and turn < 0:
            out[i] = ang
    return out


def soften(con, r, flags, trap=None):
    """Return a new contour with the corners in ``flags`` replaced by curves.
    With ``trap`` (a depth), the corners are cut into the ink instead: an ink
    trap, the notch that keeps a sharp crotch from filling in at small sizes."""
    ns = _nodes(con)
    n = len(ns)
    if not flags or n < 2 or r <= 0:
        return con
    lens = [_length(*nd) for nd in ns]
    # how much of each segment the corner at its start / end may use
    cut_s, cut_e = [0.0] * n, [0.0] * n
    for i, ang in flags.items():
        j = (i - 1) % n
        # a shallow corner needs a long, gentle blend or it reads as a kink;
        # a sharp corner keeps the small radius
        k = 1.0 + 1.0 * max(0.0, (70.0 - ang) / 42.0) if ang < 70 and trap is None else 1.0
        d = min(r * k, lens[i] * 0.42, lens[j] * 0.42)
        cut_s[i], cut_e[j] = d, d
    segs = []   # trimmed segments: (p0, seg)
    for i, (p0, s) in enumerate(ns):
        a, b = cut_s[i], cut_e[i]
        if s[0] == "l":
            L = lens[i] or 1.0
            q0 = (p0[0] + (s[1][0] - p0[0]) * a / L, p0[1] + (s[1][1] - p0[1]) * a / L)
            q1 = (s[1][0] + (p0[0] - s[1][0]) * b / L, s[1][1] + (p0[1] - s[1][1]) * b / L)
            segs.append((q0, ("l", q1)))
        else:
            P = (p0, s[1], s[2], s[3])
            if a > 0:
                P = _split(*P, _t_at(p0, s, a, False))[1]
            if b > 0:
                q = P[0]
                t = _t_at(q, ("c",) + P[1:], b, True)
                P = _split(*P, t)[0]
            segs.append((P[0], ("c", P[1], P[2], P[3])))
    out = None
    k = 0.55
    for i in range(n):
        p0, s = segs[i]
        if i in flags:
            pj, sj = segs[(i - 1) % n]
            a_end = sj[-1]
            din = _in_dir(pj, sj) or _dir(a_end, p0)
            dout = _out_dir(p0, s) or _dir(a_end, p0)
            d = cut_s[i]
            if out is None:
                out = Contour(a_end)
            if trap is not None:
                # the original corner, then pushed into the ink along the bisector
                cx_, cy_ = a_end[0] + din[0] * d, a_end[1] + din[1] * d
                bis = _dir((0, 0), (din[0] - dout[0], din[1] - dout[1])) or (0.0, 0.0)
                tip = (cx_ + bis[0] * trap, cy_ + bis[1] * trap)
                out.segs.append(("l", tip))
                out.segs.append(("l", p0))
            else:
                fillet = ("c", (a_end[0] + din[0] * d * k, a_end[1] + din[1] * d * k),
                          (p0[0] - dout[0] * d * k, p0[1] - dout[1] * d * k), p0)
                out.segs.append(fillet)
        elif out is None:
            out = Contour(p0)
        out.segs.append(s)
    # close: the last segment must end where the contour started
    if out.segs and (abs(out.segs[-1][-1][0] - out.start[0]) > 1e-6 or abs(out.segs[-1][-1][1] - out.start[1]) > 1e-6):
        out.line(out.start)
    return out


def _signature(contours):
    return tuple(tuple(s[0] for s in c.segs) for c in contours)


def union(contours):
    """Merge overlapping strokes into one clean outline (PostScript direction)."""
    import pathops
    from fontTools.pens.recordingPen import RecordingPen
    path = pathops.Path()
    pen = path.getPen()
    for c in contours:
        c.draw(pen)
    path.simplify(fix_winding=True, keep_starting_points=False, clockwise=False)
    rec = RecordingPen()
    path.draw(rec)
    out, cur = [], None
    for op, pts in rec.value:
        if op == "moveTo":
            cur = Contour(pts[0])
        elif op == "lineTo":
            cur.line(pts[0])
        elif op == "curveTo":
            cur.curve(*pts)
        elif op == "qCurveTo":   # not expected from cubic input; promote just in case
            p0 = cur.segs[-1][-1] if cur.segs else cur.start
            q, p = pts[0], pts[-1]
            cur.curve((p0[0] + 2 / 3 * (q[0] - p0[0]), p0[1] + 2 / 3 * (q[1] - p0[1])),
                      (p[0] + 2 / 3 * (q[0] - p[0]), p[1] + 2 / 3 * (q[1] - p[1])), p)
        elif op in ("closePath", "endPath"):
            out.append(cur.close())
    return out


def _rotate(c, k):
    """Same closed contour, starting at segment k."""
    pts = c.points()
    segs = c.segs[k:] + c.segs[:k]
    return Contour(pts[k]) if not segs else _with(pts[k], segs)


def _with(start, segs):
    c = Contour(start)
    c.segs = list(segs)
    return c


def _centroid(c):
    pts = c.flat(4)
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def _match(ref, cands):
    """Reorder and rotate cands so each matches ref's structure. None if impossible."""
    if len(ref) != len(cands):
        return None
    left = list(cands)
    out = []
    for r in ref:
        kinds = [s[0] for s in r.segs]
        rc = _centroid(r)
        best = None
        for ci, c in enumerate(left):
            if len(c.segs) != len(kinds):
                continue
            ck = [s[0] for s in c.segs]
            cc = _centroid(c)
            for k in range(len(ck)):
                if ck[k:] + ck[:k] != kinds:
                    continue
                rot = _rotate(c, k)
                rp, cp = r.points(), rot.points()
                d = sum(math.hypot((a[0] - rc[0]) - (b[0] - cc[0]), (a[1] - rc[1]) - (b[1] - cc[1])) for a, b in zip(rp, cp))
                d += 3 * math.hypot(rc[0] - cc[0], rc[1] - cc[1])
                if best is None or d < best[0]:
                    best = (d, ci, rot)
        if best is None:
            return None
        out.append(best[2])
        left.pop(best[1])
    return out


def _align(merged):
    aligned = [merged[0]]
    for m in merged[1:]:
        a = _match(merged[0], m)
        if a is None:
            return None
        aligned.append(a)
    return aligned


def finish_masters(drawn, designs, static=False):
    """Merge overlaps and soften corners in every master. drawn: {wght: {name: Glyph}}.

    Returns the names of glyphs whose merged outlines differ in structure
    between masters; those keep their overlapping strokes (still valid, still
    interpolating) and are softened stroke by stroke where that is safe.
    """
    ws = list(drawn)
    names = list(drawn[ws[0]])
    kept = []
    for name in names:
        gls = [drawn[w][name] for w in ws]
        if not gls[0].contours:
            continue
        merged = [union(g.contours) for g in gls]
        ok = all(merged)
        if static:
            # separate fonts per weight (a traced hand): no interpolation, so each
            # weight is merged on its own and never needs the same structure
            for w, g, m in zip(ws, gls, merged):
                if m:
                    tl = designs[w]["stem"] * 0.2
                    g.contours = [collapse(c, short_segments(c, tl)) or c for c in m]
            continue
        if ok and len(ws) > 1:
            aligned = _align(merged)
            if aligned is None:
                # structures differ, often only by a spur that exists in one
                # weight: clear spurs in each master on its own, then retry
                cleaned = [[collapse(c, short_segments(c, designs[w]["stem"] * 0.2)) for c in m] for w, m in zip(ws, merged)]
                aligned = _align(cleaned)
            if aligned is None:
                ok = False
            else:
                merged = aligned
        if not ok:
            kept.append(name)
            _soften_strokes(ws, gls, designs)
            continue
        # spurs: segments shorter than a fifth of the stem in every master go
        tol = [designs[w]["stem"] * 0.2 for w in ws]
        for ci in range(len(merged[0])):
            common = None
            for m, tl in zip(merged, tol):
                sh = short_segments(m[ci], tl)
                common = sh if common is None else common & sh
            if common:
                for m in merged:
                    m[ci] = collapse(m[ci], common)
        depth = [designs[w].get("inktrap", 0.0) * designs[w]["stem"] for w in ws]
        if max(depth) > 0:
            tflags = [dict() for _ in merged[0]]
            for m in merged:
                for ci, c in enumerate(m):
                    tflags[ci].update(concave(c, 95.0))
            merged = [[soften(c, dp * 0.9, f, trap=dp) for c, f in zip(m, tflags)] for m, dp in zip(merged, depth)]
        flags = [dict() for _ in merged[0]]
        for m in merged:   # a corner in any master is softened in all of them
            for ci, c in enumerate(m):
                flags[ci].update(corners(c))
        for w, g, m in zip(ws, gls, merged):
            r = designs[w]["stem"] * designs[w].get("soften", 0.07)
            g.contours = [soften(c, r, f) for c, f in zip(m, flags)]
    return kept


def _inside(pt, poly):
    x, y = pt
    c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def _near(pt, poly, r):
    x, y = pt
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        dx, dy = x2 - x1, y2 - y1
        L = dx * dx + dy * dy
        t = 0.0 if L == 0 else max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / L))
        if math.hypot(x - (x1 + t * dx), y - (y1 + t * dy)) < r:
            return True
    return False


def _soften_strokes(ws, gls, designs):
    """Fallback for overlapping strokes: soften only corners that are clear of
    every other stroke, so no hidden corner pokes out as a bump."""
    flags = None
    for w, g in zip(ws, gls):
        r = designs[w]["stem"] * designs[w].get("soften", 0.07)
        polys = [c.flat(8) for c in g.contours]
        fl = []
        for ci, c in enumerate(g.contours):
            pts = c.points()
            keep = {}
            for i, ang in corners(c).items():
                p = pts[i]
                hidden = any(_inside(p, q) or _near(p, q, r * 1.5) for k, q in enumerate(polys) if k != ci)
                if not hidden:
                    keep[i] = ang
            fl.append(keep)
        if flags is None:
            flags = fl
        else:   # soften a corner only if it is clear in every master
            flags = [{i: a for i, a in f.items() if i in g_} for f, g_ in zip(flags, fl)]
    for w, g in zip(ws, gls):
        r = designs[w]["stem"] * designs[w].get("soften", 0.07)
        g.contours = [soften(c, r, f) for c, f in zip(g.contours, flags)]
