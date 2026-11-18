"""Design parameters and the drawing context handed to every glyph function."""
from __future__ import annotations

import math

from .geometry import Pen, Stroke, Contour, ellipse, polygon, vec, norm

DEFAULTS = dict(
    # vertical metrics (units per em = 1000)
    upm=1000, cap=700, xh=500, asc=740, desc=-200, overshoot=10,
    # weight and contrast
    stem=84,          # lowercase vertical stem thickness
    cap_stem=1.08,    # capitals are drawn this much heavier than lowercase
    hratio=0.9,       # horizontal / vertical stroke ratio at zero contrast
    contrast=0.0,     # 0 = monoline, 0.5 = strong thick-thin contrast
    # proportions
    width=1.0,        # global horizontal scale
    o_ratio=1.0,      # lowercase o: width / x-height
    n_ratio=0.9,      # lowercase n: width / x-height
    O_ratio=1.04,     # capital O: width / cap height
    H_ratio=0.76,     # capital H: width / cap height
    # shape
    roundness=0.5523,  # curve tension: 0.5523 = true ellipse, 0.7 = squarish
    branch=0.6,        # where arches leave the stem (fraction of x-height)
    join=0.75,         # stroke thinning where a curve meets a stem
    aperture=0.5,      # 0 = closed terminals (grotesque), 1 = open (humanist)
    cut="perp",        # terminal cut on c e s a: 'h' horizontal, 'v' vertical, 'perp'
    terminal="flat",   # 'flat' or 'round' stroke ends
    dot="round",       # 'round' or 'square' i-dots and punctuation
    serif="none",      # 'none' or 'slab'
    serif_len=0.95,    # slab length beyond the stem, in stem widths
    serif_weight=1.0,  # slab thickness relative to horizontal strokes
    slant=0.0,         # degrees; positive leans right
    a="double",        # 'double' or 'single' storey a
    # rhythm
    weight_comp=0.9,   # how much letters widen as the stem gets heavier
    spacing=1.0,       # global letter-spacing factor
    kerning=1.0,       # kerning strength, 0 disables
    soften=0.07,       # corner radius in stems: 0 = knife-sharp, 0.3 = rounded-sans soft
    # stroke model (Noordzij): 'expansion' = vertical stress, 'translation' = broad nib
    stress="expansion",
    stress_angle=0.0,  # degrees: tilt of the stress axis, or the nib angle for translation
    inktrap=0.0,       # depth of ink traps in sharp inner corners, in stems (0 = none, 0.25 = deep)
)


class Shape:
    """Raw drawing of one glyph, before spacing."""

    def __init__(self):
        self.contours = []
        self.components = []   # (base glyph name, dx, dy)
        self.advance = None
        self.lsb_fixed = None  # (lsb, rsb) when the glyph sets its own spacing


