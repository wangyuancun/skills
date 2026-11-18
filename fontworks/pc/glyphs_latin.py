"""Latin letters and figures, drawn as strokes.

Every function receives a drawing context ``g`` (see context.G) and draws the
glyph with its left edge near x = 0. Sidebearings are added later by the
spacing engine, so no function sets an advance width.
"""
from __future__ import annotations

from .geometry import norm

GLYPHS = {}   # name -> (function, unicode or None, case)


def glyph(name, uni=None, case="lc"):
    def deco(fn):
        GLYPHS[name] = (fn, uni, case)
        return fn
    return deco


# ---------------------------------------------------------------- lowercase
def _a_double(g):
    T, h, xh, os = g.T, g.h, g.xh, g.os
    w = g.nw * 0.97
    xr = w - T / 2
    ytop = xh + os - h / 2
    ys = xh * 0.6
    cxa = w * 0.5
    rx, ry = xr - cxa, ytop - ys
    p, d = g.arc_node(cxa, ys, rx, ry, 180 - g.ap_angle(24, 48))
    st = g.P().m(xr, 0, "N").l(xr, ys).c(cxa, ytop, "W").c(p[0], p[1], d, cut=g.cutdir())
    g.add(st)
    g.serif(xr, 0, T, "r", +1)
    # bowl
    ybt = xh * 0.57 - h * 0.5
    w0 = T * g.join
    xj = (w - T) + w0 / 2
    inner = max(w - 2 * T, 10.0)                      # width of the bowl's counter
    cxb = max((w - T) * 0.5, T + inner * 0.42)
    ybot = -os + h / 2
    room = (ybt - ybot) - max(xh * 0.11, 44)          # keep the bowl's counter open in heavy weights
    bw = min(0.92, max(room / (2 * h), 0.45))
    b = g.P().m(xr, ybt, "W", wm=bw).l(max(cxb + w * 0.06, T + inner * 0.6), ybt, wm=bw)
    b.c(T * 0.5, (ybt + ybot) / 2, "S").c(cxb, ybot, "E", wm=min(1.0, bw / 0.92)).c(xj, ybot + (ybt - ybot) * 0.5, "N", wm=g.join)
    g.add(b, cap0="butt", cap1="butt")


def _a_single(g):
    T, xh, os = g.T, g.xh, g.os
    w = (g.nw + g.ow) / 2 * 1.02
    g.bowl(w - T, 0, -os, xh + os, right=False)
    g.stem(w - T / 2, 0, xh, sb="r")


@glyph("a", 0x61)
def a(g):
    (_a_single if g.spec["a"] == "single" else _a_double)(g)


@glyph("a.ss01")
def a_alt(g):
    (_a_double if g.spec["a"] == "single" else _a_single)(g)


def _bw(g):
    return (g.nw + g.ow) / 2 * 1.02


@glyph("b", 0x62)
def b(g):
    T = g.T
    g.stem(T / 2, 0, g.asc, st="l")
    g.bowl(T, _bw(g), -g.os, g.xh + g.os)


@glyph("c", 0x63)
def c(g):
    a = g.ap_angle()
    g.open_arc(0, -g.os, g.ow * 0.93, g.xh + g.os, a, a)


@glyph("d", 0x64)
def d(g):
    T, w = g.T, _bw(g)
    g.bowl(w - T, 0, -g.os, g.xh + g.os, right=False)
    g.stem(w - T / 2, 0, g.asc, sb="r", st="l")


