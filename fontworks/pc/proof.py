"""Proof sheets: real text set in the compiled font, shaped by HarfBuzz."""
from __future__ import annotations

import html

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen


class Face:
    def __init__(self, path, variations=None):
        self.blob = hb.Blob.from_file_path(path)
        self.face = hb.Face(self.blob)
        self.font = hb.Font(self.face)
        if variations:
            self.font.set_variations(variations)
        self.upm = self.face.upem
        self._paths = {}
        from fontTools.ttLib import TTFont
        self.glyph_names = set(TTFont(path, lazy=True).getGlyphOrder())

    def path(self, gid):
        if gid not in self._paths:
            pen = SVGPathPen(None)
            self.font.draw_glyph_with_pen(gid, pen)
            self._paths[gid] = pen.getCommands()
        return self._paths[gid]

    def shape(self, text, features=None):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.font, buf, features or {})
        return buf.glyph_infos, buf.glyph_positions


class Sheet:
    """A page of text lines. Collects SVG, tracks the cursor."""

    def __init__(self, width=1600, margin=70, bg=None, fg=None):
        from . import brand
        bg, fg = bg or brand.CREAM, fg or brand.INK
        self.w, self.m, self.bg, self.fg = width, margin, bg, fg
        self.y = margin
        self.out = []

    def gap(self, h):
        self.y += h

    def label(self, text, color=None, size=15):
        from . import brand
        self.y += size
        self.out.append(brand.label(text, self.m, self.y, size, color or brand.MUTE))
        self.y += size * 0.9

    def line(self, face, text, size, features=None, color=None, x=None, advance=True, tracking=0.0):
        """Set one line. Returns its width in px."""
        infos, pos = face.shape(text, features)
        s = size / face.upm
        base = self.y + size * 0.82
        x0 = self.m if x is None else x
        pen = 0.0
        parts = []
        for info, p in zip(infos, pos):
            d = face.path(info.codepoint)
            if d:
                parts.append(f'<path transform="translate({pen + p.x_offset:.1f} {p.y_offset:.1f})" d="{d}"/>')
            pen += p.x_advance + tracking * face.upm
        self.out.append(f'<g fill="{color or self.fg}" transform="translate({x0:.1f} {base:.1f}) scale({s:.5f} {-s:.5f})">'
                        + "".join(parts) + "</g>")
        if advance:
            self.y += size * 1.24
        return pen * s

    def wrap(self, face, text, size, features=None, color=None, leading=1.32):
        words, cur = text.split(), ""
        maxw = self.w - 2 * self.m
        for wd in words:
            trial = (cur + " " + wd).strip()
            infos, pos = face.shape(trial, features)
            if sum(p.x_advance for p in pos) * size / face.upm > maxw and cur:
                self.line(face, cur, size, features, color, advance=False)
                self.y += size * leading
                cur = wd
            else:
                cur = trial
        if cur:
            self.line(face, cur, size, features, color, advance=False)
            self.y += size * leading

    def rule(self, color=None):
        from . import brand
        color = color or brand.LINE
        self.y += 14
        self.out.append(f'<rect x="{self.m}" y="{self.y}" width="{self.w - 2 * self.m}" height="1.5" fill="{color}"/>')
        self.y += 22

    def svg(self):
        h = self.y + self.m
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{h:.0f}" viewBox="0 0 {self.w} {h:.0f}">'
                f'<rect width="100%" height="100%" fill="{self.bg}"/>' + "".join(self.out) + "</svg>")

    def save(self, path, png=True, png_width=None):
        data = self.svg()
        with open(path, "w") as f:
            f.write(data)
        if png:
            try:
                import cairosvg
                cairosvg.svg2png(bytestring=data.encode(), write_to=path[:-4] + ".png", output_width=png_width or self.w)
            except Exception as e:  # cairo missing: the SVG is still written
                print(f"note: PNG proof skipped ({e.__class__.__name__}); open {path} instead")


