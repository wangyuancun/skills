"""Handwriting and lettering from photos.

Two routes:

* Sheet route (best): print the FontWorks sheet, write one character per box,
  photograph it. Four markers on the sheet let us square up the photo exactly,
  red guide lines drop out of the scan, and every box has known metrics.
* Quick route: any photo of writing. Characters are found automatically,
  numbered on a contact image, Claude labels them, then they are traced.

Either way the result is a set of traced outlines plus measured metrics and
stroke weight. Anything the writer did not provide (accents, punctuation,
symbols) is drawn by the engine at the measured weight, so the font is
complete.
"""
from __future__ import annotations

import json
import math
import os

import numpy as np

from . import brand
from .geometry import Contour

# ---------------------------------------------------------------- sheet geometry (millimetres)
PAGE_W, PAGE_H = 210.0, 277.0          # fits on both A4 and US Letter
MARK = 12.0
MARK_C = [(17.0, 17.0), (193.0, 17.0), (17.0, 260.0), (193.0, 260.0)]
GRID_X0, GRID_X1, GRID_Y0, GRID_Y1 = 12.0, 198.0, 44.0, 250.0
COLS, ROWS = 7, 8
CELL_W, CELL_H = (GRID_X1 - GRID_X0) / COLS, (GRID_Y1 - GRID_Y0) / ROWS
BASE = 17.5                             # baseline, from the top of a cell
CAP_MM = 10.0                           # printed cap height
MMU = CAP_MM / 700.0                    # millimetres per font unit on the guides
PX_MM = 10.0                            # resolution of the squared-up page
UP = 3                                  # extra upsampling before tracing

PAGE1 = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123")
PAGE2 = list("456789.,:;!?'\"()[]{}-/\\&@#$%*+=<>_~^|€£¥¢«»‘’“”–—¿¡°©®™")
PAGES = [PAGE1, PAGE2]
DESC = set("gjpqy")


def _aruco():
    import cv2
    return cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)


def _marker_svg(page, i):
    import cv2
    bits = cv2.aruco.generateImageMarker(_aruco(), page * 4 + i, 6)
    cx, cy = MARK_C[i]
    s = MARK / 6
    x0, y0 = cx - MARK / 2, cy - MARK / 2
    out = [f'<rect x="{x0 - 2:.2f}" y="{y0 - 2:.2f}" width="{MARK + 4:.2f}" height="{MARK + 4:.2f}" fill="#fff"/>']
    for r in range(6):
        for c in range(6):
            if bits[r, c] < 128:
                out.append(f'<rect x="{x0 + c * s:.3f}" y="{y0 + r * s:.3f}" width="{s + 0.02:.3f}" height="{s + 0.02:.3f}" fill="#000"/>')
    return "".join(out)


def _cell_origin(idx):
    r, c = divmod(idx, COLS)
    return GRID_X0 + c * CELL_W, GRID_Y0 + r * CELL_H


def sheet_svg(page):
    chars = PAGES[page]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{PAGE_W}mm" height="{PAGE_H}mm" viewBox="0 0 {PAGE_W} {PAGE_H}">',
         f'<rect width="{PAGE_W}" height="{PAGE_H}" fill="#fff"/>']
    for i in range(4):
        o.append(_marker_svg(page, i))
    o.append(brand.mark(27, 11.5, 11))
    o.append(brand.wordmark(41.5, 19.6, 7.2, fill=brand.INK)[0])
    o.append(brand.text(f"Handwriting sheet {page + 1} of {len(PAGES)}" + ("  (optional)" if page else ""), 41.5, 26.4, 3.4, "Regular", brand.MUTE)[0])
    tips = ["Dark pen, not pencil. Write each character once inside its box, sitting on the red baseline.",
            "Keep inside the box. Lay the sheet flat, light it evenly and photograph it straight on, all four squares visible."]
    for j, t in enumerate(tips):
        o.append(brand.text(t, 27, 34.5 + j * 4.3, 2.75, "Regular", brand.INK)[0])
    for idx in range(COLS * ROWS):
        x, y = _cell_origin(idx)
        o.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{CELL_W:.2f}" height="{CELL_H:.2f}" fill="none" stroke="#f6c4bf" stroke-width="0.25"/>')
        if idx >= len(chars):
            continue
        b = y + BASE
        for yy, dash, wdt in ((b, None, 0.35), (b - 500 * MMU, "1.2 1", 0.25), (b - CAP_MM, "0.6 1.2", 0.2), (b + 200 * MMU, "0.6 1.2", 0.2)):
            da = f' stroke-dasharray="{dash}"' if dash else ""
            o.append(f'<line x1="{x + 1.5:.2f}" y1="{yy:.2f}" x2="{x + CELL_W - 1.5:.2f}" y2="{yy:.2f}" stroke="{brand.GUIDE}" stroke-width="{wdt}"{da}/>')
        o.append(brand.text(chars[idx], x + 1.8, y + 4.6, 3.6, "Regular", "#ee9a92")[0])
    o.append(brand.text(f"fontworks  ·  {brand.SITE}", PAGE_W / 2, PAGE_H - 3.5, 2.6, "Regular", brand.MUTE, anchor="middle")[0])
    o.append("</svg>")
    return "".join(o)