def _e(g, x0=0.0):
    T, h, xh, os = g.T, g.h, g.xh, g.os
    w = g.ow * 0.96
    cx, cy = x0 + w / 2, xh / 2
    rx, ry = w / 2 - T / 2, (xh + 2 * os) / 2 - h / 2
    heavy = min(max((T - 100) / 80, 0.0), 1.0)
    yb = xh * (0.5 + 0.035 * heavy)          # a heavier e lifts its bar to keep the eye open
    wb = 0.95 - 0.22 * heavy                 # and thins it
    import math
    ext = 0.0 if g.spec["cut"] == "h" else T * 0.36
    gap = max(h * (0.8 - 0.3 * heavy), 24)   # heavy weights keep the terminal higher, where the curve is steep
    need = (cy - (yb - h / 2 - gap - ext)) / ry
    ang = max(g.ap_angle(16, 46), math.degrees(math.asin(min(max(need, 0.0), 0.95))))
    p, d = g.arc_node(cx, cy, rx, ry, -ang)
    # the bowl starts flush with the underside of the bar: no shelf below it
    st = g.P().m(cx + rx, yb - h * wb / 2, "N").c(cx, cy + ry, "W").c(cx - rx, cy, "S")
    st.c(cx, cy - ry, "E").c(p[0], p[1], d, cut=g.cutdir())
    g.add(st, cap0="butt")
    g.bar(cx - rx, cx + rx, yb, wm=wb, cap0="butt", cap1="butt")
    return w


@glyph("e", 0x65)
def e(g):
    _e(g)


@glyph("f", 0x66)
def f(g):
    T, h = g.T, g.h
    bw = g.nw * 0.64
    xs = bw * 0.42
    r = bw * 0.56
    yt = g.asc + g.os * 0.5 - h / 2
    st = g.P().m(xs, 0, "N").l(xs, yt - r).c(xs + r, yt, "E").l(xs + r * 1.12, yt)
    g.add(st)
    g.bar(0, bw, g.xh - h / 2)
    g.serif(xs, 0, T, "f", +1)


@glyph("g", 0x67)
def gg(g):
    T, h, xh, os = g.T, g.h, g.xh, g.os
    w = _bw(g)
    xr = w - T / 2
    g.bowl(w - T, 0, -os, xh + os, right=False)
    cx = w * 0.48
    rx = xr - cx
    ry = -g.desc * 0.6
    yc = g.desc + h / 2 + ry
    p, dd = g.arc_node(cx, yc, rx, ry, 180 + g.ap_angle(34, 56), ccw=False)
    st = g.P().m(xr, xh, "S").l(xr, yc).c(cx, yc - ry, "W").c(p[0], p[1], dd, cut=g.cutdir())
    g.add(st, cap0="butt")


@glyph("h", 0x68)
def hh(g):
    T = g.T
    g.stem(T / 2, 0, g.asc, sb="f", st="l")
    g.arch(T, g.nw, g.xh, sb="f")


def _idot(g, x):
    dd = g.dotd
    g.dot(x, g.xh + g.T * 0.95 + dd / 2, dd)


@glyph("dotlessi", 0x131)
def dotlessi(g):
    g.stem(g.T / 2, 0, g.xh, sb="f", st="l")


@glyph("i", 0x69)
def i(g):
    dotlessi(g)
    _idot(g, g.T / 2)


def _j(g):
    T, h = g.T, g.h
    rx = g.nw * 0.3
    x = 0.0
    yb = g.desc + h / 2
    ry = -g.desc * 0.62
    st = g.P().m(x, g.xh, "S").l(x, yb + ry).c(x - rx, yb, "W").l(x - rx * 1.18, yb)
    g.add(st)
    g.serif(x, g.xh, T, "l", -1)


@glyph("dotlessj", 0x237)
def dotlessj(g):
    _j(g)


@glyph("j", 0x6A)
def j(g):
    _j(g)
    _idot(g, 0)


def _k(g, top, y_arm):
    T = g.T
    w = g.nw * (0.98 if g.case == "lc" else 1.0) if g.case == "lc" else g.Hw * 0.96
    yj = y_arm * 0.36
    ca, cb, half = g.dg(T * 0.5, yj, w * 0.97, y_arm, eb=1, wm=g.thin, cut0="N")
    f_ = 0.27
    xm, ym = ca + (cb - ca) * f_, yj + (y_arm - yj) * f_
    g.dg(xm, ym, w * 1.02, 0, eb=1)
    g.serif(w * 1.02 - half, 0, 0, "f", +1)
    g.serif(cb, y_arm, 0, "f", -1)


@glyph("k", 0x6B)
def k(g):
    g.stem(g.T / 2, 0, g.asc, sb="f", st="l")
    _k(g, g.asc, g.xh)


