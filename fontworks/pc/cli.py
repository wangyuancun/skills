"""FontWorks command line.

  fontworks menu                              the six ways to make a font
  fontworks presets                           list the style presets
  fontworks bases                             list open-source base fonts for route 6
  fontworks telemetry [on|off]                telemetry status (disabled in this build)
  fontworks new "Family" --preset P           write a starter spec
  fontworks build spec.json [--draft]         run the foundry pipeline
  fontworks glyph spec.json a g R             close-up of single glyphs
  fontworks sheet [--out DIR]                 printable handwriting sheets
  fontworks read-sheet PHOTO... --family N    photos of filled sheets -> font project
  fontworks segment PHOTO                     find letters in any photo
  fontworks label SEGDIR --text "..." --family N   name the letters -> font project
  fontworks mcp                               run as an MCP server (Claude Desktop, Cursor, ...)
"""
import argparse
import json
import os
import sys


def _names(token):
    from .glyphs_latin import GLYPHS
    from . import glyphs_extra  # noqa: F401
    if token in GLYPHS:
        return [token]
    by_uni = {v[1]: k for k, v in GLYPHS.items() if v[1]}
    out = [by_uni[ord(c)] for c in token if ord(c) in by_uni]
    if not out:
        sys.exit(f"no such glyph: {token}")
    return out


def run_build(spec, out=None, draft=False, proof=True):
    """Build a family. Returns (out dir, fails, proof png or None)."""
    import time
    from . import telemetry
    from .build import build, load_spec
    from .release import release
    sp = load_spec(spec)
    fam = sp["family"].replace(" ", "")
    out = out or os.path.join("build", fam)
    route, t0 = telemetry.route_of(sp), time.time()
    telemetry.track("build_started", route=route, draft=draft, surface=telemetry.SURFACE["name"])
    try:
        result = build(spec, out, formats=("ttf",) if draft else ("variable", "ttf", "otf", "woff2"))
        fails = 0
        if not draft:
            fails, _ = release(result)
        png = None
        if proof:
            from .proof import proof as make_proof
            svg = make_proof(result, os.path.join(out, "proof.svg"))
            candidate = svg[:-4] + ".png"
            png = candidate if os.path.exists(candidate) else None
    except BaseException as e:
        telemetry.track("build_failed", route=route, draft=draft, surface=telemetry.SURFACE["name"], error=type(e).__name__,
                        seconds=round(time.time() - t0, 1))
        raise
    telemetry.track("build_completed", route=route, draft=draft, surface=telemetry.SURFACE["name"], qa_fails=fails,
                    weights=len(result.get("weights", [])), seconds=round(time.time() - t0, 1),
                    base=sp.get("base") or (sp.get("remix") or {}).get("base") if route == "open_base" else None)
    return out, fails, png


def main(argv=None):
    from . import telemetry
    try:
        return _main(argv)
    finally:
        telemetry.flush()


