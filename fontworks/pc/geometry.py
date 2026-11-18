"""Stroke geometry: skeleton paths expanded into outlines.

A glyph is drawn as a handful of *strokes*. Each stroke is a centre line made
of nodes (point + tangent direction). The expander offsets every node to both
sides by half the pen width for that direction and rebuilds the curves with
the tangent-intersection method, so curve extremes get on-curve points and the
point structure is identical for every weight (variable-font compatible).
"""
from __future__ import annotations

import math

KAPPA = 0.5523

DIRS = {
    "E": (1, 0), "W": (-1, 0), "N": (0, 1), "S": (0, -1),
    "NE": (0.7071, 0.7071), "NW": (-0.7071, 0.7071),
    "SE": (0.7071, -0.7071), "SW": (-0.7071, -0.7071),
}


def vec(d):
    """Direction from a name ('N'), an angle in degrees, or an (x, y) pair."""
    if isinstance(d, str):
        return DIRS[d]
    if isinstance(d, (int, float)):
        a = math.radians(d)
        return (math.cos(a), math.sin(a))
    return norm(d)


def norm(v):
    n = math.hypot(v[0], v[1]) or 1.0
    return (v[0] / n, v[1] / n)


def add(a, b, k=1.0):
    return (a[0] + b[0] * k, a[1] + b[1] * k)


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def left(d):
    return (-d[1], d[0])


def intersect(p, d, q, e):
    """Intersection of line p+t*d with line q+u*e, or None if parallel."""
    den = cross(d, e)
    if abs(den) < 1e-6:
        return None
    t = cross(sub(q, p), e) / den
    return add(p, d, t)


class Contour:
    """Closed contour: start point plus segments ('l', p) or ('c', c1, c2, p)."""

    def __init__(self, start):
        self.start = start
        self.segs = []

    def line(self, p):
        self.segs.append(("l", p))

    def curve(self, c1, c2, p):
        self.segs.append(("c", c1, c2, p))

    def points(self):
        pts = [self.start]
        for s in self.segs:
            pts.append(s[-1])
        return pts

    def close(self):
        if self.segs and _far(self.segs[-1][-1], self.start):
            self.line(self.start)
        return self

    def reversed(self):
        pts = self.points()
        out = Contour(pts[-1])
        for i in range(len(self.segs) - 1, -1, -1):
            s = self.segs[i]
            if s[0] == "l":
                out.line(pts[i])
            else:
                out.curve(s[2], s[1], pts[i])
        return out

    def flat(self, steps=10):
        pts = [self.start]
        cur = self.start
        for s in self.segs:
            if s[0] == "l":
                pts.append(s[1])
            else:
                c1, c2, p = s[1], s[2], s[3]
                for i in range(1, steps + 1):
                    t = i / steps
                    m = 1 - t
                    pts.append((
                        m**3 * cur[0] + 3 * m * m * t * c1[0] + 3 * m * t * t * c2[0] + t**3 * p[0],
                        m**3 * cur[1] + 3 * m * m * t * c1[1] + 3 * m * t * t * c2[1] + t**3 * p[1],
                    ))
            cur = s[-1]
        return pts

    def area(self):
        pts = self.flat(6)
        a = 0.0
        for i in range(len(pts) - 1):
            a += cross(pts[i], pts[i + 1])
        return a / 2

    def transformed(self, fn):
        out = Contour(fn(self.start))
        for s in self.segs:
            out.segs.append((s[0],) + tuple(fn(p) for p in s[1:]))
        return out

    def draw(self, pen):
        pen.moveTo(_r(self.start))
        segs = self.segs
        if segs and segs[-1][0] == "l":
            segs = segs[:-1]
        for s in segs:
            if s[0] == "l":
                pen.lineTo(_r(s[1]))
            else:
                pen.curveTo(_r(s[1]), _r(s[2]), _r(s[3]))
        pen.closePath()


def _r(p):
    return (round(p[0], 2), round(p[1], 2))


def _far(a, b):
    return abs(a[0] - b[0]) > 1e-6 or abs(a[1] - b[1]) > 1e-6


class Pen:
    """Pen model: stroke thickness as a function of stroke direction.

    Vertical strokes get the full thickness, horizontal strokes get
    ``thick * hratio`` (optical correction plus contrast).
    """

    def __init__(self, hratio=0.9, power=1.5, roundness=KAPPA, stress="expansion", angle=0.0):
        self.hratio = hratio
        self.power = power
        self.k = roundness
        # Noordzij's stroke models. Expansion (pointed pen): thickness follows
        # the stroke's steepness, so stress is vertical; ``angle`` tilts that
        # axis. Translation (broad nib held at ``angle``): thickness follows
        # the stroke's angle to the nib, giving diagonal stress.
        self.stress = stress
        self.angle = math.radians(angle)
        self._norm = 1.0
        if stress == "translation":
            self._norm = self._raw((0.0, 1.0))

    def _raw(self, d):
        if self.stress == "translation":
            a = math.atan2(d[1], d[0])
            return self.hratio + (1 - self.hratio) * abs(math.sin(a - self.angle))
        if self.angle:
            c, s = math.cos(-self.angle), math.sin(-self.angle)
            d = (d[0] * c - d[1] * s, d[0] * s + d[1] * c)
        return self.hratio + (1 - self.hratio) * abs(d[1]) ** self.power

    def factor(self, d):
        return min(1.0, self._raw(d) / self._norm)