@glyph("l", 0x6C)
def l(g):
    g.stem(g.T / 2, 0, g.asc, sb="f", st="l")


@glyph("m", 0x6D)
def m(g):
    T = g.T
    span = (g.nw - T) * 0.93
    g.stem(T / 2, 0, g.xh, sb="f", st="l")
    g.arch(T, T + span, g.xh, sb="f")
    # the middle stem stays straight up to where the second arch branches,
    # otherwise the first arch's curve leaves a dent below the join
    g.stem(T + span - T / 2, T, g.xh * g.branch + T * 0.1, cap0="butt", cap1="butt")
    g.arch(T + span, T + 2 * span, g.xh, sb="f")


@glyph("n", 0x6E)
def n(g):
    T = g.T
    g.stem(T / 2, 0, g.xh, sb="f", st="l")
    g.arch(T, g.nw, g.xh, sb="f")


@glyph("o", 0x6F)
def o(g):
    g.oval(0, -g.os, g.ow, g.xh + g.os)


@glyph("p", 0x70)
def p(g):
    T = g.T
    g.stem(T / 2, g.desc, g.xh, sb="f", st="l")
    g.bowl(T, _bw(g), -g.os, g.xh + g.os)


@glyph("q", 0x71)
def q(g):
    T, w = g.T, _bw(g)
    g.bowl(w - T, 0, -g.os, g.xh + g.os, right=False)
    g.stem(w - T / 2, g.desc, g.xh, sb="f")


@glyph("r", 0x72)
def r(g):
    T, h = g.T, g.h
    rw = g.nw * 0.66
    g.stem(T / 2, 0, g.xh, sb="f", st="l")
    w0 = T * g.join
    yt = g.xh + g.os - h / 2
    st = g.P().m(T - w0 / 2, g.xh * g.branch, "N", wm=g.join).c(rw, yt - 3, -10, cut="N", wm=1.04)
    g.add(st, cap0="butt")


def _s(g, w, H, T):
    """Upper bowl, diagonal spine, lower bowl, drawn as one stroke.

    Heavy weights widen the letter and thin the spine, as a designer does, so
    the two counters stay open instead of closing to slits."""
    import math
    heavy = min(max((T / H - 0.17) / 0.12, 0.0), 1.0)
    w = w + T * 0.42 * heavy
    spine = 1.0 - 0.1 * heavy
    from .geometry import Pen, Stroke
    pen = Pen(hratio=g.pen.hratio * (1.0 - 0.2 * heavy), roundness=g.pen.k,   # lighter horizontals, open counters
              stress=g.pen.stress, angle=math.degrees(g.pen.angle))
    hf = pen.factor((1.0, 0.0))
    h, os = T * hf, g.os
    cx = w / 2
    top, bot = H + os - h / 2, -os + h / 2
    ym = (top + bot) / 2 + H * 0.012
    ru, rl = (top - ym) / 2, (ym - bot) / 2
    au, al = (w * 0.94 - T) / 2, (w - T) / 2
    cxu = w * 0.03 + T / 2 + au
    yu, yl = top - ru * 0.9, bot + rl * 0.92          # heights of the two side nodes
    # spine angle: steep enough that both bends stay round
    ang = -math.degrees(math.atan2(0.64 * ((yu - ym) + (ym - yl)) / 2, (au + al) / 2))
    a = g.ap_angle(26, 50)
    t1, d1 = g.arc_node(cxu, top - ru * 1.15, au, ru * 1.15, a)
    t2, d2 = g.arc_node(cx, bot + rl * 1.15, al, rl * 1.15, 180 + a)
    cut = g.cutdir()
    st = Stroke(pen, T)
    st.m(t1[0], t1[1], d1, cut=cut).c(cxu, top, "W").c(cxu - au, yu, "S")
    st.c(cx, ym, ang, w=T * spine, k=0.6).c(cx + al, yl, "S", k=0.6).c(cx, bot, "W")
    st.c(t2[0], t2[1], (-d2[0], -d2[1]), cut=cut)
    g.add(st)