def write_sheets(out_dir):
    """Write the printable sheets as PDF (both pages) plus PNG previews."""
    import cairosvg
    os.makedirs(out_dir, exist_ok=True)
    pdfs, pngs = [], []
    for p in range(len(PAGES)):
        svg = sheet_svg(p).encode()
        pdf = os.path.join(out_dir, f"fontworks-sheet-{p + 1}.pdf")
        png = os.path.join(out_dir, f"fontworks-sheet-{p + 1}.png")
        cairosvg.svg2pdf(bytestring=svg, write_to=pdf)
        cairosvg.svg2png(bytestring=svg, write_to=png, output_width=int(PAGE_W * 8))
        pdfs.append(pdf)
        pngs.append(png)
    merged = os.path.join(out_dir, "fontworks-handwriting-sheets.pdf")
    try:
        from pypdf import PdfWriter
        w = PdfWriter()
        for p in pdfs:
            w.append(p)
        with open(merged, "wb") as f:
            w.write(f)
        for p in pdfs:
            os.remove(p)
        return [merged] + pngs
    except ImportError:
        return pdfs + pngs


# ---------------------------------------------------------------- image helpers
def _load(path):
    from PIL import Image, ImageOps
    import cv2
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


def _flatten(channel, k):
    """Divide out uneven lighting: each pixel relative to its local paper colour."""
    import cv2
    k = max(3, int(k) | 1)
    bg = cv2.morphologyEx(channel, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    bg = cv2.GaussianBlur(bg, (0, 0), k / 3)
    return np.clip(channel.astype(np.float32) / np.maximum(bg.astype(np.float32), 1.0), 0, 1)


def _clean(mask, min_area):
    import cv2
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    keep = np.zeros(n, bool)
    keep[1:] = st[1:, cv2.CC_STAT_AREA] >= min_area
    return keep[lab]


# ---------------------------------------------------------------- sheet route
def find_page(img):
    """Locate the markers. Returns (page index, homography photo->page px) or raises."""
    import cv2
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    scale = min(1.0, 2400 / max(gray.shape))
    small = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1 else gray
    det = cv2.aruco.ArucoDetector(_aruco(), cv2.aruco.DetectorParameters())
    corners, ids, _ = det.detectMarkers(small)
    if ids is None or len(ids) < 2:
        raise ValueError("Could not find the sheet's corner squares. Retake the photo with all four squares visible, "
                         "flat and in focus.")
    ids = ids.flatten()
    pages = [i // 4 for i in ids]
    page = max(set(pages), key=pages.count)
    src, dst = [], []
    for cs, i in zip(corners, ids):
        if i // 4 != page or i % 4 > 3:
            continue
        cx, cy = MARK_C[i % 4]
        h = MARK / 2
        for (px, py), (mx, my) in zip(cs.reshape(4, 2), [(cx - h, cy - h), (cx + h, cy - h), (cx + h, cy + h), (cx - h, cy + h)]):
            src.append((px / scale, py / scale))
            dst.append((mx * PX_MM, my * PX_MM))
    if len(src) < 8:
        raise ValueError("Only one corner square was readable. Retake the photo with the whole sheet in frame.")
    H, _ = cv2.findHomography(np.array(src, np.float32), np.array(dst, np.float32), cv2.RANSAC, 3.0)
    return page, H, int(len(src) / 4)


def read_sheet(path, log=print):
    """One photo of one sheet -> list of samples."""
    import cv2
    img = _load(path)
    page, H, nmark = find_page(img)
    W, Hh = int(PAGE_W * PX_MM), int(PAGE_H * PX_MM)
    flat = cv2.warpPerspective(img, H, (W, Hh), flags=cv2.INTER_CUBIC, borderValue=(255, 255, 255))
    red = _flatten(flat[:, :, 2], 9 * PX_MM)            # red guides vanish in the red channel
    chars = PAGES[page]
    samples, notes = [], []
    pad = 0.9 * PX_MM
    for idx, ch in enumerate(chars):
        x, y = _cell_origin(idx)
        x0, y0 = int(x * PX_MM + pad), int(y * PX_MM + pad)   # the printed label is red and drops out
        x1, y1 = int((x + CELL_W) * PX_MM - pad), int((y + CELL_H) * PX_MM - pad)
        cell = red[y0:y1, x0:x1]
        big = cv2.resize(cell, None, fx=UP, fy=UP, interpolation=cv2.INTER_CUBIC)
        big = cv2.GaussianBlur(big, (0, 0), UP * 0.6)
        mask = big < 0.58
        mask = _clean(mask, (0.35 * PX_MM * UP) ** 2)
        if mask.sum() < (0.6 * PX_MM * UP) ** 2:
            continue
        edge = mask[0].any() or mask[-1].any() or mask[:, 0].any() or mask[:, -1].any()
        if edge:
            notes.append(ch)
        scale = 1.0 / (PX_MM * UP * MMU)                  # font units per traced pixel
        oy = (y + BASE) * PX_MM * UP - y0 * UP              # baseline in traced pixels
        samples.append(dict(char=ch, mask=mask, scale=scale, ox=0.0, oy=oy))
    log(f"sheet {page + 1}: {nmark} corner squares found, {len(samples)} of {len(chars)} characters written")
    if notes:
        log(f"  touching the box edge (may be clipped): {' '.join(notes)}")
    return page, samples, flat


# ---------------------------------------------------------------- quick route
def segment(path, out_dir):
    """Find characters in any photo. Writes a numbered contact image and segments.json."""
    import cv2
    img = _load(path)
    scale = min(1.0, 2600 / max(img.shape[:2]))
    if scale < 1:
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    gray = img.min(axis=2)
    flat = _flatten(gray, max(img.shape[:2]) / 25)
    ink = flat < 0.6
    ink = _clean(ink, max(6, img.shape[0] * img.shape[1] * 1.5e-6))
    n, lab, st, cen = cv2.connectedComponentsWithStats(ink.astype(np.uint8), 8)
    H0, W0 = ink.shape
    boxes = []
    for i in range(1, n):
        x, y, w, h = (int(v) for v in st[i, :4])
        if x <= 1 or y <= 1 or x + w >= W0 - 1 or y + h >= H0 - 1:
            continue                      # paper edges, table, shadows at the border
        if w * h > 0.2 * W0 * H0:
            continue
        boxes.append(dict(ids=[i], x0=x, y0=y, x1=x + w, y1=y + h))
    if not boxes:
        raise ValueError("No writing found in the photo.")
    hmed = float(np.median([b["y1"] - b["y0"] for b in boxes]))
    boxes = [b for b in boxes if (b["y1"] - b["y0"]) < hmed * 4 and (b["x1"] - b["x0"]) < hmed * 8]
    hmed = float(np.median([b["y1"] - b["y0"] for b in boxes]))
    boxes = [b for b in boxes if (b["y1"] - b["y0"]) > hmed * 0.12 or (b["x1"] - b["x0"]) > hmed * 0.12]
    # specks far from any writing (dust, paper corners) are dropped
    def near(b):
        cx, cy = (b["x0"] + b["x1"]) / 2, (b["y0"] + b["y1"]) / 2
        return any(o is not b and abs((o["x0"] + o["x1"]) / 2 - cx) < hmed * 3 and abs((o["y0"] + o["y1"]) / 2 - cy) < hmed * 1.5
                   for o in boxes)
    boxes = [b for b in boxes if (b["y1"] - b["y0"]) > hmed * 0.5 or near(b)]
    # merge parts stacked above each other (i, j, !, ?, ;, accents)
    merged = True
    while merged:
        merged = False
        for a in boxes:
            for b in boxes:
                if a is b:
                    continue
                ov = min(a["x1"], b["x1"]) - max(a["x0"], b["x0"])
                small = min(a["x1"] - a["x0"], b["x1"] - b["x0"])
                gap = max(a["y0"], b["y0"]) - min(a["y1"], b["y1"])
                if ov > 0.45 * small and gap < hmed * 0.75:
                    a["ids"] += b["ids"]
                    a["x0"], a["y0"] = min(a["x0"], b["x0"]), min(a["y0"], b["y0"])
                    a["x1"], a["y1"] = max(a["x1"], b["x1"]), max(a["y1"], b["y1"])
                    boxes.remove(b)
                    merged = True
                    break
            if merged:
                break
    # reading order: lines by vertical centre, then left to right
    boxes.sort(key=lambda b: (b["y0"] + b["y1"]) / 2)
    lines, cur = [], []
    for b in boxes:
        cy = (b["y0"] + b["y1"]) / 2
        if cur and abs(cy - np.mean([(c["y0"] + c["y1"]) / 2 for c in cur])) > hmed * 0.9:
            lines.append(cur)
            cur = []
        cur.append(b)
    if cur:
        lines.append(cur)
    out, k = [], 1
    for li, line in enumerate(lines):
        for b in sorted(line, key=lambda b: b["x0"]):
            b.update(n=k, line=li)
            out.append(b)
            k += 1
    os.makedirs(out_dir, exist_ok=True)
    np.save(os.path.join(out_dir, "labels.npy"), lab.astype(np.int32))
    cv2.imwrite(os.path.join(out_dir, "photo.png"), img)
    kept = np.isin(lab, [i for b in out for i in b["ids"]])
    vis = np.where(kept[..., None], np.array([18, 22, 23], np.uint8), np.array([228, 239, 244], np.uint8)).astype(np.uint8)
    fs = max(0.5, hmed / 45)
    for b in out:
        cv2.rectangle(vis, (b["x0"] - 2, b["y0"] - 2), (b["x1"] + 2, b["y1"] + 2), (47, 107, 95), 2)
        cv2.putText(vis, str(b["n"]), (b["x0"], max(14, b["y0"] - 6)), cv2.FONT_HERSHEY_SIMPLEX, fs, (47, 107, 95), max(1, int(fs * 2)))
    contact = os.path.join(out_dir, "segments.png")
    cv2.imwrite(contact, vis)
    with open(os.path.join(out_dir, "segments.json"), "w") as f:
        json.dump(dict(photo=os.path.abspath(path), count=len(out), boxes=out), f)
    return contact, len(out), len(lines)


# typical heights of symbols in a 1000-unit em, for lines with no letters to measure
SYM_H = {"(": 900, ")": 900, "[": 900, "]": 900, "{": 900, "}": 900, "|": 960, "\\": 760, "/": 760,
         "$": 820, "\u20ac": 710, "\u00a3": 710, "@": 740, "#": 700, "&": 720, "?": 710, "!": 710, ":": 480}
ON_BASE = ".!?:@#&%/$\u20ac\u00a3<>|\\"


def _base_at(base0, slope, curve, x):
    return float(np.polyval(curve, x)) if curve is not None else base0 + slope * x


def _local_base(b, items, fallback, k=4):
    """Baseline under one letter, from the bottoms of its nearest neighbours that
    sit on the line. Follows a curled page or a line that wanders, where one fit
    for the whole line would leave letters floating or sinking."""
    cx = (b["x0"] + b["x1"]) / 2
    flat = [((o["x0"] + o["x1"]) / 2, o["y1"]) for ch, o in items
            if ch.isalnum() and ch not in DESC and ch not in "Qf"]
    if len(flat) < 3:
        return fallback
    near = sorted(flat, key=lambda p: abs(p[0] - cx))[:k]
    if len(near) >= 3:   # a straight line through the neighbours, read off at this letter
        xs = np.array([p[0] for p in near]); ys = np.array([p[1] for p in near])
        if np.ptp(xs) > 0:
            a, c = np.polyfit(xs, ys, 1)
            return float(a * cx + c)
    return float(np.median([p[1] for p in near]))


def read_labeled(seg_dir, labels, log=print):
    """labels: {"1": "H", "2": "e", ...} or a string with one character per box in reading order."""
    import cv2
    with open(os.path.join(seg_dir, "segments.json")) as f:
        seg = json.load(f)
    lab = np.load(os.path.join(seg_dir, "labels.npy"))
    boxes = {b["n"]: b for b in seg["boxes"]}
    soft = None
    ph = os.path.join(seg_dir, "photo.png")
    if os.path.exists(ph):
        img = cv2.imread(ph)
        if img is not None and img.shape[:2] == lab.shape:
            flat = _flatten(img.min(axis=2), max(img.shape[:2]) / 25)
            soft = np.clip((0.82 - flat) / 0.44, 0.0, 1.0).astype(np.float32)
    if isinstance(labels, str):
        chars = [c for c in labels if not c.isspace()]
        labels = {str(i + 1): c for i, c in enumerate(chars)}
    by_line = {}
    for k, ch in labels.items():
        if not ch or ch in ("skip", "?skip"):
            continue
        b = boxes[int(k)]
        by_line.setdefault(b["line"], []).append((ch, b))
    # pass 1: baseline, slope and scale for every line. A line with no letters
    # to measure (punctuation, symbols) borrows the scale of the lettered lines,
    # so a colon is as big as the writer made it, not stretched to cap height.
    geo = {}
    for li, items in by_line.items():
        flat = [((b["x0"] + b["x1"]) / 2, b["y1"]) for ch, b in items if ch.isalnum() and ch not in DESC and ch not in "Q"]
        if not flat:   # symbols only: trust the marks that sit on the baseline
            flat = [((b["x0"] + b["x1"]) / 2, b["y1"]) for ch, b in items if ch in ON_BASE]
        if not flat:
            flat = [((b["x0"] + b["x1"]) / 2, b["y1"]) for ch, b in items]
        xs = np.array([p[0] for p in flat])
        ys = np.array([p[1] for p in flat])
        slope = 0.0
        if len(flat) >= 4 and np.ptp(xs) > 0:      # writing that runs uphill or downhill
            slope = float(np.polyfit(xs, ys, 1)[0])
            slope = max(min(slope, 0.25), -0.25)
        base0 = float(np.median(ys - slope * xs))
        curve = None
        if len(flat) >= 7 and np.ptp(xs) > 0:      # a curled page or a phone held at an angle bends the line
            c2 = np.polyfit(xs, ys, 2)
            r1 = np.abs(ys - (base0 + slope * xs))
            r2 = np.abs(ys - np.polyval(c2, xs))
            if np.median(r2) < np.median(r1) * 0.7:
                curve = c2
        xh_tops = [_base_at(base0, slope, curve, (b["x0"] + b["x1"]) / 2) - b["y0"] for ch, b in items if ch in "acemnorsuvwxz"]
        caps = [b["y1"] - b["y0"] for ch, b in items if ch in "ABDEFHIKLMNPRTUVWXYZ0123456789"]
        units = None
        syms = [SYM_H[ch] / max(b["y1"] - b["y0"], 1) for ch, b in items if ch in SYM_H]
        if xh_tops:
            units = 500.0 / max(float(np.median(xh_tops)), 1.0)
        elif caps:
            units = 700.0 / max(float(np.median(caps)), 1.0)
        elif syms:   # symbols only: size them as type, not as large as they were scribbled
            units = float(np.median(syms))
        if not any(ch.isalnum() or ch in ON_BASE for ch, _ in items):
            base0 = None      # nothing on this line sits on a baseline
        geo[li] = [base0, slope, units, curve]
    known = [g[2] for g in geo.values() if g[2]]
    for li, g in geo.items():
        if g[2] is None:
            g[2] = float(np.median(known)) if known else 700.0 / max(float(np.median([b["y1"] - b["y0"] for _, b in by_line[li]])), 1.0)
        if g[0] is None:
            g[0] = float(max(b["y1"] for _, b in by_line[li]))
    samples, seen = [], set()
    for li, items in by_line.items():
        base0, slope, units, curve = geo[li]
        for ch, b in items:
            if ch in seen:
                continue
            seen.add(ch)
            base = _base_at(base0, slope, curve, (b["x0"] + b["x1"]) / 2)
            base = _local_base(b, items, base)
            m = 4
            y0, y1, x0, x1 = max(b["y0"] - m, 0), b["y1"] + m, max(b["x0"] - m, 0), b["x1"] + m
            hard = np.isin(lab[y0:y1, x0:x1], b["ids"]).astype(np.uint8)
            # trace the ink's own soft edge, not the thresholded pixels, so a
            # thin pen line comes out smooth instead of stair-stepped
            near = cv2.dilate(hard, np.ones((5, 5), np.uint8)).astype(np.float32)
            crop = soft[y0:y1, x0:x1] * near if soft is not None else hard.astype(np.float32)
            if soft is not None and hard.any():
                # a lighter stroke (pressure eased off) still counts as a full stroke
                crop = np.clip(crop / max(float(np.percentile(crop[hard > 0], 60)), 0.35), 0.0, 1.0)
                crop = np.maximum(crop, hard * 0.75)
            big = cv2.resize(crop, None, fx=UP * 2, fy=UP * 2, interpolation=cv2.INTER_CUBIC)
            big = cv2.GaussianBlur(big, (0, 0), UP * 1.6)
            mask = big > 0.5
            f = UP * 2
            samples.append(dict(char=ch, mask=mask, faint=big > 0.22, scale=units / f, ox=0.0, oy=(base - y0) * f))
    log(f"quick photo: {len(samples)} labelled characters on {len(by_line)} line(s)")
    return samples


# ---------------------------------------------------------------- tracing
def _bbox_units(s):
    ys, xs = np.nonzero(s["mask"])
    return ((xs.min() - s["ox"]) * s["scale"], (s["oy"] - ys.max()) * s["scale"],
            (xs.max() - s["ox"]) * s["scale"], (s["oy"] - ys.min()) * s["scale"])


def _median(vals, default):
    vals = [v for v in vals if v is not None]
    return float(np.median(vals)) if vals else default


def normalise(samples):
    """Scale and shift all samples together so the median cap height is 700 and the baseline sits at 0."""
    bb = {s["char"]: _bbox_units(s) for s in samples}

    def med(chars, i):
        return _median([bb[c][i] for c in chars if c in bb], None)

    base = med("EFHIKLMNTZxzvwnmhklriu1457", 1)
    base = 0.0 if base is None else base
    cap = med("EFHIKLMNTUVWXZ", 3) or med("ABDPRBO", 3)
    if cap is None:
        xh = med("xzvwnmrsuoace", 3)
        cap = (xh - base) * 1.4 + base if xh is not None else 700.0
    k = 700.0 / max(cap - base, 1.0)
    for s in samples:
        s["oy"] -= base / s["scale"]
        s["scale"] *= k
    bb = {s["char"]: _bbox_units(s) for s in samples}

    def med2(chars, i, d):
        v = _median([bb[c][i] for c in chars if c in bb], None)
        return d if v is None else v

    xh = med2("xzvwnmrsuoace", 3, 500.0)
    asc = med2("bdhkl", 3, max(760.0, xh * 1.5))
    return dict(cap=700, xh=int(round(min(max(xh, 330), 640))),
                asc=int(round(min(max(asc, 640), 980))),
                desc=int(round(min(max(med2("gjpqy", 1, -200.0), -380), -110))))


def tidy(samples, metrics, amount):
    """Pull each letter part of the way toward the common heights and baseline.
    0 keeps the writing exactly as written, 1 lines everything up."""
    if amount <= 0:
        return
    targets = {}
    for ch in "ABDEFHIKLMNPRTUVWXYZ0123456789CGOQS!?&":
        targets[ch] = metrics["cap"]
    for ch in "acemnorsuvwxz":
        targets[ch] = metrics["xh"]
    for ch in "bdhkl":
        targets[ch] = metrics["asc"]
    flat = set("ABDEFHIKLMNPRTUVWXZ0123456789abdhiklmnrtuvwxz!?&")
    for s in samples:
        t = targets.get(s["char"])
        if t is None:
            continue
        x0, bot, x1, top = _bbox_units(s)
        if top <= 1:
            continue
        if s["char"] in flat:
            s["oy"] -= (bot * amount) / s["scale"]      # settle onto the baseline
            top -= bot * amount
        f = (t / top) ** amount
        s["scale"] *= f
    # very wide letters read as sprawl in running text: ease them toward a
    # typical width without changing their height or shape
    for s in samples:
        ch = s["char"]
        lim = WIDE.get(ch, 1.3 if ch.isalpha() or ch.isdigit() else None)
        if not lim:
            continue
        x0, bot, x1, top = _bbox_units(s)
        h = max(top - max(bot, metrics["desc"]), 1.0)
        if ch in "gjpqy":
            h = max(top - bot, 1.0)
        ratio = (x1 - x0) / h
        if ratio > lim:
            k = (lim / ratio) ** amount
            _squeeze(s, k)


DOTTED = set('ij!?;:%"=÷')   # marks that must stay apart
WIDE = {**{c: 1.9 for c in "mwMW"}, **{c: 1.35 for c in "OQCGD0@"}, "r": 1.1, "f": 1.0, "t": 1.0, "1": 0.6}


def _squeeze(s, k):
    """Narrow a sample horizontally by k, keeping its left edge."""
    import cv2
    m = s["mask"]
    w = max(1, int(round(m.shape[1] * k)))
    s["mask"] = cv2.resize(m.astype(np.uint8), (w, m.shape[0]), interpolation=cv2.INTER_AREA) > 0
    if s.get("faint") is not None:
        s["faint"] = cv2.resize(s["faint"].astype(np.uint8), (w, m.shape[0]), interpolation=cv2.INTER_AREA) > 0
    s["ox"] = s["ox"] * k


def stroke_width(samples):
    """Median stroke width in font units, from area / perimeter of the ink."""
    import cv2
    ws = []
    for s in samples:
        if not s["char"].isalpha():
            continue
        m = s["mask"].astype(np.uint8)
        cs, _ = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        per = sum(cv2.arcLength(c, True) for c in cs)
        if per > 0:
            ws.append(2.0 * m.sum() / per * s["scale"])
    return _median(ws, 80.0)


def _morph(mask, r_px):
    import cv2
    if abs(r_px) < 0.5:
        return mask
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(2 * abs(r_px)) | 1, int(2 * abs(r_px)) | 1))
    op = cv2.dilate if r_px > 0 else cv2.erode
    return op(mask.astype(np.uint8), k).astype(bool)