class Stroke:
    """Centre-line path builder.

    m(x, y, d)   start node, heading in direction d
    l(x, y)      straight line to a node
    c(x, y, d)   curve to a node, arriving in direction d
    Node options: wm (thickness multiplier), w (absolute thickness),
    cut (direction of the cut at that node, e.g. 'E' for a horizontal cut).
    """

    def __init__(self, pen, thick, wm=1.0, k=None):
        self.pen = pen
        self.thick = thick
        self.wm = wm
        self.k = pen.k if k is None else k
        self.nodes = []

    def m(self, x, y, d=None, **o):
        self.nodes.append(dict(p=(x, y), kind="m", d=vec(d) if d is not None else None, **o))
        return self

    def l(self, x, y, **o):
        self.nodes.append(dict(p=(x, y), kind="l", d=None, **o))
        return self

    def c(self, x, y, d, **o):
        self.nodes.append(dict(p=(x, y), kind="c", d=vec(d), **o))
        return self

    # ------------------------------------------------------------------
    def _resolve(self, closed):
        ns = self.nodes
        n = len(ns)
        for i, nd in enumerate(ns):
            prev = ns[i - 1] if i > 0 else None
            nxt = ns[i + 1] if i < n - 1 else (ns[0] if closed else None)
            if nd["kind"] == "l":
                din = norm(sub(nd["p"], prev["p"]))
            else:
                din = nd["d"]
            if nxt is None:
                dout = din
            elif nxt["kind"] == "l":
                dout = norm(sub(nxt["p"], nd["p"]))
            else:
                dout = nd["d"] if nd["d"] is not None else din
            if din is None:
                din = dout
            if nd["kind"] == "m" and not closed:
                din = dout
            nd["din"], nd["dout"] = din, dout
            nd["rmax"] = None
        # Radius of curvature at each end of every curve. A stroke thicker than
        # twice that radius would fold over itself on the inside of the bend,
        # so the pen thins there, the way a type designer lightens tight bowls.
        segs = [(i, i + 1) for i in range(n - 1)] + ([(n - 1, 0)] if closed else [])
        for a, b in segs:
            na, nb = ns[a], ns[b]
            if nb["kind"] == "l":
                continue
            c = intersect(na["p"], na["dout"], nb["p"], nb["din"])
            if c is None:
                continue
            ha = max(dot(sub(c, na["p"]), na["dout"]), 1e-3)
            hb = max(dot(sub(nb["p"], c), nb["din"]), 1e-3)
            k = nb.get("k", self.k)
            c1, c2 = add(na["p"], na["dout"], ha * k), add(nb["p"], nb["din"], -hb * k)
            mid = sub(c2, c1)
            for nd, v, ln in ((na, sub(c1, na["p"]), ha * k), (nb, sub(nb["p"], c2), hb * k)):
                bend = abs(cross(v, mid))
                if bend < 1e-6:
                    continue
                r = 1.5 * ln ** 3 / bend
                nd["rmax"] = r if nd["rmax"] is None else min(nd["rmax"], r)

    def _width(self, nd, d):
        if nd.get("w") is not None:
            w = nd["w"]
        else:
            w = self.thick * self.wm * nd.get("wm", 1.0) * self.pen.factor(d)
        if nd.get("rmax") is not None:
            w = min(w, max(1.9 * nd["rmax"], 0.8 * w))
        return w

    def _sides(self, nd):
        """Left and right offset points of a node."""
        p, din, dout = nd["p"], nd["din"], nd["dout"]
        cut = nd.get("cut")
        if cut is not None:
            c = vec(cut)
            d = dout
            w = self._width(nd, d)
            n = left(d)
            # a cut nearly parallel to the stroke would slice off a long thin
            # wedge; tilt it just enough to meet the stroke at a firm angle
            cn, cd = dot(c, n), dot(c, d)
            if abs(cn) < 0.62:
                cn = 0.62 if cn >= 0 else -0.62
                cd = math.copysign(math.sqrt(1 - cn * cn), cd if cd else 1.0)
                c = add((n[0] * cn, n[1] * cn), d, cd)
            den = dot(n, c)
            if abs(den) < 0.4:
                den = 0.4 if den >= 0 else -0.4
                off = (w / 2) / den
                return add(p, c, off), add(p, c, -off)
            # offset each side square to the stroke, then run it along its own
            # direction until it meets the cut through p: the side keeps its
            # line, so its curve arrives clean with no tooth at the terminal
            ql, qr = add(p, n, w / 2), add(p, n, -w / 2)
            return intersect(ql, d, p, c) or ql, intersect(qr, d, p, c) or qr
        win, wout = self._width(nd, din), self._width(nd, dout)
        li, ri = add(p, left(din), win / 2), add(p, left(din), -win / 2)
        if abs(cross(din, dout)) < 1e-3:
            return li, ri
        lo, ro = add(p, left(dout), wout / 2), add(p, left(dout), -wout / 2)
        lm = intersect(li, din, lo, dout) or li
        rm = intersect(ri, din, ro, dout) or ri
        return lm, rm

    def _side_segs(self, pts, idx):
        """Segments along one side. pts[i] is the offset point for node i."""
        ns = self.nodes
        segs = []
        for a, b in idx:
            na, nb = ns[a], ns[b]
            if nb["kind"] == "l":
                segs.append(("l", pts[b]))
                continue
            pa, pb = pts[a], pts[b]
            da, db = na["dout"], nb["din"]
            k = nb.get("k", self.k)
            corner = intersect(pa, da, pb, db)
            chord = math.hypot(pb[0] - pa[0], pb[1] - pa[1])
            if corner is None:
                c1, c2 = add(pa, da, chord / 3), add(pb, db, -chord / 3)
            else:
                ha, hb = dot(sub(corner, pa), da), dot(sub(pb, corner), db)
                ha, hb = max(ha, 0.0), max(hb, 0.0)
                lim = chord * 1.5
                ha, hb = min(ha, lim), min(hb, lim)
                c1, c2 = add(pa, da, ha * k), add(pb, db, -hb * k)
            segs.append(("c", c1, c2, pb))
        return segs

    def _cap(self, con, a, b, tip_dir, style, w):
        """Join side point a to side point b across a stroke end."""
        if style == "round":
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            r = math.hypot(a[0] - b[0], a[1] - b[1]) / 2
            tip = add(mid, tip_dir, r)
            k = KAPPA * r
            ta = norm(sub(tip, add(a, tip_dir, r)))
            con.curve(add(a, tip_dir, k), add(tip, ta, -k), tip)
            con.curve(add(tip, ta, k), add(b, tip_dir, k), b)
        else:
            con.line(b)

    def outline(self, cap0="butt", cap1="butt"):
        """Open stroke -> one closed contour (counter-clockwise)."""
        self._resolve(False)
        ns = self.nodes
        n = len(ns)
        L, R = (list(x) for x in zip(*[self._sides(nd) for nd in ns]))
        fwd = [(i, i + 1) for i in range(n - 1)]
        self._uncross(L, fwd)
        self._uncross(R, fwd)
        con = Contour(R[0])
        for s in self._side_segs(R, fwd):
            con.segs.append(s)
        self._cap(con, R[-1], L[-1], ns[-1]["dout"], cap1, 0)
        # left side backwards
        back = Stroke._reverse_segs(L[0], self._side_segs(L, fwd))
        con.segs.extend(back)
        d0 = ns[0]["din"]
        self._cap(con, L[0], R[0], (-d0[0], -d0[1]), cap0, 0)
        con.close()
        if con.area() < 0:
            con = con.reversed()
        return [con]

    def _uncross(self, pts, idx):
        """Where the inside of a tight bend folds back on itself, pinch the
        two offset points together so the outline keeps a clean cusp."""
        ns = self.nodes
        for a, b in idx:
            if ns[b]["kind"] == "l":
                continue
            run = sub(ns[b]["p"], ns[a]["p"])
            if dot(sub(pts[b], pts[a]), run) < 0:
                mid = ((pts[a][0] + pts[b][0]) / 2, (pts[a][1] + pts[b][1]) / 2)
                pts[a] = pts[b] = mid

    @staticmethod
    def _reverse_segs(start, segs):
        tmp = Contour(start)
        tmp.segs = list(segs)
        rev = tmp.reversed()
        return rev.segs

    def ring(self):
        """Closed stroke -> outer and inner contour."""
        self._resolve(True)
        ns = self.nodes
        n = len(ns)
        L, R = (list(x) for x in zip(*[self._sides(nd) for nd in ns]))
        loop = [(i, (i + 1) % n) for i in range(n)]
        self._uncross(L, loop)
        self._uncross(R, loop)
        out = []
        for pts in (L, R):
            con = Contour(pts[0])
            con.segs = self._side_segs(pts, loop)
            out.append(con)
        a0, a1 = out[0].area(), out[1].area()
        outer, inner = (out[0], out[1]) if abs(a0) > abs(a1) else (out[1], out[0])
        if outer.area() < 0:
            outer = outer.reversed()
        if inner.area() > 0:
            inner = inner.reversed()
        return [outer, inner]


def ellipse(cx, cy, rx, ry, k=KAPPA):
    con = Contour((cx + rx, cy))
    con.curve((cx + rx, cy + ry * k), (cx + rx * k, cy + ry), (cx, cy + ry))
    con.curve((cx - rx * k, cy + ry), (cx - rx, cy + ry * k), (cx - rx, cy))
    con.curve((cx - rx, cy - ry * k), (cx - rx * k, cy - ry), (cx, cy - ry))
    con.curve((cx + rx * k, cy - ry), (cx + rx, cy - ry * k), (cx + rx, cy))
    return con


def polygon(pts):
    con = Contour(pts[0])
    for p in pts[1:]:
        con.line(p)
    con.close()
    if con.area() < 0:
        con = con.reversed()
    return con