@glyph("s", 0x73)
def s(g):
    _s(g, g.ow * 0.84, g.xh, g.T)


@glyph("t", 0x74)
def t(g):
    T, h = g.T, g.h
    bw = g.nw * 0.66
    xs = bw * 0.40
    r = bw * 0.54
    yb = -g.os + h / 2
    ytop = g.xh + (g.asc - g.xh) * 0.62
    st = g.P().m(xs, ytop, "S").l(xs, yb + r).c(xs + r, yb, "E").l(xs + r * 1.14, yb)
    g.add(st)
    g.bar(0, bw, g.xh - h / 2)


@glyph("u", 0x75)
def u(g):
    T, h = g.T, g.h
    w = g.nw
    w0 = T * g.join
    yb = -g.os + h / 2
    xt = (w - T) / 2 - w * 0.04 + T * 0.5
    ry = min((xt - T / 2) * 1.08, g.xh * 0.7)
    st = g.P().m(T / 2, g.xh, "S").l(T / 2, yb + ry).c(xt, yb, "E").c(w - T + w0 / 2, g.xh * (1 - g.branch), "N", wm=g.join)
    g.add(st, cap1="butt")
    g.serif(T / 2, g.xh, T, "l", -1)
    g.stem(w - T / 2, 0, g.xh, sb="r", st="l")


def _v(g, w, H, left_wm=1.0, right_wm=1.0):
    a = g.dg(0, H, w / 2, 0, ea=-1, wm=left_wm)
    b_ = g.dg(w, H, w / 2, 0, ea=1, wm=right_wm)
    g.serif(a[0], H, 0, "f", -1)
    g.serif(b_[0], H, 0, "f", -1)


@glyph("v", 0x76)
def v(g):
    _v(g, g.nw * 1.0, g.xh, 1.0, g.thin)


def _w(g, w, H):
    xs = [0, w * 0.265, w * 0.5, w * 0.735, w]
    a = g.dg(xs[0], H, xs[1], 0, ea=-1)
    g.dg(xs[2], H, xs[1], 0, wm=g.thin)
    g.dg(xs[2], H, xs[3], 0)
    b_ = g.dg(xs[4], H, xs[3], 0, ea=1, wm=g.thin)
    g.serif(a[0], H, 0, "f", -1)
    g.serif(b_[0], H, 0, "f", -1)


@glyph("w", 0x77)
def w(g):
    _w(g, g.nw * 1.52, g.xh)


def _x(g, w, H):
    a = g.dg(0, H, w, 0, ea=-1, eb=1)
    b_ = g.dg(w, H, 0, 0, ea=1, eb=-1, wm=g.thin)
    for x_, y_, up in ((a[0], H, -1), (a[1], 0, 1), (b_[0], H, -1), (b_[1], 0, 1)):
        g.serif(x_, y_, 0, "f", up)


@glyph("x", 0x78)
def x(g):
    _x(g, g.nw * 0.98, g.xh)


@glyph("y", 0x79)
def y(g):
    w = g.nw * 1.0
    xh = g.xh
    ca, cb, half = g.dg(w, xh, w * 0.16, g.desc, ea=1, eb=-1, wm=g.thin)
    yj = g.T * 0.15
    xj = cb + (ca - cb) * (yj - g.desc) / (xh - g.desc)
    a = g.dg(0, xh, xj, yj, ea=-1)
    g.serif(a[0], xh, 0, "f", -1)
    g.serif(ca, xh, 0, "f", -1)


def _z(g, w, H):
    h = g.h
    g.bar(0, w, H - h / 2, cap0="butt", cap1="butt")
    g.bar(0, w, h / 2, cap0="butt", cap1="butt")
    g.dg(w, H, 0, 0, ea=1, eb=-1)
    g.vserif(0, H - h / 2, True, False)
    g.vserif(w, h / 2, False, True)


@glyph("z", 0x7A)
def z(g):
    _z(g, g.nw * 0.9, g.xh)


