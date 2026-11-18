"""Punctuation, symbols, accents and the extra Latin letters."""
from __future__ import annotations

from .geometry import norm
from .glyphs_latin import GLYPHS, glyph, _e, _s, _fw
from . import glyphs_latin as L


# ---------------------------------------------------------------- punctuation
def _period(g, x=None, y=None):
    d = g.dotd
    g.dot(d / 2 if x is None else x, d / 2 if y is None else y, d)
    return d


def _comma(g, x=None, y=None):
    d = g.dotd
    cx, cy = (d / 2 if x is None else x), (d / 2 if y is None else y)
    g.dot(cx, cy, d)
    r = d / 2
    g.poly([(cx + r * 0.92, cy), (cx + r * 0.92, cy - r * 0.4), (cx - r * 0.55, cy - d * 1.25), (cx - r * 1.0, cy - d * 1.25), (cx - r * 0.1, cy - r * 0.6)])


@glyph("period", 0x2E, "punct")
def period(g):
    _period(g)


@glyph("comma", 0x2C, "punct")
def comma(g):
    _comma(g)


@glyph("colon", 0x3A, "punct")
def colon(g):
    d = _period(g)
    _period(g, d / 2, g.xh - d / 2)


@glyph("semicolon", 0x3B, "punct")
def semicolon(g):
    d = g.dotd
    _comma(g)
    _period(g, d / 2, g.xh - d / 2)


@glyph("ellipsis", 0x2026, "punct")
def ellipsis(g):
    d = g.dotd
    for i in range(3):
        _period(g, d / 2 + i * d * 2.6, d / 2)


@glyph("exclam", 0x21, "punct")
def exclam(g):
    d = g.dotd
    g.dot(d / 2, d / 2, d)
    g.stem(d / 2, d * 1.9, g.cap, wm=1.05, cap0="butt")


@glyph("exclamdown", 0xA1, "punct")
def exclamdown(g):
    g.rotate(exclam, g.dotd, g.xh + 0.0)


@glyph("question", 0x3F, "punct")
def question(g):
    T, h, H = g.T, g.h, g.cap
    w = g.fw * 0.82
    d = g.dotd
    cx = w / 2
    top = H + g.os - h / 2
    ry = H * 0.25
    rx = w / 2 - T / 2
    p, dd = g.arc_node(cx, top - ry, rx, ry, 180 - g.ap_angle(14, 40), ccw=False)
    st = g.P().m(p[0], p[1], dd, cut=g.cutdir()).c(cx, top, "E").c(cx + rx, top - ry, "S")
    st.c(cx, H * 0.36, "S", k=0.6).l(cx, d * 1.95)
    g.add(st, cap1="butt")
    g.dot(cx, d / 2, d)


@glyph("questiondown", 0xBF, "punct")
def questiondown(g):
    g.rotate(question, g.fw * 0.82, g.xh + 0.0)


def _tick(g, x, y0, y1):
    g.add(g.P(0.92).m(x, y0, "N").l(x, y1), "butt", "butt")


@glyph("quotesingle", 0x27, "punct")
def quotesingle(g):
    _tick(g, g.T / 2, g.cap * 0.64, g.cap)


@glyph("quotedbl", 0x22, "punct")
def quotedbl(g):
    _tick(g, g.T / 2, g.cap * 0.64, g.cap)
    _tick(g, g.T / 2 + g.T * 2.1, g.cap * 0.64, g.cap)


def _qr(g, x=0.0):
    d = g.dotd
    _comma(g, x + d / 2, g.cap - d / 2)


def _ql(g, x=0.0):
    d = g.dotd
    cons = g.sandbox(_comma)
    y0 = g.cap - d * 1.25
    g.shape.contours.extend(c.transformed(lambda p: (x + d - p[0], y0 + d / 2 - p[1] + d / 2)) for c in cons)


@glyph("quoteright", 0x2019, "punct")
def quoteright(g):
    _qr(g)


@glyph("quoteleft", 0x2018, "punct")
def quoteleft(g):
    _ql(g)


@glyph("quotedblright", 0x201D, "punct")
def quotedblright(g):
    _qr(g)
    _qr(g, g.dotd * 1.75)


@glyph("quotedblleft", 0x201C, "punct")
def quotedblleft(g):
    _ql(g)
    _ql(g, g.dotd * 1.75)


