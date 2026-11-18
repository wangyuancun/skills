"""FontWorks as an MCP server.

Local (stdio), for Claude Desktop, Claude Code, Cursor, Windsurf, VS Code, Codex:
    fontworks mcp

Remote (Streamable HTTP), for ChatGPT developer mode and any hosted client:
    fontworks mcp --http --port 8000 --public-url https://your-tunnel.example
In HTTP mode every file lives in one work folder, photos can be given as URLs,
and results come back as download links served by the same server.
"""
from __future__ import annotations

import contextlib
import io
import json
import os

GUIDE = """FontWorks is a type foundry. Work like one:
1. Call `menu` and offer the routes unless the user already chose.
2. Describe route: `new_font` with a preset and design changes, then `build_font(draft=True)`, LOOK at the proof image,
   fix with `update_design`, rebuild, at least two rounds, then `build_font(draft=False)`.
3. Handwriting route: `handwriting_sheet` -> user prints, writes, photographs -> `read_sheet_photos` -> `build_font`.
4. Quick photo route (also for plain paper, no printer): `find_letters` -> read the numbered image -> `label_letters` -> `build_font`.
Only make original fonts. Never copy a commercial typeface. Always show the user the proof and the Studio link."""


class Ctx:
    """Where files go and how they are handed back."""

    def __init__(self, remote=False, workdir=None, public_url=None):
        self.remote = remote
        self.workdir = os.path.abspath(workdir or (os.path.join(os.getcwd(), "fontworks-work") if remote else os.getcwd()))
        self.public_url = (public_url or "").rstrip("/")
        os.makedirs(self.workdir, exist_ok=True)
        if remote:
            os.chdir(self.workdir)          # default build folders land inside the work folder

    def path(self, p):
        """Local mode: any path. Remote mode: always inside the work folder."""
        if not self.remote:
            return os.path.abspath(p)
        full = os.path.abspath(os.path.join(self.workdir, p.lstrip("/\\")))
        if os.path.commonpath([full, self.workdir]) != self.workdir:
            raise ValueError("Paths must stay inside the work folder.")
        return full

    def show(self, p):
        """How to present a file to the user: a link when remote, a path when local."""
        p = os.path.abspath(p)
        if self.remote and self.public_url and p.startswith(self.workdir):
            return f"{self.public_url}/files/{os.path.relpath(p, self.workdir).replace(os.sep, '/')}"
        return p

    def fetch(self, src, folder="uploads"):
        """Local files only. Remote URL fetching disabled (SSRF / no-network build)."""
        if src.startswith(("http://", "https://")):
            raise ValueError(
                "Remote URL input is disabled in this build. Save the image to a "
                "local file first and pass its path."
            )
        return self.path(src)


