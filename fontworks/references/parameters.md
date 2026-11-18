# Design parameters

Put these under `"design"` in the spec. Units are font units (1000 per em).
Anything you leave out comes from the preset, then from the defaults below.

## Vertical proportions

| Parameter | Default | Effect |
| --- | --- | --- |
| `cap` | 700 | Capital height. |
| `xh` | 500 | x-height. Larger reads bigger and more modern (520 to 560); smaller is more elegant (460 to 480). |
| `asc` | 740 | Ascender height (b d h k l). Above `cap` looks classic, equal looks compact. |
| `desc` | -200 | Descender depth (g j p q y). |
| `overshoot` | 10 | How far round letters pass the baseline and x-height. |

## Weight and contrast

| Parameter | Default | Effect |
| --- | --- | --- |
| `stem` | 84 | Vertical stroke of the Regular (400) lowercase. Other weights are derived from it. |
| `cap_stem` | 1.08 | Capitals are this much heavier than lowercase. |
| `hratio` | 0.9 | Horizontal stroke thickness relative to vertical, before contrast. |
| `contrast` | 0.0 | Thick-thin contrast. 0 monoline, 0.15 humanist, 0.5 fashion display. |
| `join` | 0.75 | Stroke thinning where curves meet stems (n, b, a). Lower is more sculpted. |

## Width and shape

| Parameter | Default | Effect |
| --- | --- | --- |
| `width` | 1.0 | Global width. 0.72 condensed, 1.15 extended. |
| `o_ratio` | 1.0 | Width of o relative to x-height. 1.0 is a circle. |
| `n_ratio` | 0.9 | Width of n relative to x-height. |
| `O_ratio` | 1.04 | Width of O relative to cap height. |
| `H_ratio` | 0.76 | Width of H relative to cap height. |
| `roundness` | 0.5523 | Curve tension. 0.5523 true ellipse, 0.62 soft square, 0.74 squarish (DIN-like). |
| `branch` | 0.6 | Height where arches leave the stem. 0.5 geometric, 0.7 grotesque. |
| `aperture` | 0.5 | Opening of c e s a. 0.1 closed and compact, 0.9 open and legible at small sizes. |
| `cut` | "perp" | Terminal cut: `"h"` horizontal (neo-grotesque), `"v"` vertical, `"perp"` at right angles to the stroke. |
| `terminal` | "flat" | `"round"` gives rounded stroke ends everywhere. |
| `dot` | "round" | `"square"` for square i-dots and punctuation. |
| `serif` | "none" | `"slab"` adds slab serifs. |
| `serif_len` | 0.95 | Slab length. |
| `serif_weight` | 1.0 | Slab thickness relative to horizontal strokes. |
| `slant` | 0 | Degrees of lean (oblique). |
| `a` | "double" | Default form of a: `"double"` or `"single"` storey. The other form becomes `ss01`. |
| `stress` | "expansion" | Stroke model (Noordzij). `"expansion"`: thickness follows steepness, vertical stress (grotesques, Didones). `"translation"`: a broad nib, diagonal stress (humanist and old-style). |
| `stress_angle` | 0 | Tilt of the stress axis in degrees; for `"translation"` the nib angle (25 to 35 is calligraphic). |
| `inktrap` | 0 | Ink traps cut into sharp crotches (v w y k M), in stems. 0.15 subtle, 0.25 visible display detail. |
| `soften` | 0.07 | Corner radius in stems. 0 knife-sharp, 0.3 soft rounded. |

## Rhythm

| Parameter | Default | Effect |
| --- | --- | --- |
| `spacing` | 1.0 | Letter-spacing. 0.92 tight headline fit, 1.08 airy text. |
| `kerning` | 1.0 | Kerning strength. 0 turns kerning off. |
| `weight_comp` | 0.9 | How much letters widen as weight grows. Lower keeps Bold narrow. |

## Spec fields outside `design`

```json
{
  "family": "Family Name",
  "version": "1.000",
  "designer": "Name",
  "designer_url": "https://...",
  "description": "One or two sentences.",
  "license": "SIL Open Font License 1.1",
  "license_url": "https://openfontlicense.org",
  "vendor": "ABCD",
  "preset": "grotesque",
  "weights": [300, 400, 700],
  "glyphs": "my_glyphs.py",
  "design": { }
}
```

`weights` may use any of 100 to 900 in steps of 100. Masters are created
for the lightest, the heaviest and 400 when it lies between them.

For full control, set `"masters"` instead: a map from weight to parameter
overrides, for example `{"300": {"stem": 50}, "800": {"stem": 160, "aperture": 0.7}}`.
Any numeric parameter can differ between masters and will interpolate.