@glyph("quotesinglbase", 0x201A, "punct")
def quotesinglbase(g):
    _comma(g)


@glyph("quotedblbase", 0x201E, "punct")
def quotedblbase(g):
    d = g.dotd
    _comma(g)
    _comma(g, d / 2 + d * 1.75)


@glyph("hyphen", 0x2D, "punct")
def hyphen(g):
    g.bar(0, g.nw * 0.62, g.xh * 0.5, wm=1.05)


@glyph("hyphen.case", None, "punct")
def hyphen_case(g):
    g.bar(0, g.nw * 0.62, g.cap * 0.5, wm=1.05)


@glyph("endash", 0x2013, "punct")
def endash(g):
    g.bar(0, 500 * g.wd, g.xh * 0.5)


@glyph("emdash", 0x2014, "punct")
def emdash(g):
    g.bar(0, 900 * g.wd, g.xh * 0.5)


@glyph("underscore", 0x5F, "punct")
def underscore(g):
    g.bar(0, 520 * g.wd, g.desc * 0.55, cap0="butt", cap1="butt")


def _paren(g):
    w = g.T * 1.2 + g.cap * 0.2
    yt, yb = g.asc + 10, g.desc * 0.75
    ym = (yt + yb) / 2
    st = g.P(0.9).m(w, yt, 228).c(g.T * 0.45, ym, "S").c(w, yb, -48)
    g.add(st)
    return w


@glyph("parenleft", 0x28, "punct")
def parenleft(g):
    _paren(g)


@glyph("parenright", 0x29, "punct")
def parenright(g):
    g.mirror_x(_paren, g.T * 1.2 + g.cap * 0.2)


def _bracket(g):
    T, h = g.T * 0.9, g.h * 0.9
    w = g.T * 1.1 + g.cap * 0.16
    yt, yb = g.asc + 10, g.desc * 0.75
    st = g.P(0.9).m(w, yt - h / 2).l(T / 2, yt - h / 2).l(T / 2, yb + h / 2).l(w, yb + h / 2)
    g.add(st, "butt", "butt")


@glyph("bracketleft", 0x5B, "punct")
def bracketleft(g):
    _bracket(g)


@glyph("bracketright", 0x5D, "punct")
def bracketright(g):
    g.mirror_x(_bracket, g.T * 1.1 + g.cap * 0.16)


def _brace(g):
    h = g.h * 0.85
    w = g.T * 1.3 + g.cap * 0.22
    yt, yb = g.asc + 10, g.desc * 0.75
    ym = (yt + yb) / 2
    xm = w * 0.52
    r = w * 0.48
    g.add(g.P(0.85).m(w, yt - h / 2, "W").c(xm, yt - h / 2 - r, "S").l(xm, ym + r).c(h * 0.2, ym, "W"), "butt", "butt")
    g.add(g.P(0.85).m(h * 0.2, ym, "E").c(xm, ym - r, "S").l(xm, yb + h / 2 + r).c(w, yb + h / 2, "E"), "butt", "butt")


@glyph("braceleft", 0x7B, "punct")
def braceleft(g):
    _brace(g)


@glyph("braceright", 0x7D, "punct")
def braceright(g):
    g.mirror_x(_brace, g.T * 1.3 + g.cap * 0.22)


def _slash(g):
    w = g.cap * 0.42
    g.dg(0, g.desc * 0.5, w, g.asc, ea=-1, eb=1, wm=0.92)


@glyph("slash", 0x2F, "punct")
def slash(g):
    _slash(g)


@glyph("backslash", 0x5C, "punct")
def backslash(g):
    g.mirror_x(_slash, g.cap * 0.42)


@glyph("bar", 0x7C, "punct")
def bar_(g):
    g.stem(g.T / 2, g.desc, g.asc + 20, wm=0.92, cap0="butt", cap1="butt")


def _guil(g, x=0.0, hgt=None):
    hgt = hgt or g.xh * 0.3
    w = hgt * 0.95
    yc = g.xh * 0.5
    g.add(g.P(0.86).m(x + w, yc + hgt).l(x + g.T * 0.3, yc).l(x + w, yc - hgt), "butt", "butt")


@glyph("guilsinglleft", 0x2039, "punct")
def guilsinglleft(g):
    _guil(g)


@glyph("guilsinglright", 0x203A, "punct")
def guilsinglright(g):
    g.mirror_x(_guil, g.xh * 0.285)