# ---------------------------------------------------------------- capitals
def _dbowl(g, x0, x1, yt, yb, wm=1.0):
    """D-shaped bowl: two horizontals joined by a half round on the right."""
    T = g.T
    ry = (yt - yb) / 2
    r = min(ry * 1.02, (x1 - T / 2 - x0) * 0.82)
    xa = x1 - T / 2 - r
    st = g.P(wm).m(x0, yt, "E").l(xa, yt).c(x1 - T / 2, (yt + yb) / 2, "S").c(xa, yb, "W").l(x0, yb)
    g.add(st, cap0="butt", cap1="butt")


@glyph("A", 0x41, "uc")
def A(g):
    w = g.cap * 0.94 * g.wd
    H = g.cap
    a = g.dg(0, 0, w / 2, H, ea=-1, wm=g.thin)
    b_ = g.dg(w, 0, w / 2, H, ea=1)
    yb = H * 0.27
    f_ = yb / H
    g.bar(a[0] + (a[1] - a[0]) * f_, b_[0] + (b_[1] - b_[0]) * f_, yb, wm=0.94, cap0="butt", cap1="butt")
    g.serif(a[0], 0, 0, "f", 1)
    g.serif(b_[0], 0, 0, "f", 1)


@glyph("B", 0x42, "uc")
def B(g):
    T, h, H = g.T, g.h, g.cap
    w = g.Hw * 0.87
    ym = H * 0.535
    g.stem(T / 2, 0, H, sb="l", st="l")
    _dbowl(g, T / 2, w * 0.94, H - h / 2, ym)
    _dbowl(g, T / 2, w, ym, h / 2)


@glyph("C", 0x43, "uc")
def C(g):
    a = g.ap_angle(24, 50)
    g.open_arc(0, -g.os, g.Ow * 0.92, g.cap + g.os, a, a)


@glyph("D", 0x44, "uc")
def D(g):
    T, h, H = g.T, g.h, g.cap
    w = (g.Hw + g.Ow) / 2 * 0.98
    g.stem(T / 2, 0, H, sb="l", st="l")
    st = g.P().m(T / 2, H - h / 2, "E").l(w * 0.36, H - h / 2).c(w - T / 2, H / 2, "S").c(w * 0.36, h / 2, "W").l(T / 2, h / 2)
    g.add(st, cap0="butt", cap1="butt")


@glyph("E", 0x45, "uc")
def E(g):
    T, h, H = g.T, g.h, g.cap
    w = g.Hw * 0.8
    g.stem(T / 2, 0, H, sb="l", st="l")
    g.bar(T / 2, w, H - h / 2, cap0="butt")
    g.bar(T / 2, w * 0.92, H * 0.525, wm=0.96, cap0="butt")
    g.bar(T / 2, w, h / 2, cap0="butt")
    g.vserif(w, H - h / 2, True)
    g.vserif(w, h / 2, False)


@glyph("F", 0x46, "uc")
def F(g):
    T, h, H = g.T, g.h, g.cap
    w = g.Hw * 0.77
    g.stem(T / 2, 0, H, sb="f", st="l")
    g.bar(T / 2, w, H - h / 2, cap0="butt")
    g.bar(T / 2, w * 0.9, H * 0.5, wm=0.96, cap0="butt")
    g.vserif(w, H - h / 2, True)


@glyph("G", 0x47, "uc")
def Gc(g):
    T, h, H, os = g.T, g.h, g.cap, g.os
    w = g.Ow * 0.96
    cx, cy = w / 2, H / 2
    rx, ry = w / 2 - T / 2, (H + 2 * os) / 2 - h / 2
    p, d = g.arc_node(cx, cy, rx, ry, g.ap_angle(26, 50))
    yb = H * 0.44
    st = g.P().m(p[0], p[1], d, cut=g.cutdir()).c(cx, cy + ry, "W").c(cx - rx, cy, "S").c(cx, cy - ry, "E")
    st.c(w - T / 2, H * 0.3, "N").l(w - T / 2, yb + h / 2)
    g.add(st, cap1="butt")
    g.bar(w * 0.53, w - T / 2, yb, cap1="butt")


