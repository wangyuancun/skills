"""Style archetypes. A spec names one preset and overrides what it wants."""

PRESETS = {
    # Circles and straight lines. Futura / Avenir territory.
    "geometric": dict(o_ratio=1.02, n_ratio=0.88, O_ratio=1.06, roundness=0.5523, branch=0.56, join=0.78,
                      aperture=0.55, cut="perp", contrast=0.0, hratio=0.92, a="single", dot="round", asc=760),
    # Neutral workhorse. Closed apertures, horizontal terminals, tall x-height.
    "grotesque": dict(xh=520, o_ratio=0.94, n_ratio=0.86, O_ratio=1.0, H_ratio=0.74, roundness=0.6, branch=0.68,
                      join=0.7, aperture=0.15, cut="h", contrast=0.06, hratio=0.88, dot="square", asc=730, cap=714),
    # Open, warm, built for reading. Some stroke contrast, open apertures.
    "humanist": dict(xh=490, o_ratio=0.98, n_ratio=0.88, O_ratio=1.04, roundness=0.56, branch=0.62, join=0.66,
                     aperture=0.9, cut="perp", contrast=0.16, hratio=0.9, dot="round", asc=750),
    # Soft and friendly: round stroke ends, generous curves.
    "rounded": dict(o_ratio=1.0, n_ratio=0.9, roundness=0.58, branch=0.6, join=0.8, aperture=0.5, cut="perp",
                    terminal="round", dot="round", contrast=0.0, hratio=0.96, a="single", spacing=1.04, soften=0.32),
    # Sturdy slab serif with low contrast.
    "slab": dict(xh=500, o_ratio=0.98, n_ratio=0.92, roundness=0.58, branch=0.64, join=0.72, aperture=0.3, cut="v",
                 serif="slab", contrast=0.04, hratio=0.86, dot="round", spacing=0.9, H_ratio=0.78),
    # Squared-off curves, engineered feel. DIN / Eurostile territory.
    "technical": dict(xh=510, o_ratio=0.9, n_ratio=0.86, O_ratio=0.94, roundness=0.74, branch=0.72, join=0.74,
                      aperture=0.2, cut="h", contrast=0.0, hratio=0.94, dot="square", width=0.98),
    # Tall, narrow, loud. Headlines and posters.
    "condensed": dict(xh=540, cap=720, asc=740, width=0.72, o_ratio=0.9, n_ratio=0.86, O_ratio=0.94, H_ratio=0.74,
                      roundness=0.66, branch=0.72, join=0.7, aperture=0.12, cut="h", contrast=0.08, hratio=0.86,
                      dot="square", spacing=1.2, weight_comp=0.75),
    # High contrast sans for display sizes: thin horizontals, fashion feel.
    "contrast": dict(xh=480, o_ratio=1.0, n_ratio=0.88, O_ratio=1.06, roundness=0.56, branch=0.6, join=0.55,
                     aperture=0.6, cut="v", contrast=0.55, hratio=0.9, dot="round", asc=760, soften=0.04),
}

# Stem multiplier per weight class, relative to Regular (400).
WEIGHT_STEM = {100: 0.26, 200: 0.44, 300: 0.66, 400: 1.0, 500: 1.19, 600: 1.4, 700: 1.66, 800: 1.92, 900: 2.2}
WEIGHT_NAME = {100: "Thin", 200: "ExtraLight", 300: "Light", 400: "Regular", 500: "Medium", 600: "SemiBold",
               700: "Bold", 800: "ExtraBold", 900: "Black"}