def _guil2(g):
    _guil(g)
    _guil(g, g.xh * 0.32)


@glyph("guillemetleft", 0xAB, "punct")
def guillemetleft(g):
    _guil2(g)


@glyph("guillemetright", 0xBB, "punct")
def guillemetright(g):
    g.mirror_x(_guil2, g.xh * 0.605)


@glyph("periodcentered", 0xB7, "punct")
def periodcentered(g):
    _period(g, g.dotd / 2, g.xh * 0.5)


@glyph("bullet", 0x2022, "punct")
def bullet(g):
    d = g.dotd * 1.7
    from .geometry import ellipse
    g.put([ellipse(d / 2, g.xh * 0.5, d / 2, d / 2)])


# ---------------------------------------------------------------- math and symbols
def _mw(g):
    return g.fw * 0.88


def _axis(g):
    return g.cap * 0.48


@glyph("plus", 0x2B, "sym")
def plus(g):
    w = _mw(g)
    g.bar(0, w, _axis(g))
    g.stem(w / 2, _axis(g) - w / 2, _axis(g) + w / 2, wm=g.hf)


@glyph("minus", 0x2212, "sym")
def minus(g):
    g.bar(0, _mw(g), _axis(g))


@glyph("equal", 0x3D, "sym")
def equal(g):
    gap = g.cap * 0.13
    g.bar(0, _mw(g), _axis(g) + gap)
    g.bar(0, _mw(g), _axis(g) - gap)


@glyph("multiply", 0xD7, "sym")
def multiply(g):
    w = _mw(g) * 0.84
    y0, y1 = _axis(g) - w / 2, _axis(g) + w / 2
    g.add(g.P(0.9).m(0, y0).l(w, y1))
    g.add(g.P(0.9).m(0, y1).l(w, y0))


@glyph("divide", 0xF7, "sym")
def divide(g):
    w = _mw(g)
    d = g.dotd * 0.95
    g.bar(0, w, _axis(g))
    g.dot(w / 2, _axis(g) + g.cap * 0.22, d)
    g.dot(w / 2, _axis(g) - g.cap * 0.22, d)


def _less(g):
    w = _mw(g)
    hgt = g.cap * 0.26
    g.add(g.P(0.92).m(w, _axis(g) + hgt).l(g.T * 0.4, _axis(g)).l(w, _axis(g) - hgt), "butt", "butt")


@glyph("less", 0x3C, "sym")
def less(g):
    _less(g)


@glyph("greater", 0x3E, "sym")
def greater(g):
    g.mirror_x(_less, _mw(g))


@glyph("asterisk", 0x2A, "sym")
def asterisk(g):
    import math
    r = g.cap * 0.19
    cx, cy = r, g.cap - r
    for a in (90, 30, 150):
        dx, dy = r * math.cos(math.radians(a)), r * math.sin(math.radians(a))
        g.add(g.P(0.78).m(cx - dx, cy - dy).l(cx + dx, cy + dy))


@glyph("numbersign", 0x23, "sym")
def numbersign(g):
    w = g.fw
    H = g.cap
    for x in (w * 0.2, w * 0.62):
        g.dg(x, 0, x + w * 0.16, H, wm=0.82)
    for y in (H * 0.33, H * 0.67):
        g.bar(0, w, y, wm=0.9)


@glyph("asciicircum", 0x5E, "sym")
def asciicircum(g):
    w = g.fw * 0.78
    g.add(g.P(0.86).m(0, g.cap * 0.52).l(w / 2, g.cap).l(w, g.cap * 0.52), "butt", "butt")


@glyph("asciitilde", 0x7E, "sym")
def asciitilde(g):
    w = _mw(g)
    yc, a = _axis(g), g.cap * 0.075
    st = g.P(0.95).m(0, yc - a * 0.7, 72).c(w * 0.27, yc + a, "E").c(w * 0.5, yc, -32).c(w * 0.73, yc - a, "E").c(w, yc + a * 0.7, 72)
    g.add(st)


@glyph("degree", 0xB0, "sym")
def degree(g):
    d = g.cap * 0.36
    g.oval(0, g.cap - d + g.os, d, g.cap + g.os, wm=0.7)


