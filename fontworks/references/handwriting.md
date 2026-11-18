# Handwriting and photo routes

## The sheet

`fontworks.py sheet` writes a two-page PDF (fits A4 and US Letter).

- Four black corner squares let the engine find and square up the page from a
  phone photo taken at an angle.
- Each box has a baseline (solid), an x-height line and a cap line (dashed).
  All guides are printed in a red that drops out when the photo is read, so
  only the ink remains.
- Page 1: A to Z, a to z, 0 to 3. Page 2: 4 to 9, punctuation, currency, quotes.

## Tell the user

- Dark pen or marker. Pencil and light blue ink are too faint.
- One character per box, sitting on the solid red line, not touching the box edge.
- Capitals reach the top dashed line; small letters like x reach the middle line.
- Photo: flat, even light, no shadow of the phone, whole page in frame, in focus.
- Any colour of ink works except red or pink.

## What the engine measures

| Measured | Used for |
| --- | --- |
| Cap height | scaled so capitals are 700 units |
| x-height, ascender, descender | the font's vertical metrics |
| Stroke width (ink area over outline length) | weight of every engine-drawn glyph, so they match |
| Each letter's ink | traced to smooth curves |

## Options

| Option | Effect |
| --- | --- |
| `--neat 0` | exactly as written: every letter keeps its own size and bounce |
| `--neat 0.5` | default: half way to aligned |
| `--neat 1` | letters lined up on shared heights, like type |

`--even` traces the centre line of every stroke and draws it again with one steady pen. Blots, faint ballpoint lines, broken strokes and ragged phone-photo edges go; the writer's shapes stay. Strokes that nearly touch inside a letter are joined (never the dot of i, j, ! or ?). Recommended for any phone photo: `--even --neat 0.9`.
| `--ink 20` | strokes 20 units heavier (use for thin ballpoint) |
| `--ink -20` | lighter (use for a fat marker that fills in) |
| `--weights 400,700` | adds weights by growing the same strokes |

## Problems and fixes

| Message or symptom | Fix |
| --- | --- |
| "Could not find the sheet's corner squares" | retake with all four squares visible, less glare, closer |
| "touching the box edge" | that letter may be cut off; rewrite it smaller or accept it |
| A letter is missing from the count | it was too faint; rewrite darker, or let the engine draw it |
| Counters filled in (a, e look like blobs) | `--ink -15`, or a thinner pen |
| Letters look ragged | photo was blurry or small; retake closer |
| Wrong letter in a box | rewrite that box on a fresh sheet and photograph it; later photos can be passed together |

## Quick photo notes

`segment` works best on dark writing on a plain light background with letters
that do not touch. Joined letters are found as one shape; skip them in the
label map. Dots of i and j and other stacked parts are merged automatically.
Sloping lines are handled.
