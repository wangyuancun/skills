# Drawing custom glyphs

A custom glyph file redraws any letter. Point the spec at it:
`"glyphs": "my_glyphs.py"`. The build runs the file; each function decorated
with `@glyph` replaces the stock drawing of that name. `glyph`, `L` (stock
Latin drawings) and `X` (punctuation and symbols) are already in scope.

Glyphs are drawn as **strokes**: you describe the centre line, the engine
gives it thickness, contrast, joins and terminals that match the rest of the
family, in every weight. Never draw outlines by hand unless you need a solid shape.

```python
@glyph("Q", 0x51, "uc")           # name, Unicode, case: "lc", "uc", "fig", "punct", "sym"
def Q(g):
    L.O(g)                         # reuse the stock O
    w = g.Ow
    st = g.P().m(w * 0.5, g.cap * 0.14, -35).c(w * 0.8, -g.cap * 0.05, "E").c(w * 1.02, g.cap * 0.02, 25)
    g.add(st)
```

Draw with the left edge of the letter near x = 0. Do not set a width; spacing is automatic.

## Measurements on `g`

| Name | Meaning |
| --- | --- |
| `g.xh`, `g.cap`, `g.asc`, `g.desc` | vertical metrics |
| `g.os` | overshoot |
| `g.T` | stem thickness for this glyph's case |
| `g.h` | thickness of a horizontal stroke |
| `g.nw`, `g.ow` | width of n and o |
| `g.Hw`, `g.Ow` | width of H and O |
| `g.fw` | figure width |
| `g.thin` | multiplier for the thin diagonal in contrast designs |
| `g.join`, `g.branch`, `g.ap` | join thinning, branch height, aperture |

Always build from these, never from fixed numbers, so the glyph follows every weight and width.

## Strokes

`g.P(wm=1.0)` starts a stroke; `wm` scales its thickness.

- `.m(x, y, d)` start, heading in direction `d`
- `.l(x, y)` straight line to a point
- `.c(x, y, d)` curve to a point, arriving in direction `d`

Directions: `"N" "S" "E" "W" "NE" "NW" "SE" "SW"`, an angle in degrees, or a vector.
Put a node at every extreme of a curve (top, bottom, left, right) and never turn
more than 90 degrees between two nodes.

Options on any node: `wm=0.7` (thinner here), `w=60` (exact thickness),
`cut="E"` (cut the end horizontally) or `cut="N"` (vertically).

`g.add(stroke, cap0=None, cap1=None)` draws it. Caps follow the design; pass
`"butt"` to force a flat end where the stroke hides inside another.

## Ready-made parts

| Call | Draws |
| --- | --- |
| `g.stem(x, y0, y1)` | vertical stroke centred on x. `sb="f"`, `st="l"` add slab serifs when the design has them |
| `g.bar(x0, x1, y)` | horizontal stroke centred on y |
| `g.oval(x0, y0, x1, y1)` | closed bowl from its outer box |
| `g.dg(xa, ya, xb, yb, ea=-1, eb=1)` | diagonal with flat cuts; `ea`/`eb` say whether x is the left edge (-1), centre (0) or right edge (1) |
| `g.arch(xl, xr, ytop)` | the shoulder of n, m, h |
| `g.bowl(xs, x1, y0, y1, right=True)` | the bowl of b, d, p, q |
| `g.open_arc(x0, y0, x1, y1, a_top, a_bot)` | a c-shape |
| `g.dot(cx, cy, d)` | dot in the family's dot style |
| `g.poly(points)` | a solid polygon |
| `g.mirror_x(fn, w)`, `g.rotate(fn, w, h)` | reuse another drawing mirrored or rotated |

## Rules for variable fonts

Every weight must produce the same number of strokes and nodes. So:

- No `if` on weight or on measurements inside a glyph function.
- Use `min()` / `max()` freely; they keep the structure.

## Check your drawing

```bash
python scripts/fontworks.py glyph spec.json Q y --out q.png             # filled, every master
python scripts/fontworks.py glyph spec.json Q --outline --out q.png     # outlines
```