@glyph("at", 0x40, "sym")
def at(g):
    T = g.T * 0.74
    h = T * g.hf
    R = g.cap * 0.62
    cx, cy = R, g.cap * 0.42
    ri = R * 0.44
    xi = cx + ri - T * 0.2
    g.oval(cx - ri - T * 0.2, cy - ri, cx + ri - T * 0.2, cy + ri, wm=0.74)
    rx, ry = R - T / 2, R - h / 2
    p, d = g.arc_node(cx, cy, rx, ry, -52, ccw=False)
    st = g.P(0.74).m(p[0], p[1], d).c(cx, cy - ry, "W").c(cx - rx, cy, "N").c(cx, cy + ry, "E").c(cx + rx, cy, "S")
    st.c(cx + rx * 0.72, cy - ri + h / 2, "W", k=0.6).c(xi, cy - ri * 0.4, "N", k=0.6).l(xi, cy + ri)
    g.add(st, cap1="butt")


@glyph("ampersand", 0x26, "sym")
def ampersand(g):
    T, h, H = g.T, g.h, g.cap
    w = g.Hw * 1.02
    top, bot = H + g.os - h / 2, -g.os + h / 2
    st = g.P().m(w, 0, cut="E").l(w * 0.3, H * 0.66)
    st.c(w * 0.2, H * 0.8, "N", k=0.6).c(w * 0.4, top, "E").c(w * 0.6, H * 0.8, "S")
    st.c(w * 0.3, H * 0.44, 215).c(T * 0.5, H * 0.22, "S").c(w * 0.4, bot, "E").c(w * 0.86, H * 0.42, 68)
    g.add(st, cap0="butt")


@glyph("dollar", 0x24, "fig")
def dollar(g):
    w = _fw(g) * 0.96
    _s(g, w, g.cap, g.T)
    g.stem(w / 2, -g.cap * 0.1, g.cap * 1.1, wm=0.62, cap0="butt", cap1="butt")


@glyph("cent", 0xA2, "fig")
def cent(g):
    L.c(g)
    w = g.ow * 0.93
    g.stem(w * 0.52, -g.xh * 0.16, g.xh * 1.16, wm=0.62, cap0="butt", cap1="butt")


@glyph("Euro", 0x20AC, "fig")
def euro(g):
    off = g.fw * 0.12
    a = g.ap_angle(24, 50)
    s2 = g.sub(1, 1, dx=off)
    s2.open_arc(0, -g.os, g.Ow * 0.86, g.cap + g.os, a, a)
    for y in (g.cap * 0.58, g.cap * 0.42):
        g.bar(0, g.Ow * 0.5, y, wm=0.85, cap0="butt", cap1="butt")


@glyph("sterling", 0xA3, "fig")
def sterling(g):
    T, h, H = g.T, g.h, g.cap
    w = _fw(g)
    xs = w * 0.36
    top = H + g.os - h / 2
    rx = w * 0.92 - T / 2 - (xs + w * 0.26)
    cx = xs + w * 0.26
    ry = H * 0.3
    p, d = g.arc_node(cx, top - ry, w * 0.9 - T / 2 - cx, ry, g.ap_angle(24, 46))
    st = g.P().m(p[0], p[1], d, cut=g.cutdir()).c(cx, top, "W").c(xs, top - ry, "S").l(xs, h / 2)
    g.add(st, cap1="butt")
    g.bar(0, w, h / 2, cap0="butt")
    g.bar(w * 0.06, w * 0.72, H * 0.45, wm=0.9, cap0="butt", cap1="butt")


@glyph("yen", 0xA5, "fig")
def yen(g):
    L.Y(g)
    w = g.cap * 0.9 * g.wd
    for y in (g.cap * 0.36, g.cap * 0.2):
        g.bar(w * 0.14, w * 0.86, y, wm=0.8, cap0="butt", cap1="butt")


@glyph("percent", 0x25, "fig")
def percent(g):
    H = g.cap
    d = H * 0.44
    w = d * 2 + H * 0.2
    wm = 0.74
    g.oval(0, H - d + g.os, d * 0.86, H + g.os, wm=wm)
    g.oval(w - d * 0.86, -g.os, w, d - g.os, wm=wm)
    g.dg(w * 0.24, 0, w * 0.76, H, wm=0.8)