PANGRAM = "Sphinx of black quartz, judge my vow. Pack my box with five dozen liquor jugs."
TEXT = ("Type is the clothing words wear. A good typeface disappears while you read and leaves only the voice "
        "of the writer. Spacing is half of that work: the white between letters must feel as even as the black "
        "of the strokes, so that a line of text has one steady rhythm from the first word to the last.")
SPACING = ["nnnonnoonoonnn HHHOHHOOHOOHHH", "nanbncndnenfngnhninjnknlnmnn", "nonpnqnrnsntnunvnwnxnynzn",
           "oaobocodoeofogohoiojokolomoo", "oopoqorosotouovowoxoyozo", "HAHBHCHDHEHFHGHHHIHJHKHLHMH",
           "HNHOHPHQHRHSHTHUHVHWHXHYHZH", "0010203040506070809011 1234567890"]
KERNING = ["AVATAR WAVE Tokyo Yes Type LTD", "To Ta Te Ty Tr Va Ve Vo Ya Yo We Wo", "P. F, T. V. Y, r. y. w, f) (j) [a] {o}",
           "“Quoted” ‘single’ L’A it’s T-o A-V", "fjord Kyoto Ray vowel away RTFM"]


def proof(result, path, png_width=1500):
    """One tall sheet: headline, weights, text, spacing strings, kerning, glyph set."""
    fam = result["family"]
    fid = result["family_id"]
    out = result["out"]
    import os
    from . import brand
    from .presets import WEIGHT_NAME
    faces = {}
    for w in result["weights"]:
        style = WEIGHT_NAME.get(w, str(w))
        p = os.path.join(out, "fonts", "ttf", f"{fid}-{style}.ttf")
        if os.path.exists(p):
            faces[w] = Face(p)
    ws = sorted(faces)
    reg = faces[400] if 400 in faces else faces[ws[len(ws) // 2]]
    heavy = faces[ws[-1]]
    sh = Sheet()
    sh.out.append(brand.mark(sh.w - sh.m - 40, sh.m - 6, 40))
    sh.label(f"{fam}  ·  proof sheet  ·  fontworks {brand.VERSION}")
    sh.line(heavy, fam, 150)
    sh.gap(10)
    for w in ws:
        sh.label(f"{WEIGHT_NAME.get(w, w)} {w}")
        sh.line(faces[w], "Hamburgefonstiv 0123456789", 76)
    sh.rule()
    sh.label("text 30px")
    sh.wrap(reg, TEXT, 30)
    sh.gap(10)
    sh.label("text 20px")
    sh.wrap(reg, TEXT, 20)
    sh.rule()
    sh.label("spacing")
    for s in SPACING:
        sh.line(reg, s, 50)
    sh.rule()
    sh.label("kerning on")
    for s in KERNING:
        sh.line(reg, s, 58)
    sh.label("kerning off")
    sh.line(reg, KERNING[0], 58, {"kern": False}, color=brand.MUTE)
    sh.rule()
    has_ss01 = "a.ss01" in reg.glyph_names
    sh.label("features: tnum / zero / case" + (" / ss01" if has_ss01 else ""))
    sh.line(reg, "1111 0000  ->", 50, advance=False)
    sh.line(reg, "1111 0000", 50, {"tnum": True, "zero": True}, x=520)
    if has_ss01:
        sh.line(reg, "banana  ->", 50, advance=False)
        sh.line(reg, "banana", 50, {"ss01": True}, x=520)
    sh.line(reg, "(A-B)  ->", 50, advance=False)
    sh.line(reg, "(A-B)", 50, {"case": True}, x=520)
    sh.rule()
    sh.label("glyph set")
    cps = sorted(reg.face.unicodes)
    chars = "".join(chr(c) for c in cps if c > 0x20 and c != 0xA0)
    for i in range(0, len(chars), 38):
        sh.line(reg, " ".join(chars[i:i + 38]), 32)
    if len(ws) > 1:
        sh.rule()
        sh.label("heaviest weight")
        sh.wrap(heavy, PANGRAM + " " + "".join(chr(c) for c in range(0x41, 0x5B)), 44)
    sh.save(path, png_width=png_width)
    return path