def trace_mask(mask, scale, ox, oy):
    """Bitmap -> outline contours in font units, correctly oriented."""
    import potrace
    from .spacing import profile  # noqa: F401  (keeps numpy import warm)
    pad = 4
    m = np.pad(mask, pad)
    path = potrace.Bitmap(~m).trace(turdsize=int(max(8, m.shape[0] * 0.02) ** 2 / 8), alphamax=1.05,
                                    opticurve=True, opttolerance=0.5)

    def T(p):
        return ((p.x - pad - ox) * scale, (oy - (p.y - pad)) * scale)

    cons = []
    for curve in path:
        c = Contour(T(curve.start_point))
        for seg in curve.segments:
            if seg.is_corner:
                c.line(T(seg.c))
                c.line(T(seg.end_point))
            else:
                c.curve(T(seg.c1), T(seg.c2), T(seg.end_point))
        c.close()
        if len(c.segs) >= 2:
            cons.append(c)
    # orientation from nesting depth: outer anticlockwise, holes clockwise
    polys = [np.array(c.flat(6)) for c in cons]
    out = []
    for i, c in enumerate(cons):
        p = polys[i][0]
        depth = sum(1 for j, q in enumerate(polys) if j != i and _inside(p, q))
        want_ccw = depth % 2 == 0
        if (c.area() > 0) != want_ccw:
            c = c.reversed()
        out.append(c)
    return out