def _circled(g, fn, case):
    R = g.cap * 0.56
    cy = g.cap * 0.5
    g.oval(0, cy - R, 2 * R, cy + R, wm=0.55)
    k = 0.5
    inner = g.sub(k, 0.6, case=case)
    cons = inner.sandbox(fn)
    xs = [p[0] for c in cons for p in c.flat(3)]
    ys = [p[1] for c in cons for p in c.flat(3)]
    dx, dy = R - (min(xs) + max(xs)) / 2, cy - (min(ys) + max(ys)) / 2
    g.shape.contours.extend(c.transformed(lambda p: (p[0] + dx, p[1] + dy)) for c in cons)


@glyph("copyright", 0xA9, "sym")
def copyright_(g):
    _circled(g, L.C, "uc")


@glyph("registered", 0xAE, "sym")
def registered(g):
    _circled(g, L.R, "uc")


@glyph("trademark", 0x2122, "sym")
def trademark(g):
    k = 0.42
    t = g.sub(k, 0.6, dy=g.cap * (1 - k), case="uc")
    L.Tc(t)
    m = g.sub(k, 0.6, dx=g.Hw * k * 1.25, dy=g.cap * (1 - k), case="uc")
    L.M(m)


# ---------------------------------------------------------------- accents (centred on x = 0)
def _ay(g):
    return g.xh + g.T * 0.9


@glyph("grave", 0x60, "accent")
def grave(g):
    y = _ay(g)
    g.add(g.P(0.86).m(-g.xh * 0.13, y + g.xh * 0.25).l(g.xh * 0.07, y), "butt", "butt")


@glyph("acute", 0xB4, "accent")
def acute(g):
    y = _ay(g)
    g.add(g.P(0.86).m(g.xh * 0.13, y + g.xh * 0.25).l(-g.xh * 0.07, y), "butt", "butt")


@glyph("circumflex", 0x2C6, "accent")
def circumflex(g):
    y = _ay(g)
    w = g.xh * 0.21
    g.add(g.P(0.8).m(-w, y).l(0, y + g.xh * 0.2).l(w, y), "butt", "butt")


@glyph("caron", 0x2C7, "accent")
def caron(g):
    y = _ay(g)
    w = g.xh * 0.21
    g.add(g.P(0.8).m(-w, y + g.xh * 0.2).l(0, y).l(w, y + g.xh * 0.2), "butt", "butt")


@glyph("tilde", 0x2DC, "accent")
def tilde(g):
    y = _ay(g) + g.xh * 0.1
    w = g.xh * 0.3
    a = g.xh * 0.055
    st = g.P(0.8).m(-w, y - a * 0.6, 70).c(-w * 0.46, y + a, "E").c(0, y, -30).c(w * 0.46, y - a, "E").c(w, y + a * 0.6, 70)
    g.add(st)


@glyph("dieresis", 0xA8, "accent")
def dieresis(g):
    d = g.dotd * 0.9
    y = _ay(g) + d / 2
    g.dot(-d * 0.95, y, d)
    g.dot(d * 0.95, y, d)


@glyph("dotaccent", 0x2D9, "accent")
def dotaccent(g):
    d = g.dotd
    g.dot(0, g.xh + g.T * 0.95 + d / 2, d)


@glyph("ring", 0x2DA, "accent")
def ring(g):
    y = _ay(g) - g.T * 0.25
    r = g.xh * 0.15
    g.oval(-r, y, r, y + 2 * r, wm=0.62)


@glyph("macron", 0xAF, "accent")
def macron(g):
    y = _ay(g) + g.h * 0.6
    g.bar(-g.xh * 0.24, g.xh * 0.24, y, wm=0.86, cap0="butt", cap1="butt")


@glyph("cedilla", 0xB8, "accent")
def cedilla(g):
    T = g.T * 0.62
    st = g.P(0.62).m(0, 0, "S").l(0, -g.xh * 0.1).c(g.xh * 0.02, -g.xh * 0.12, "E").c(g.xh * 0.1, -g.xh * 0.2, "S")
    st.c(-g.xh * 0.02, -g.xh * 0.3, "W").l(-g.xh * 0.1, -g.xh * 0.3)
    g.add(st, cap0="butt")


# ---------------------------------------------------------------- extra letters
@glyph("oslash", 0xF8)
def oslash(g):
    L.o(g)
    g.dg(g.ow * 0.14, -g.xh * 0.1, g.ow * 0.86, g.xh * 1.1, wm=0.66)