class G:
    """Drawing context. One per glyph per master."""

    def __init__(self, spec, case="lc", scale=1.0, stem_scale=1.0, shape=None, dx=0.0, dy=0.0):
        p = dict(DEFAULTS)
        p.update(spec)
        self.spec = p
        self.scale, self.stem_scale = scale, stem_scale
        self.dx, self.dy = dx, dy
        k = scale
        self.cap, self.xh = p["cap"] * k, p["xh"] * k
        self.asc, self.desc = p["asc"] * k, p["desc"] * k
        # flatter, squarer curves linger at the baseline and need less overshoot
        self.os = p["overshoot"] * k * max(0.5, min(1.15, 1 - (p["roundness"] - 0.5523) * 2.2))
        self.s = p["stem"] * stem_scale
        self.S = p["stem"] * p["cap_stem"] * stem_scale
        self.F = p["stem"] * (1 + (p["cap_stem"] - 1) * 0.6) * stem_scale
        self.wd = p["width"]
        hr = p["hratio"] * (1 - p["contrast"])
        self.pen = Pen(hratio=hr, roundness=p["roundness"], stress=p["stress"], angle=p["stress_angle"])
        self.hf = self.pen.factor((1.0, 0.0))
        self.join, self.branch, self.ap = p["join"], p["branch"], p["aperture"]
        self.contrast = p["contrast"]
        self.round = p["terminal"] == "round"
        self.slab = p["serif"] == "slab"
        self.case = case
        self.T = {"lc": self.s, "uc": self.S}.get(case, self.F)
        wc = (p["stem"] - 84) * p["weight_comp"] * stem_scale
        self.ow = self.xh * p["o_ratio"] * self.wd + wc
        self.nw = self.xh * p["n_ratio"] * self.wd + wc
        self.Hw = self.cap * p["H_ratio"] * self.wd + wc * 1.1
        self.Ow = self.cap * p["O_ratio"] * self.wd + wc * 1.1
        self.fw = self.cap * 0.74 * self.wd + wc  # figure body width
        self.shape = shape if shape is not None else Shape()

    def sub(self, scale, stem_scale, dx=0.0, dy=0.0, case=None):
        """Context for a scaled-down drawing inside the same glyph (e.g. the R in ®)."""
        return G(self.spec, case or self.case, scale, stem_scale, self.shape, self.dx + dx, self.dy + dy)

    # --- thickness helpers ---------------------------------------------
    @property
    def h(self):
        """Thickness of a horizontal stroke at the current stem weight."""
        return self.T * self.hf

    @property
    def thin(self):
        """Multiplier for the thin diagonal of A V W etc."""
        return 1 - self.contrast * 0.75

    # --- primitives ----------------------------------------------------
    def P(self, wm=1.0, k=None, T=None):
        return Stroke(self.pen, T or self.T, wm, k)

    def put(self, contours):
        if self.dx or self.dy:
            contours = [c.transformed(lambda p: (p[0] + self.dx, p[1] + self.dy)) for c in contours]
        self.shape.contours.extend(contours)

    def add(self, st, cap0=None, cap1=None):
        """Expand an open stroke. Ends are round when the design asks for it."""
        c0 = cap0 or ("round" if self.round else "butt")
        c1 = cap1 or ("round" if self.round else "butt")
        ns = st.nodes
        for cap, i, j in ((c0, 0, 1), (c1, -1, -2)):
            # round ends on straight segments are pulled in so heights still align
            straight = (ns[1]["kind"] == "l") if i == 0 else (ns[-1]["kind"] == "l")
            if cap == "round" and straight and ns[i].get("cut") is None:
                a, b = ns[i]["p"], ns[j]["p"]
                d = norm((b[0] - a[0], b[1] - a[1]))
                w = st.thick * st.wm * ns[i].get("wm", 1.0) * self.pen.factor(d)
                seg = math.hypot(b[0] - a[0], b[1] - a[1])
                r = min(w / 2, seg * 0.45)
                ns[i]["p"] = (a[0] + d[0] * r, a[1] + d[1] * r)
        self.put(st.outline(c0, c1))
        return st

    def stem(self, x, y0, y1, wm=1.0, sb="", st="", cap0=None, cap1=None):
        """Vertical stroke centred on x. sb / st: slab serif at bottom / top
        ('f' both sides, 'l' left, 'r' right)."""
        self.add(self.P(wm).m(x, y0, "N").l(x, y1), cap0, cap1)
        w = self.T * wm
        if sb:
            self.serif(x, y0, w, sb, +1)
        if st:
            self.serif(x, y1, w, st, -1)

    def bar(self, x0, x1, y, wm=1.0, cap0=None, cap1=None):
        """Horizontal stroke centred on y."""
        self.add(self.P(wm).m(x0, y, "E").l(x1, y), cap0, cap1)

    def serif(self, x, y, w, sides, up):
        """Slab serif at a stroke end. ``up`` is +1 when the slab sits above y."""
        if not self.slab:
            return
        ln = (self.T * 0.55 + 38 * self.scale) * self.spec["serif_len"]
        t = self.h * self.spec["serif_weight"]
        x0 = x - w / 2 - (ln if sides in ("f", "l") else 0)
        x1 = x + w / 2 + (ln if sides in ("f", "r") else 0)
        self.put([polygon([(x0, y), (x1, y), (x1, y + up * t), (x0, y + up * t)])])

    def vserif(self, x, y, down=True, right=True):
        """Vertical slab on the end of a horizontal arm (T, E, F, L, Z).
        x is the arm end, y the arm's centre line."""
        if not self.slab:
            return
        t = self.T * 0.86
        ln = (self.T * 0.55 + 38 * self.scale) * self.spec["serif_len"] * 0.8
        h = self.h
        x0, x1 = (x - t, x) if right else (x, x + t)
        y0, y1 = (y - h / 2 - ln, y + h / 2) if down else (y - h / 2, y + h / 2 + ln)
        self.put([polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])])

    def oval(self, x0, y0, x1, y1, wm=1.0, k=None):
        """Closed bowl with the given outer bounds."""
        t = self.T * wm
        h = t * self.hf
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        st = self.P(wm, k)
        st.m(cx, y0 + h / 2, "E").c(x1 - t / 2, cy, "N").c(cx, y1 - h / 2, "W").c(x0 + t / 2, cy, "S")
        self.put(st.ring())

    def dot(self, cx, cy, d):
        """Dot of diameter d: round or square depending on the design."""
        r = d / 2
        if self.spec["dot"] == "round":
            self.put([ellipse(cx, cy, r, r)])
        else:
            r *= 0.92
            self.put([polygon([(cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy + r)])])

    @property
    def dotd(self):
        return self.T * (1.22 if self.spec["dot"] == "round" else 1.12)

    def sandbox(self, fn, *a):
        """Run a drawing function and return its contours instead of adding them."""
        keep, self.shape = self.shape, Shape()
        try:
            fn(self, *a)
            return self.shape.contours
        finally:
            self.shape = keep

    def mirror_x(self, fn, w, *a):
        """Draw fn mirrored left-right inside a box of width w."""
        self.shape.contours.extend(c.transformed(lambda p: (w - p[0], p[1])).reversed() for c in self.sandbox(fn, *a))

    def rotate(self, fn, w, hgt, *a):
        """Draw fn rotated by 180 degrees inside a w x hgt box."""
        self.shape.contours.extend(c.transformed(lambda p: (w - p[0], hgt - p[1])) for c in self.sandbox(fn, *a))

    def poly(self, pts):
        self.put([polygon(pts)])

    def dg(self, xa, ya, xb, yb, wm=1.0, ea=0, eb=0, cut="E", cut0=None, cap0=None, cap1=None):
        """Diagonal stroke with horizontal cuts at both ends.

        ea / eb say how xa / xb are measured: 0 = centre line, -1 = xa is the
        left edge of the cut, +1 = the right edge.
        """
        ca, cb = xa, xb
        for _ in range(4):
            d = norm((cb - ca, yb - ya))
            w = self.T * wm * self.pen.factor(d)
            half = (w / 2) / max(abs(d[1]), 0.15)
            ca, cb = xa - ea * half, xb - eb * half
        st = self.P(wm).m(ca, ya, cut=cut0 or cut).l(cb, yb, cut=cut)
        self.add(st, cap0 or "butt", cap1 or "butt")
        return ca, cb, half

    # --- curve helpers -------------------------------------------------
    def cutdir(self):
        return {"h": "E", "v": "N"}.get(self.spec["cut"])

    def arc_node(self, cx, cy, rx, ry, ang, ccw=True):
        """Point and travel direction on an ellipse at angle ``ang`` (degrees)."""
        a = math.radians(ang)
        p = (cx + rx * math.cos(a), cy + ry * math.sin(a))
        d = norm((-rx * math.sin(a), ry * math.cos(a)))
        if not ccw:
            d = (-d[0], -d[1])
        return p, d

    def open_arc(self, x0, y0, x1, y1, a_top, a_bot, wm=1.0):
        """C-shaped stroke inside the outer box, open to the right.
        a_top / a_bot: opening angles of the upper and lower terminal."""
        t, h = self.T * wm, self.T * wm * self.hf
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        rx, ry = (x1 - x0) / 2 - t / 2, (y1 - y0) / 2 - h / 2
        (p1, d1), (p2, d2) = self.arc_node(cx, cy, rx, ry, a_top), self.arc_node(cx, cy, rx, ry, -a_bot)
        cut = self.cutdir()
        st = self.P(wm)
        st.m(p1[0], p1[1], d1, cut=cut).c(cx, cy + ry, "W").c(cx - rx, cy, "S")
        st.c(cx, cy - ry, "E").c(p2[0], p2[1], d2, cut=cut)
        self.add(st)
        return rx, ry

    def ap_angle(self, lo=22, hi=52):
        """Opening angle of a curved terminal. Horizontal cuts need a steep
        tangent (small angle), vertical cuts a shallow one (large angle)."""
        a = lo + (hi - lo) * self.ap
        cut = self.spec["cut"]
        if cut == "h":
            return a * 0.55
        if cut == "v":
            return 46 + (a - lo) * 0.7
        return a

    def arch(self, xl, xr, ytop, ybot=0, sb="", bias=0.04, cap1=None):
        """Shoulder leaving a stem whose right edge is xl, landing on a stem
        whose right edge is xr (n, m, h)."""
        T, h, j = self.T, self.h, self.join
        w0 = T * j
        xs, xe = xl - w0 / 2, xr - T / 2
        xt = (xl - T + xr) / 2 + (xr - xl) * bias
        yt = ytop + self.os - h / 2
        ry = min((xe - xt) * 1.08, (ytop - ybot) * 0.7)
        st = self.P().m(xs, ybot + (ytop - ybot) * self.branch, "N", wm=j).c(xt, yt, "E").c(xe, yt - ry, "S").l(xe, ybot)
        self.add(st, cap0="butt", cap1=cap1)
        if sb:
            self.serif(xe, ybot, T, sb, +1)

    def bowl(self, xs, x1, y0, y1, right=True, j=None):
        """Open bowl attached to a stem (b d p q). xs is the stem edge the bowl
        grows from, x1 the far outer edge; y0 / y1 the outer bottom and top."""
        T, h = self.T, self.h
        jn = self.join
        w0 = T * jn
        sg = 1 if right else -1
        xa = xs - sg * w0 / 2
        cx = (xs - sg * T + x1) / 2 + sg * (abs(x1 - xs)) * 0.03
        xf = x1 - sg * T / 2
        cy = (y0 + y1) / 2
        spread = (y1 - y0) * (self.branch - 0.5) if j is None else (y1 - y0) * j
        st = self.P()
        st.m(xa, cy + spread, "N", wm=jn).c(cx, y1 - h / 2, "E" if right else "W")
        st.c(xf, cy, "S").c(cx, y0 + h / 2, "W" if right else "E").c(xa, cy - spread, "N", wm=jn)
        self.add(st, cap0="butt", cap1="butt")