@glyph("H", 0x48, "uc")
def H(g):
    T, w = g.T, g.Hw
    g.stem(T / 2, 0, g.cap, sb="f", st="f")
    g.stem(w - T / 2, 0, g.cap, sb="f", st="f")
    g.bar(T / 2, w - T / 2, g.cap * 0.52, cap0="butt", cap1="butt")


@glyph("I", 0x49, "uc")
def I(g):
    g.stem(g.T / 2, 0, g.cap, sb="f", st="f")


@glyph("J", 0x4A, "uc")
def J(g):
    T, h = g.T, g.h
    w = g.Hw * 0.62
    xr = w - T / 2
    cx = xr / 2 + T * 0.1
    rx = xr - cx
    ry = g.cap * 0.3
    yc = -g.os + h / 2 + ry
    p, d = g.arc_node(cx, yc, rx, ry, 180 + g.ap_angle(18, 40), ccw=False)
    st = g.P().m(xr, g.cap, "S").l(xr, yc).c(cx, yc - ry, "W").c(p[0], p[1], d, cut=g.cutdir())
    g.add(st)
    g.serif(xr, g.cap, T, "f", -1)


@glyph("K", 0x4B, "uc")
def K(g):
    g.stem(g.T / 2, 0, g.cap, sb="f", st="f")
    _k(g, g.cap, g.cap)


@glyph("L", 0x4C, "uc")
def L(g):
    T = g.T
    g.stem(T / 2, 0, g.cap, sb="l", st="f")
    g.bar(T / 2, g.Hw * 0.76, g.h / 2, cap0="butt")
    g.vserif(g.Hw * 0.76, g.h / 2, False)


@glyph("M", 0x4D, "uc")
def M(g):
    T, H = g.T, g.cap
    w = g.Hw * 1.22
    g.stem(T / 2, 0, H, wm=0.94, sb="f", st="l")
    g.stem(w - T / 2, 0, H, wm=0.94, sb="f", st="r")
    g.dg(0, H, w / 2, 0, ea=-1, wm=0.92)
    g.dg(w, H, w / 2, 0, ea=1, wm=0.92 * g.thin)


@glyph("N", 0x4E, "uc")
def N(g):
    T, H = g.T, g.cap
    w = g.Hw * 1.03
    g.stem(T / 2, 0, H, wm=0.94 * g.thin, sb="f", st="l")
    g.stem(w - T / 2, 0, H, wm=0.94 * g.thin, st="f")
    g.dg(0, H, w, 0, ea=-1, eb=1, wm=0.96)


@glyph("O", 0x4F, "uc")
def O(g):
    g.oval(0, -g.os, g.Ow, g.cap + g.os)


@glyph("P", 0x50, "uc")
def P(g):
    T, h, H = g.T, g.h, g.cap
    g.stem(T / 2, 0, H, sb="f", st="l")
    _dbowl(g, T / 2, g.Hw * 0.86, H - h / 2, H * 0.44)


@glyph("Q", 0x51, "uc")
def Q(g):
    O(g)
    w = g.Ow
    g.add(g.P().m(w * 0.56, g.cap * 0.2).l(w * 0.96, -g.cap * 0.07), "butt", "butt")


@glyph("R", 0x52, "uc")
def R(g):
    T, h, H = g.T, g.h, g.cap
    w = g.Hw * 0.9
    yb = H * 0.47
    g.stem(T / 2, 0, H, sb="f", st="l")
    _dbowl(g, T / 2, w * 0.95, H - h / 2, yb)
    a = g.dg(w * 0.5, yb, w * 1.02, 0, eb=1)
    g.serif(a[1], 0, 0, "f", 1)


@glyph("S", 0x53, "uc")
def S(g):
    _s(g, g.Hw * 0.86, g.cap, g.T)


@glyph("T", 0x54, "uc")
def Tc(g):
    w = g.Hw * 0.98
    g.bar(0, w, g.cap - g.h / 2)
    g.stem(w / 2, 0, g.cap, sb="f", cap1="butt")
    g.vserif(0, g.cap - g.h / 2, True, False)
    g.vserif(w, g.cap - g.h / 2, True, True)