@glyph("Oslash", 0xD8, "uc")
def Oslash(g):
    L.O(g)
    g.dg(g.Ow * 0.14, -g.cap * 0.07, g.Ow * 0.86, g.cap * 1.07, wm=0.66)


@glyph("ae", 0xE6)
def ae(g):
    L._a_double(g)
    off = g.nw * 0.97 - g.T
    cons = g.sandbox(_e)
    g.shape.contours.extend(c.transformed(lambda p: (p[0] + off, p[1])) for c in cons)


@glyph("oe", 0x153)
def oe(g):
    L.o(g)
    off = g.ow - g.T
    cons = g.sandbox(_e)
    g.shape.contours.extend(c.transformed(lambda p: (p[0] + off, p[1])) for c in cons)


@glyph("AE", 0xC6, "uc")
def AE(g):
    T, h, H = g.T, g.h, g.cap
    xe = g.cap * 0.52 * g.wd
    w = xe + g.Hw * 0.74
    a = g.dg(0, 0, xe, H, ea=-1, eb=0, wm=g.thin)
    g.stem(xe + T * 0.3, 0, H, cap0="butt", cap1="butt")
    yb = H * 0.27
    g.bar(a[0] + (a[1] - a[0]) * yb / H, xe, yb, wm=0.94, cap0="butt", cap1="butt")
    g.bar(xe, w, H - h / 2, cap0="butt")
    g.bar(xe, w * 0.95, H * 0.525, wm=0.96, cap0="butt")
    g.bar(xe, w, h / 2, cap0="butt")


@glyph("OE", 0x152, "uc")
def OE(g):
    T, h, H = g.T, g.h, g.cap
    L.O(g)
    xe = g.Ow - T / 2
    w = xe + g.Hw * 0.68
    g.stem(xe, 0, H, cap0="butt", cap1="butt")
    g.bar(xe, w, H - h / 2, cap0="butt")
    g.bar(xe, w * 0.96, H * 0.525, wm=0.96, cap0="butt")
    g.bar(xe, w, h / 2, cap0="butt")


@glyph("germandbls", 0xDF)
def germandbls(g):
    T, h = g.T, g.h
    w = g.nw * 1.02
    top = g.asc + g.os * 0.5 - h / 2
    bot = -g.os + h / 2
    xm = T / 2 + (w * 0.84 - T) / 2
    ym = g.xh * 0.98
    st = g.P().m(T / 2, 0, "N").l(T / 2, top - (xm - T / 2)).c(xm, top, "E").c(w * 0.84 - T / 2, (top + ym) / 2, "S").c(w * 0.5, ym, "W")
    g.add(st, cap1="butt")
    st = g.P().m(w * 0.5, ym, "E").c(w - T / 2, (ym + bot) / 2, "S").c(w * 0.56, bot, "W").l(T * 1.9, bot)
    g.add(st, cap0="butt")


@glyph("lslash", 0x142)
def lslash(g):
    T = g.T
    g.stem(T * 1.1, 0, g.asc)
    g.dg(0, g.asc * 0.4, T * 2.2, g.asc * 0.6, wm=0.8, cut="N")


@glyph("Lslash", 0x141, "uc")
def Lslash(g):
    T = g.T
    cons = g.sandbox(L.L)
    g.shape.contours.extend(c.transformed(lambda p: (p[0] + T * 0.6, p[1])) for c in cons)
    g.dg(0, g.cap * 0.36, T * 2.6, g.cap * 0.56, wm=0.8, cut="N")


@glyph("eth", 0xF0)
def eth(g):
    T = g.T
    L.o(g)
    w = g.ow
    st = g.P().m(w - T / 2, g.xh * 0.5, "N").c(w * 0.32, g.asc, 150)
    g.add(st, cap0="butt")
    g.dg(w * 0.3, g.asc * 0.84, w * 0.8, g.asc * 0.96, wm=0.6, cut="N")


@glyph("thorn", 0xFE)
def thorn(g):
    T = g.T
    g.stem(T / 2, g.desc, g.asc)
    g.bowl(T, L._bw(g), -g.os, g.xh + g.os)


@glyph("Thorn", 0xDE, "uc")
def Thorn(g):
    T, h, H = g.T, g.h, g.cap
    g.stem(T / 2, 0, H)
    L._dbowl(g, T / 2, g.Hw * 0.84, H * 0.8, H * 0.24)