def _inside(p, poly):
    x, y = p
    xs, ys = poly[:, 0], poly[:, 1]
    xs2, ys2 = np.roll(xs, -1), np.roll(ys, -1)
    cond = ((ys > y) != (ys2 > y)) & (x < (xs2 - xs) * (y - ys) / np.where(ys2 - ys == 0, 1e-9, ys2 - ys) + xs)
    return bool(np.count_nonzero(cond) % 2)


def contours_to_json(cons):
    out = []
    for c in cons:
        seq = [["m", round(c.start[0], 1), round(c.start[1], 1)]]
        for s in c.segs:
            if s[0] == "l":
                seq.append(["l", round(s[1][0], 1), round(s[1][1], 1)])
            else:
                seq.append(["c"] + [round(v, 1) for p in s[1:] for v in p])
        out.append(seq)
    return out


def contours_from_json(data):
    cons = []
    for seq in data:
        c = Contour((seq[0][1], seq[0][2]))
        for s in seq[1:]:
            if s[0] == "l":
                c.line((s[1], s[2]))
            else:
                c.curve((s[1], s[2]), (s[3], s[4]), (s[5], s[6]))
        cons.append(c)
    return cons


def trace_samples(samples, weights, ink=0.0, neat=0.5, log=print, even=False):
    """Trace every sample at every requested weight. Returns the traced-font dict."""
    from .glyphs_latin import GLYPHS
    from . import glyphs_extra  # noqa: F401
    from .presets import WEIGHT_STEM
    by_uni = {v[1]: k for k, v in GLYPHS.items() if v[1]}
    metrics = normalise(samples)
    tidy(samples, metrics, neat)
    stem0 = stroke_width(samples)
    weights = sorted(int(w) for w in weights) or [400]
    out = dict(source="handwriting", metrics=metrics, weights={})
    for w in weights:
        target = stem0 * WEIGHT_STEM.get(w, 1.0) / WEIGHT_STEM[400] + ink
        glyphs, stems = {}, []
        for s in samples:
            name = by_uni.get(ord(s["char"]))
            if not name:
                continue
            if even:
                src = s["mask"]
                if s.get("faint") is not None:   # light pen pressure still counts as a stroke when redrawing
                    src = s["mask"] | s["faint"]
                m = _even_pen(src, target / 2 / s["scale"], bridge=s["char"] not in DOTTED)
            else:
                m = _morph(s["mask"], (target - stem0) / 2 / s["scale"])
            cons = trace_mask(m, s["scale"], s["ox"], s["oy"])
            if cons:
                glyphs[name] = dict(contours=contours_to_json(cons))
        out["weights"][str(w)] = dict(stem=round(max(target, 12.0), 1), glyphs=glyphs)
        log(f"  wght {w}: {len(glyphs)} glyphs traced, stroke {max(target, 12):.0f} units")
    return out