@glyph("U", 0x55, "uc")
def U(g):
    T, h, H = g.T, g.h, g.cap
    w = g.Hw * 0.98
    yb = -g.os + h / 2
    ry = min((w / 2 - T / 2) * 1.05, H * 0.5)
    st = g.P().m(T / 2, H, "S").l(T / 2, yb + ry).c(w / 2, yb, "E").c(w - T / 2, yb + ry, "N").l(w - T / 2, H)
    g.add(st)
    g.serif(T / 2, H, T, "f", -1)
    g.serif(w - T / 2, H, T, "f", -1)


@glyph("V", 0x56, "uc")
def V(g):
    _v(g, g.cap * 0.92 * g.wd, g.cap, 1.0, g.thin)


@glyph("W", 0x57, "uc")
def W(g):
    _w(g, g.cap * 1.36 * g.wd, g.cap)


@glyph("X", 0x58, "uc")
def X(g):
    _x(g, g.cap * 0.88 * g.wd, g.cap)


@glyph("Y", 0x59, "uc")
def Y(g):
    T, H = g.T, g.cap
    w = g.cap * 0.9 * g.wd
    ym = H * 0.42
    a = g.dg(0, H, w / 2, ym, ea=-1)
    b_ = g.dg(w, H, w / 2, ym, ea=1, wm=g.thin)
    g.stem(w / 2, 0, ym + T * 0.4, sb="f", cap1="butt")
    g.serif(a[0], H, 0, "f", -1)
    g.serif(b_[0], H, 0, "f", -1)


@glyph("Z", 0x5A, "uc")
def Z(g):
    _z(g, g.Hw * 0.92, g.cap)


# ---------------------------------------------------------------- figures
def _fw(g):
    return g.fw * 0.94


@glyph("zero", 0x30, "fig")
def zero(g):
    g.oval(0, -g.os, _fw(g), g.cap + g.os)


@glyph("zero.zero", None, "fig")
def zero_slash(g):
    zero(g)
    w = _fw(g)
    g.add(g.P(0.7).m(w * 0.3, g.cap * 0.2).l(w * 0.7, g.cap * 0.8), "butt", "butt")


@glyph("one", 0x31, "fig")
def one(g):
    T, H = g.T, g.cap
    w = _fw(g)
    xs = w * 0.56
    g.stem(xs, 0, H, sb="f", cap1="butt")
    g.dg(xs + T / 2, H, w * 0.08, H * 0.74, ea=1, eb=-1, wm=0.86)


@glyph("two", 0x32, "fig")
def two(g):
    T, h, H = g.T, g.h, g.cap
    w = _fw(g)
    cx = w / 2
    rx = w / 2 - T / 2
    top = H + g.os - h / 2
    ry = H * 0.27
    cy = top - ry
    p, d = g.arc_node(cx, cy, rx, ry, 180 - g.ap_angle(14, 40), ccw=False)
    xb = T * 0.72
    # one continuous stroke: the bowl rolls straight into the diagonal, the
    # same pen all the way, so there is no step where they meet
    nk = (w * 0.6, H * 0.4)
    dn = norm((xb - nk[0], h * 0.5 - nk[1]))
    st = g.P().m(p[0], p[1], d, cut=g.cutdir()).c(cx, top, "E").c(cx + rx, cy, "S", k=0.6).c(nk[0], nk[1], dn, k=0.62)
    st.l(xb, h * 0.5, cut="E")
    g.add(st, cap1="butt")
    g.bar(0, w, h / 2, cap0="butt")


