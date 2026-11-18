# Critique checklist

Look at `proof.png` with this list. For each problem, the usual fix follows.

## Colour and rhythm (the text block)

- **Even grey?** Squint at the paragraph. Dark clumps or pale holes mean spacing trouble.
  Clumps everywhere: raise `spacing`. Holes around round letters: lower `o_ratio` or raise `spacing` slightly.
- **Does it read at 20px?** If letters fill in, raise `aperture`, raise `xh`, lower `stem`.
- **Word shapes distinct?** If a, e, c, o look alike, raise `aperture` or switch `a` to `"double"`.

## Spacing strings

- `nnnonnoon`: the gaps between n-n, n-o and o-o should feel equal. They are computed, so a
  mismatch usually means an extreme proportion; move `o_ratio` and `n_ratio` closer together.
- `HHHOHHOOH`: same test for capitals.
- Figures should sit a little looser than letters.

## Kerning

- `AVATAR`, `To`, `LT`, `Ty`: no gaps, no collisions. Too tight: lower `kerning` (0.8). Too loose: raise it (1.15).
- Punctuation after r, y, T, F, P should tuck in without touching.

## Individual letters (use the `glyph` command)

- **a, e, s in the heaviest weight**: counters must stay open. If they clog: lower `weight_comp` less
  (letters need width), raise `aperture`, or lower the heaviest weight in `weights`.
- **Joins of n, m, b, p**: a dark knot at the join means `join` is too high for that weight.
- **S and s**: should not lean. If top-heavy, redraw with a custom glyph.
- **g, y, j descenders**: enough depth to read; deepen `desc` if cramped.
- **Round vs flat alignment**: o should pass the baseline slightly. If round letters look small, raise `overshoot`.
- **Capitals vs lowercase**: capitals should look only a little darker. Adjust `cap_stem`.

## Family

- Each weight should be clearly different from its neighbours.
- The lightest weight must still hold together; the heaviest must not clog.
- Proportions should feel related across weights.

## Character

- Does the proof match the three adjectives from the brief? If it looks generic, pick two or
  three letters and give them a custom drawing, or push one parameter further than is comfortable.