def _even_pen(mask, r_px, bridge=True):
    """Redraw the writing with one steady pen: find the centre line of every
    stroke, drop the little hairs a skeleton grows at blobs and corners, and
    stroke it again at an even width. Keeps the hand's path and shapes, loses
    the blur, the pressure blots and the ragged ink edge of a phone photo."""
    import cv2
    from skimage.morphology import skeletonize
    m = mask.astype(np.uint8)
    if m.sum() == 0:
        return mask
    # close pinholes and specks first so the centre line is one clean path
    k = max(3, int(r_px * 0.5) | 1)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m)
    big = st[1:, cv2.CC_STAT_AREA].max() if n > 1 else 0
    for i in range(1, n):
        floor = max(big * 0.015, (r_px * 1.2) ** 2) if not bridge else max(big * 0.02, (r_px * 1.5) ** 2)
        if st[i, cv2.CC_STAT_AREA] >= floor:
            keep[lab == i] = 1
    if bridge:
        keep = _bridge(keep, max(r_px * 4.0, 0.14 * max(keep.shape)))
    sk = skeletonize(keep > 0).astype(np.uint8)
    sk = _prune(sk, int(max(4, r_px * 2.4)))
    if sk.sum() == 0:
        return mask
    # stroke the centre line: distance to the line below the pen radius
    dist = cv2.distanceTransform((1 - sk).astype(np.uint8), cv2.DIST_L2, 5)
    out = (dist <= r_px).astype(np.float32)
    out = cv2.GaussianBlur(out, (0, 0), max(1.0, r_px * 0.35))
    return out > 0.5