def _run(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        res = fn(*a, **k)
    return res, buf.getvalue()


def make_server(ctx: Ctx | None = None, **server_kw):
    try:                                    # mcp 2.x
        from mcp.server.mcpserver import MCPServer as Server, Image
    except ImportError:                     # mcp 1.x
        from mcp.server.fastmcp import FastMCP as Server, Image
    from . import brand, handwriting as hw
    from .cli import run_build
    from .context import DEFAULTS
    from .presets import PRESETS

    ctx = ctx or Ctx()
    try:
        mcp = Server("fontworks", instructions=GUIDE, version=brand.VERSION, **server_kw)
    except TypeError:
        mcp = Server("fontworks", instructions=GUIDE, **server_kw)

    import functools
    from . import telemetry
    _seen = {"client": False}

    def _who():
        if _seen["client"]:
            return
        try:
            ci = mcp.get_context().session.client_params.clientInfo
            telemetry.set_client(ci.name, getattr(ci, "version", ""))
            _seen["client"] = True
        except Exception:
            pass

    _plain_tool = mcp.tool

    def tool(*a, **k):
        deco = _plain_tool(*a, **k)

        def wrap(fn):
            @functools.wraps(fn)
            def inner(*args, **kwargs):
                _who()
                telemetry.track("tool_called", tool=fn.__name__, surface="mcp", transport="http" if ctx.remote else "stdio")
                return fn(*args, **kwargs)
            return deco(inner)
        return wrap

    mcp.tool = tool

    @mcp.tool()
    def menu() -> str:
        """Show the six ways to make a font. Start here."""
        return brand.menu_text() + "\n\n" + GUIDE

    @mcp.tool()
    def presets() -> str:
        """List style presets and every design parameter with its default."""
        return json.dumps(dict(presets=PRESETS, parameters=DEFAULTS), indent=1)

    @mcp.tool()
    def new_font(family: str, preset: str = "geometric", weights: list[int] = [300, 400, 700], design: dict = {},
                 designer: str = "", description: str = "", license: str = "", folder: str = ".") -> str:
        """Create a font spec from a brief. `design` overrides preset parameters (see `presets`). Returns the spec path."""
        if preset not in PRESETS:
            return f"Unknown preset. Choose from: {', '.join(PRESETS)}"
        bad = [k for k in design if k not in DEFAULTS]
        if bad:
            return f"Unknown design parameter(s): {', '.join(bad)}"
        d = ctx.path(folder)
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, family.replace(" ", "") + ".json")
        with open(path, "w") as f:
            json.dump(dict(family=family, version="1.000", designer=designer, description=description, license=license,
                           preset=preset, weights=weights, design=design), f, indent=2)
        return os.path.relpath(path, ctx.workdir) if ctx.remote else path

    @mcp.tool()
    def update_design(spec: str, design: dict = {}, weights: list[int] = [], glyphs_file: str = "") -> str:
        """Change design parameters, weights or the custom glyph file of an existing spec."""
        spec = ctx.path(spec)
        with open(spec) as f:
            data = json.load(f)
        bad = [k for k in design if k not in DEFAULTS]
        if bad:
            return f"Unknown design parameter(s): {', '.join(bad)}"
        data.setdefault("design", {}).update(design)
        if weights:
            data["weights"] = weights
        if glyphs_file:
            data["glyphs"] = glyphs_file
        with open(spec, "w") as f:
            json.dump(data, f, indent=2)
        return json.dumps(data["design"])

    @mcp.tool()
    def build_font(spec: str, draft: bool = True, out: str = "") -> list:
        """Run the foundry pipeline. draft=True is fast (static fonts + proof). draft=False makes the full release:
        variable font, TTF, OTF, WOFF2, CSS, QA report and the Studio app. Returns the stage log and the proof image."""
        spec = ctx.path(spec)
        try:
            (o, fails, png), log = _run(run_build, spec, ctx.path(out) if out else None, draft, True)
        except SystemExit as e:
            return [f"Build failed: {e}"]
        o = os.path.abspath(o)
        msg = log + ("" if ctx.remote else f"\noutput folder: {o}")
        if draft and png:
            msg += f"\nproof: {ctx.show(png)}"
        if not draft:
            import shutil
            fonts = os.path.join(o, "fonts")
            z = shutil.make_archive(os.path.join(o, os.path.basename(o)), "zip", fonts)
            msg += f"\nstudio app: {ctx.show(os.path.join(fonts, 'studio.html'))}"
            msg += f"\nfont files (zip): {ctx.show(z)}"
            msg += "\nQA: " + ("FAILED checks, see report.md" if fails else "all checks pass")
        res = [msg]
        if png and os.path.exists(png):
            res.append(Image(path=png))
        return res

    @mcp.tool()
    def inspect_glyphs(spec: str, glyphs: str, outline: bool = False) -> list:
        """Close-up image of letters at every master weight. `glyphs` is a string of characters, for example "agsR&"."""
        from .cli import _names
        from .inspect_glyph import render
        spec = ctx.path(spec)
        out = os.path.join(os.path.dirname(spec), "glyphs.png")
        try:
            render(spec, [n for c in glyphs.split() or [glyphs] for n in _names(c)], out, outline=outline)
        except SystemExit as e:
            return [str(e)]
        return [Image(path=out)]

    @mcp.tool()
    def handwriting_sheet(folder: str = "sheets") -> list:
        """Make the printable handwriting sheets (PDF). The user prints, writes one character per box, and photographs each sheet."""
        files = hw.write_sheets(ctx.path(folder))
        return ["Sheets:\n" + "\n".join(ctx.show(f) for f in files)
                + "\nSheet 1 (letters, 0 to 3) is enough for a font. Sheet 2 adds figures and punctuation."
                + "\nNo printer? Use find_letters on a photo of writing on any plain paper.",
                Image(path=[f for f in files if f.endswith(".png")][0])]

    @mcp.tool()
    def read_sheet_photos(photos: list[str], family: str, weights: list[int] = [400], neat: float = 0.5,
                          ink: float = 0.0, designer: str = "", folder: str = "") -> str:
        """Turn photos of filled-in sheets into a font project. Photos are file paths or http(s) URLs.
        neat: 0 keeps every wobble, 1 lines letters up. ink: heavier (+) or lighter (-) strokes in font units.
        Returns the spec path; then call build_font."""
        logs = []
        try:
            samples = []
            for p in photos:
                samples += hw.read_sheet(ctx.fetch(p), log=logs.append)[1]
            if len(samples) < 5:
                return "Too few characters were readable. Ask for a sharper, flatter photo with all four corner squares visible."
            spec = hw.make_font_project(samples, family, ctx.path(folder or family.replace(" ", "")), weights, ink, neat,
                                        designer, log=logs.append)
        except (ValueError, OSError) as e:
            return str(e)
        return "\n".join(logs) + f"\nspec: {os.path.relpath(spec, ctx.workdir) if ctx.remote else spec}"

    @mcp.tool()
    def find_letters(photo: str, folder: str = "segments") -> list:
        """Quick photo route, step 1: find the characters in any photo of writing (path or http(s) URL).
        Returns a numbered image. Read it and call label_letters with the characters in number order."""
        try:
            contact, count, lines = hw.segment(ctx.fetch(photo), ctx.path(folder))
        except (ValueError, OSError) as e:
            return [str(e)]
        return [f"{count} characters on {lines} line(s). Segment folder: {folder}", Image(path=contact)]

    @mcp.tool()
    def label_letters(folder: str, family: str, labels: dict = {}, text: str = "", weights: list[int] = [400],
                      neat: float = 0.5, ink: float = 0.0, designer: str = "", out: str = "", even: bool = False) -> str:
        """Quick photo route, step 2: name the numbered characters. `labels` maps box number to character
        ({"1": "H", "2": "a"}; leave out boxes that are not letters), or give `text` with every character in order.
        `even` redraws every stroke with one steady pen: use it for ballpoint or phone photos, where the ink is
        blotchy or faint in places, to get a cleaner, finished font."""
        logs = []
        try:
            samples = hw.read_labeled(ctx.path(folder), labels or text, log=logs.append)
            if len(samples) < 5:
                return "Too few characters to make a font. Ask for more writing: 'Sphinx of black quartz, judge my vow' covers a to z."
            spec = hw.make_font_project(samples, family, ctx.path(out or family.replace(" ", "")), weights, ink, neat,
                                        designer, log=logs.append, route="photo", even=even)
        except (ValueError, KeyError, OSError) as e:
            return f"Could not label: {e}"
        return "\n".join(logs) + f"\nspec: {os.path.relpath(spec, ctx.workdir) if ctx.remote else spec}"

    if ctx.remote:
        from starlette.responses import FileResponse, HTMLResponse, PlainTextResponse

        @mcp.custom_route("/files/{path:path}", methods=["GET"])
        async def files(request):
            try:
                p = ctx.path(request.path_params["path"])
            except ValueError:
                return PlainTextResponse("not found", status_code=404)
            if not os.path.isfile(p):
                return PlainTextResponse("not found", status_code=404)
            return FileResponse(p)

        @mcp.custom_route("/", methods=["GET"])
        async def home(request):
            return HTMLResponse(f'<!doctype html><title>fontworks</title><body style="font:16px system-ui;background:{brand.CREAM};'
                                f'color:{brand.INK};padding:40px"><svg width="48" viewBox="0 0 100 100">{brand.mark(0, 0, 100)}</svg>'
                                f'<h1>fontworks MCP server</h1><p>Connect your client to <code>/mcp</code>. Docs: {brand.SITE}</p>')
    return mcp


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="fontworks mcp")
    ap.add_argument("--http", action="store_true", help="serve Streamable HTTP (for ChatGPT and other remote clients)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    ap.add_argument("--public-url", default=os.environ.get("FONTWORKS_PUBLIC_URL", ""),
                    help="the address clients reach this server at, used for download links")
    ap.add_argument("--workdir", default=os.environ.get("FONTWORKS_WORKDIR"))
    a = ap.parse_args(argv)
    from . import telemetry
    telemetry.SURFACE["name"] = "mcp"
    telemetry.track("mcp_started", transport="http" if a.http else "stdio", surface="mcp")
    try:
        if not a.http:
            make_server(Ctx()).run()
            return 0
        ctx = Ctx(remote=True, workdir=a.workdir, public_url=a.public_url or f"http://{a.host}:{a.port}")
        try:
            server = make_server(ctx)
            from mcp.server.mcpserver import MCPServer  # noqa: F401  (2.x: options go to run)
            server.run("streamable-http", host=a.host, port=a.port, stateless_http=True)
        except ImportError:
            server = make_server(ctx, host=a.host, port=a.port, stateless_http=True)
            server.run("streamable-http")
    except ImportError:
        raise SystemExit("The MCP server needs the 'mcp' package: pip install mcp")
    return 0


if __name__ == "__main__":
    main()