@glyph("Eth", 0xD0, "uc")
def Eth(g):
    T = g.T
    cons = g.sandbox(L.D)
    g.shape.contours.extend(c.transformed(lambda p: (p[0] + T * 0.5, p[1])) for c in cons)
    g.bar(0, T * 2.6, g.cap * 0.52, wm=0.85, cap0="butt", cap1="butt")


# ---------------------------------------------------------------- more marks: Central European, Baltic, Turkish, Romanian
@glyph("breve", 0x2D8, "accent")
def breve(g):
    y = _ay(g) + g.xh * 0.02
    w = g.xh * 0.2
    st = g.P(0.78).m(-w, y + g.xh * 0.19, "S").c(0, y, "E").c(w, y + g.xh * 0.19, "N")
    g.add(st, "butt", "butt")


@glyph("hungarumlaut", 0x2DD, "accent")
def hungarumlaut(g):
    y = _ay(g)
    for dx in (-g.xh * 0.12, g.xh * 0.12):
        g.add(g.P(0.8).m(dx + g.xh * 0.11, y + g.xh * 0.25).l(dx - g.xh * 0.06, y), "butt", "butt")


@glyph("ogonek", 0x2DB, "accent")
def ogonek(g):
    xh = g.xh
    st = g.P(0.72).m(0, g.h * 0.5, "S").c(-xh * 0.13, -xh * 0.17, "S", k=0.62).c(xh * 0.05, -xh * 0.33, "E").l(xh * 0.15, -xh * 0.33)
    g.add(st, "butt")


@glyph("commaaccentcomb", 0x326, "accent")
def commaaccentcomb(g):
    d = g.T * 0.9
    y = -g.xh * 0.1 - d / 2
    g.dot(0, y, d)
    g.add(g.P(0.62).m(d * 0.32, y, "S").c(-d * 0.3, y - g.xh * 0.2, 240), "butt")


@glyph("commaturnedabove", 0x312, "accent")
def commaturnedabove(g):
    d = g.T * 0.9
    y = _ay(g) + g.xh * 0.06 + d / 2
    g.dot(0, y, d)
    g.add(g.P(0.62).m(-d * 0.32, y, "N").c(d * 0.3, y + g.xh * 0.2, 60), "butt")


@glyph("dotbelowcomb", 0x323, "accent")
def dotbelowcomb(g):
    d = g.dotd
    g.dot(0, -g.xh * 0.12 - d / 2, d)


@glyph("caronvert", None, "accent")
def caronvert(g):
    """The apostrophe-like caron of d', l', t', L' (Czech, Slovak)."""
    d = g.T * 0.9
    g.add(g.P(0.7).m(g.xh * 0.04, 0, "S").l(-g.xh * 0.03, -g.xh * 0.2), "round", "butt")


@glyph("dcroat", 0x111)
def dcroat(g):
    L.d(g)
    T, w = g.T, L._bw(g)
    g.bar(w - T * 2.1, w + T * 0.55, g.xh + (g.asc - g.xh) * 0.48, wm=0.8, cap0="butt", cap1="butt")


@glyph("Dcroat", 0x110, "uc")
def Dcroat(g):
    Eth(g)


@glyph("hbar", 0x127)
def hbar(g):
    T = g.T
    cons = g.sandbox(L.hh)
    g.shape.contours.extend(cons)
    g.bar(-T * 0.45, T * 2.1, g.xh + (g.asc - g.xh) * 0.55, wm=0.8, cap0="butt", cap1="butt")


@glyph("Hbar", 0x126, "uc")
def Hbar(g):
    T = g.T
    L.H(g)
    g.bar(-T * 0.3, g.Hw + T * 0.3, g.cap * 0.76, wm=0.75, cap0="butt", cap1="butt")



# accent table used by the composite builder: combining mark -> accent glyph
MARKS = {
    0x300: "grave", 0x301: "acute", 0x302: "circumflex", 0x303: "tilde", 0x308: "dieresis",
    0x30A: "ring", 0x30C: "caron", 0x327: "cedilla", 0x304: "macron", 0x307: "dotaccent",
    0x306: "breve", 0x30B: "hungarumlaut", 0x328: "ogonek", 0x326: "commaaccentcomb", 0x323: "dotbelowcomb",
}
BELOW = {"cedilla", "ogonek", "commaaccentcomb", "dotbelowcomb"}