def _main(argv=None):
    from . import brand
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv[:1] == ["mcp"]:                      # the server has its own options
        from .mcp_server import main as serve
        return serve(argv[1:])
    ap = argparse.ArgumentParser(prog="fontworks", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version="fontworks " + brand.VERSION)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("menu")
    sub.add_parser("presets")
    sub.add_parser("bases", help="list open-source base fonts for the remix route")
    tl = sub.add_parser("telemetry", help="telemetry status (disabled in this build)")
    tl.add_argument("state", nargs="?", choices=["status", "on", "off"], default="status")
    sub.add_parser("mcp", help="run as an MCP server (add --http for ChatGPT)")
    n = sub.add_parser("new")
    n.add_argument("family")
    n.add_argument("--preset", default="geometric")
    n.add_argument("--weights", default="300,400,700")
    n.add_argument("--out", default=None)
    b = sub.add_parser("build")
    b.add_argument("spec")
    b.add_argument("--out", default=None, help="output folder (default: build/<Family>)")
    b.add_argument("--draft", action="store_true", help="fast pass: static TTFs and proof only")
    b.add_argument("--no-proof", action="store_true")
    g = sub.add_parser("glyph")
    g.add_argument("spec")
    g.add_argument("names", nargs="+")
    g.add_argument("--weight", type=int)
    g.add_argument("--outline", action="store_true")
    g.add_argument("--out", default="glyphs.png")
    s = sub.add_parser("sheet")
    s.add_argument("--out", default="sheets")
    for name in ("read-sheet", "label"):
        r = sub.add_parser(name)
        r.add_argument("inputs", nargs="+", help="photos (read-sheet) or the segment folder (label)")
        r.add_argument("--family", required=True)
        r.add_argument("--out", default=None, help="project folder (default: the family name)")
        r.add_argument("--weights", default="400", help="for example 400,700")
        r.add_argument("--neat", type=float, default=0.5, help="0 keeps every wobble, 1 lines letters up like type")
        r.add_argument("--ink", type=float, default=0.0, help="make strokes heavier (+) or lighter (-), in font units")
        r.add_argument("--even", action="store_true", help="redraw every stroke with one steady pen: cleaner, more finished")
        r.add_argument("--designer", default="")
        if name == "label":
            r.add_argument("--text", help="the characters in reading order, as numbered on segments.png")
            r.add_argument("--map", help='JSON like {"1": "H", "2": "a"} for exact control')
    sg = sub.add_parser("segment")
    sg.add_argument("photo")
    sg.add_argument("--out", default="segments")
    a = ap.parse_args(argv)

    if a.cmd == "menu":
        print(brand.menu_text())
        return 0
    if a.cmd == "telemetry":
        from . import telemetry
        print("telemetry: off (disabled in this build; no data leaves your machine)")
        return 0
    if a.cmd == "bases":
        from .remix import BASES, BUNDLED
        files = set(os.listdir(BUNDLED)) if os.path.isdir(BUNDLED) else set()
        for k, (path, nm, note) in BASES.items():
            tag = "bundled" if os.path.basename(path) in files else "local file needed"
            print(f"{k:22s} {nm}: {note} [{tag}]")
        print("\nAll SIL Open Font License. Only fonts marked [bundled] ship with the skill;")
        print("others need a local OFL .ttf path. Remixes ship under the OFL with a new name.")
        return 0
    if a.cmd == "presets":
        from .presets import PRESETS
        from .context import DEFAULTS
        for name, p in PRESETS.items():
            print(f"{name:10s} " + ", ".join(f"{k}={v}" for k, v in p.items()))
        print("\nAll parameters and defaults:")
        print(json.dumps(DEFAULTS, indent=2))
        return 0
    if a.cmd == "new":
        from .presets import PRESETS
        if a.preset not in PRESETS:
            sys.exit(f"Unknown preset. Choose from: {', '.join(PRESETS)}")
        spec = {"family": a.family, "version": "1.000", "designer": "", "description": "", "license": "",
                "preset": a.preset, "weights": [int(w) for w in a.weights.split(",")], "design": {}}
        path = a.out or (a.family.replace(" ", "") + ".json")
        with open(path, "w") as f:
            json.dump(spec, f, indent=2)
        print(f"wrote {path}")
        return 0
    if a.cmd == "glyph":
        from .inspect_glyph import render
        names = [x for nme in a.names for x in _names(nme)]
        print("wrote", render(a.spec, names, a.out, a.weight, outline=a.outline))
        return 0
    if a.cmd == "sheet":
        from .handwriting import write_sheets
        brand.banner("handwriting sheets")
        for p in write_sheets(a.out):
            print("wrote", p)
        print("Print at 100% (no scaling to fit is needed, but it is fine). Sheet 1 is enough; sheet 2 adds punctuation.")
        return 0
    if a.cmd == "segment":
        from .handwriting import segment
        brand.banner("quick photo")
        try:
            contact, count, lines = segment(a.photo, a.out)
        except ValueError as e:
            sys.exit(str(e))
        print(f"found {count} characters on {lines} line(s)")
        print(f"look at {contact}, then run: fontworks label {a.out} --text \"<the characters in number order>\" --family \"Name\"")
        return 0
    if a.cmd in ("read-sheet", "label"):
        from . import handwriting as hw
        brand.banner("handwriting")
        weights = [int(w) for w in a.weights.split(",")]
        try:
            if a.cmd == "read-sheet":
                samples = []
                for p in a.inputs:
                    samples += hw.read_sheet(p)[1]
            else:
                labels = json.loads(a.map) if a.map else a.text
                if not labels:
                    sys.exit("give --text or --map")
                samples = hw.read_labeled(a.inputs[0], labels)
        except ValueError as e:
            sys.exit(str(e))
        if len(samples) < 5:
            sys.exit("Too few characters were readable to make a font. Check the photo and try again.")
        out = a.out or a.family.replace(" ", "")
        spec = hw.make_font_project(samples, a.family, out, weights, a.ink, a.neat, a.designer,
                                    route="handwriting" if a.cmd == "read-sheet" else "photo", even=getattr(a, "even", False))
        print(f"wrote {spec}\nnext: fontworks build {spec} --draft")
        return 0
    if a.cmd == "build":
        brand.banner()
        out, fails, png = run_build(a.spec, a.out, a.draft, not a.no_proof)
        if png:
            print(f"\nproof: {png}  (look at it before calling the font done)")
        if not a.draft:
            print(f"studio: {os.path.join(out, 'fonts', 'studio.html')}  (the font's app: open or publish it)")
        print(f"output: {out}")
        return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