def _bridge(m, gap):
    """Join pen strokes that nearly touch (a lifted pen inside one letter)
    with a short stroke between their closest points."""
    import cv2
    n, lab = cv2.connectedComponents(m, connectivity=8)
    if n <= 2:
        return m
    pts = [np.argwhere(lab == i) for i in range(1, n)]
    out = m.copy()
    w = max(1, int(gap / 2.2))
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            a, b = pts[i][:: max(1, len(pts[i]) // 400)], pts[j][:: max(1, len(pts[j]) // 400)]
            d = ((a[:, None, :] - b[None, :, :]) ** 2).sum(-1)
            k = np.unravel_index(int(d.argmin()), d.shape)
            if 0 < d[k] ** 0.5 <= gap:
                (y0, x0), (y1, x1) = a[k[0]], b[k[1]]
                cv2.line(out, (int(x0), int(y0)), (int(x1), int(y1)), 1, w)
    return out


def _prune(sk, length):
    """Remove skeleton branches shorter than length that end in a free tip."""
    import cv2
    sk = sk.copy()
    kern = np.ones((3, 3), np.uint8)
    for _ in range(3):
        nb = cv2.filter2D(sk, -1, kern, borderType=cv2.BORDER_CONSTANT) - sk
        ends = np.argwhere((sk == 1) & (nb == 1))
        junction = (sk == 1) & (nb >= 3)
        changed = False
        for y, x in ends:
            path = [(y, x)]; py, px = y, x; prev = None
            while len(path) <= length:
                ys, xs = np.nonzero(sk[max(py - 1, 0):py + 2, max(px - 1, 0):px + 2])
                nxt = [(py - 1 + a + (py == 0), px - 1 + b + (px == 0)) for a, b in zip(ys, xs)]
                nxt = [q for q in nxt if q != (py, px) and q != prev and q not in path]
                if len(nxt) != 1 or junction[nxt[0]]:
                    break
                prev = (py, px); py, px = nxt[0]; path.append((py, px))
            hit_junction = any(junction[max(py - 1, 0):py + 2, max(px - 1, 0):px + 2].ravel())
            if len(path) <= length and hit_junction:
                for q in path:
                    sk[q] = 0
                changed = True
        if not changed:
            break
    return sk


def make_font_project(samples, family, out_dir, weights=(400,), ink=0.0, neat=0.5, designer="", log=print, route="handwriting", even=False):
    """Trace samples and write traced.json plus a ready spec. Returns the spec path.
    ink: add (or remove, if negative) stroke weight in font units.
    neat: 0 keeps every bounce of the writing, 1 lines letters up like type."""
    traced = trace_samples(samples, weights, ink, neat, log, even)
    os.makedirs(out_dir, exist_ok=True)
    tpath = os.path.join(out_dir, "traced.json")
    with open(tpath, "w") as f:
        json.dump(traced, f)
    m = traced["metrics"]
    reg = traced["weights"].get("400") or next(iter(traced["weights"].values()))
    spec = dict(family=family, version="1.000", designer=designer, description=f"{family}, made from handwriting with FontWorks.",
                license="", mode="handwriting", route=route, traced="traced.json", weights=[int(w) for w in traced["weights"]],
                design=dict(cap=m["cap"], xh=m["xh"], asc=m["asc"], desc=m["desc"], stem=reg["stem"], terminal="round",
                            dot="round", contrast=0.0, hratio=1.0, cut="perp", cap_stem=1.0, spacing=1.0))
    spath = os.path.join(out_dir, family.replace(" ", "") + ".json")
    with open(spath, "w") as f:
        json.dump(spec, f, indent=2)
    have = set().union(*[set(v["glyphs"]) for v in traced["weights"].values()])
    log(f"metrics: x-height {m['xh']}, ascender {m['asc']}, descender {m['desc']}; {len(have)} characters from the photo")
    return spath


def load_traced(spec):
    path = spec.get("traced")
    if not path:
        return None
    full = path if os.path.isabs(path) else os.path.join(spec["_dir"], path)
    with open(full) as f:
        return json.load(f)