@glyph("three", 0x33, "fig")
def three(g):
    T, h, H = g.T, g.h, g.cap
    w = _fw(g) * 0.98
    ym = H * 0.535
    top, bot = H + g.os - h / 2, -g.os + h / 2
    wu = w * 0.93
    cxu, rxu = wu / 2 + w * 0.02, wu / 2 - T / 2
    ryu = (top - ym) / 2
    a = g.ap_angle(22, 46)
    p, d = g.arc_node(cxu, top - ryu * 1.2, rxu, ryu * 1.2, 180 - a, ccw=False)
    xm = w * 0.4
    st = g.P().m(p[0], p[1], d, cut=g.cutdir()).c(cxu, top, "E").c(cxu + rxu, ym + ryu, "S").c(xm, ym, "W")
    g.add(st, cap1="butt")
    cxl, rxl = w / 2, w / 2 - T / 2
    ryl = (ym - bot) / 2
    p2, d2 = g.arc_node(cxl, bot + ryl * 1.2, rxl, ryl * 1.2, 180 + a, ccw=False)
    st = g.P().m(xm, ym, "E").c(cxl + rxl, bot + ryl, "S").c(cxl, bot, "W").c(p2[0], p2[1], d2, cut=g.cutdir())
    g.add(st, cap0="butt")


@glyph("four", 0x34, "fig")
def four(g):
    T, h, H = g.T, g.h, g.cap
    w = _fw(g) * 1.06
    xs = w * 0.71
    yb = H * 0.25
    g.stem(xs, 0, H, sb="f", cap1="butt")
    ca, cb, half = g.dg(xs + T / 2, H, 0, yb - h / 2, ea=1, eb=-1, wm=0.95)
    # the bar's left end follows the diagonal's outer edge, so nothing pokes out
    xa_l, xb_l = ca - half, cb - half
    y0, y1 = yb - h / 2, yb + h / 2

    def edge(y):
        return xb_l + (xa_l - xb_l) * (y - y0) / (H - y0)
    g.poly([(edge(y0), y0), (w, y0), (w, y1), (edge(y1), y1)])


@glyph("five", 0x35, "fig")
def five(g):
    T, h, H = g.T, g.h, g.cap
    w = _fw(g) * 0.97
    xl = w * 0.13 + T / 2
    g.bar(xl, w * 0.92, H - h / 2, cap0="butt")
    g.stem(xl, H * 0.47, H, cap0="butt", cap1="butt")
    bot = -g.os + h / 2
    ytb = H * 0.635 - h / 2
    cx = w * 0.47
    rx = w - T / 2 - cx
    ry = (ytb - bot) / 2
    p, d = g.arc_node(cx - w * 0.02, bot + ry * 1.15, rx, ry * 1.15, 180 + g.ap_angle(22, 46), ccw=False)
    st = g.P().m(xl - T / 2 + T * g.join / 2, H * 0.49, 78, wm=g.join).c(cx, ytb, "E").c(w - T / 2, bot + ry, "S").c(cx - w * 0.02, bot, "W")
    st.c(p[0], p[1], d, cut=g.cutdir())
    g.add(st, cap0="butt")


@glyph("six", 0x36, "fig")
def six(g):
    T, h, H = g.T, g.h, g.cap
    w = _fw(g)
    yo = H * 0.63
    g.oval(0, -g.os, w, yo)
    top = H + g.os - h / 2
    cx = w * 0.53
    yl = H * 0.42
    rx, ry = cx - T / 2, top - yl
    p, d = g.arc_node(cx, yl, rx * 0.98, ry, min(g.ap_angle(34, 58) + max(T - 90, 0) * 0.2, 72))
    # the stem runs down into the bowl's widest point and stops where the bowl's
    # own side takes over, so the two outlines meet tangent with no ledge
    st = g.P().m(p[0], p[1], d, cut=g.cutdir()).c(cx, top, "W").c(T / 2, yl, "S").l(T / 2, yo / 2 - g.os / 2)
    g.add(st, cap1="butt")


@glyph("seven", 0x37, "fig")
def seven(g):
    w = _fw(g) * 0.96
    g.bar(0, w, g.cap - g.h / 2, cap0="butt", cap1="butt")
    g.dg(w, g.cap, w * 0.36, 0, ea=1)


@glyph("eight", 0x38, "fig")
def eight(g):
    h, H = g.h, g.cap
    w = _fw(g)
    ym = H * 0.535
    g.oval(w * 0.045, ym - h / 2, w * 0.955, H + g.os)
    g.oval(0, -g.os, w, ym + h / 2)


@glyph("nine", 0x39, "fig")
def nine(g):
    g.rotate(six, _fw(g), g.cap)
