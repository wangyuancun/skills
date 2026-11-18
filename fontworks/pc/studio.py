"""FontWorks Studio: one self-contained HTML file that is the font's home.

A foundry-grade specimen app: type tester with presets, colourways and a
system-font comparison; waterfall; animated weight axis; glyph inspector with
every outline point and handle; kerning explorer; layouts in use; language
support; full specs and QA; install guides for desktop, web, Tailwind,
Next.js, Figma and Canva; per-file and whole-family downloads; a printable
specimen. Every font is embedded, so the file works offline.
"""
from __future__ import annotations

import base64
import io
import json
import os
import zipfile

from . import brand
from .presets import WEIGHT_NAME


def _b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _zip(fonts_dir, fid):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in sorted(os.walk(fonts_dir)):
            for fn in sorted(files):
                if fn == "studio.html" or ("Flex[" in fn and fn.endswith(".ttf")):
                    continue   # the lab's full design space ships in the folder, not the in-page zip
                full = os.path.join(root, fn)
                z.write(full, os.path.join(fid, os.path.relpath(full, fonts_dir)))
    return base64.b64encode(buf.getvalue()).decode()


def _field_b64(meadow=False, w=1400, h=640):
    from PIL import Image
    buf = io.BytesIO()
    Image.fromarray(brand.field(w, h, "meadow" if meadow else "haze", seed=4, grain=14)).save(buf, "JPEG", quality=78)
    return base64.b64encode(buf.getvalue()).decode()


def glyph_table(ttf):
    """Kept for callers of the first Studio: (rows, metrics, features)."""
    from .studio_data import measure
    m = measure({400: ttf})
    return [g[:4] for g in m["glyphs"]], m["metrics"], m["features"]


def build_studio(result, qa=None, qa_lines=None):
    from .studio_data import file_list, measure
    fam, fid = result["family"], result["family_id"]
    fonts = os.path.join(result["out"], "fonts")
    ws = result["weights"]
    reg = 400 if 400 in ws else ws[len(ws) // 2]
    faces = []
    if result["variable"]:
        vf = os.path.join(fonts, "webfonts", f"{fid}[wght].woff2")
        faces.append(dict(src=_b64(vf), weight=f"{min(result['masters'])} {max(result['masters'])}"))
    else:
        for w in ws:
            p = os.path.join(fonts, "webfonts", f"{fid}-{WEIGHT_NAME.get(w, w)}.woff2")
            if os.path.exists(p):
                faces.append(dict(src=_b64(p), weight=str(w)))
    ttfs = {}
    for w in ws:
        p = os.path.join(fonts, "ttf", f"{fid}-{WEIGHT_NAME.get(w, w)}.ttf")
        if os.path.exists(p):
            ttfs[w] = p
    first = ttfs.get(reg) or next(iter(ttfs.values()))
    ttfs = dict([(reg, first)] + [(w, p) for w, p in ttfs.items() if w != reg])
    m = measure(ttfs)
    spec = result["spec"]
    data = dict(family=fam, id=fid, version=spec.get("version", "1.000"), designer=spec.get("designer", ""),
                description=spec.get("description") or "An original typeface.",
                license=spec.get("license") or ("SIL Open Font License 1.1" if spec.get("mode") == "remix" else "All rights reserved"),
                license_url=spec.get("license_url", ""),
                weights=[[w, WEIGHT_NAME.get(w, str(w))] for w in ws], variable=result["variable"],
                range=[min(result["masters"]), max(result["masters"])], regular=reg,
                glyphs=m["glyphs"], shapes={str(k): v for k, v in m["shapes"].items()}, metrics=m["metrics"],
                features=m["features"], kern=m["kern"], kern_total=m["kern_total"], languages=m["languages"],
                files=file_list(fonts), qa=qa or "", qa_lines=qa_lines or [],
                source=("handwriting" if spec.get("mode") == "handwriting" else spec.get("preset", "custom")),
                tool=f"{brand.NAME} {brand.VERSION}", site=brand.SITE, repo=brand.REPO)
    flex = result.get("flex")
    if flex:
        fx = os.path.join(fonts, "webfonts", flex["file"][:-4] + ".woff2")
        if os.path.exists(fx):
            from .presets import WEIGHT_STEM
            d0 = result["design"]
            if flex.get("remix"):
                data["flex"] = dict(axes=flex["axes"], file=flex["file"], remix=True, base_name=d0.get("base_name", ""),
                                    base=d0.get("base", ""))
            else:
                data["flex"] = dict(axes=flex["axes"], file=flex["file"], stemf={str(k): v for k, v in WEIGHT_STEM.items()},
                                    base={k: d0[k] for k in ("width", "stem", "xh", "hratio", "roundness", "soften",
                                                              "aperture", "slant")})
            faces.append(dict(src=_b64(fx), weight=None, family="PCFLEX"))
    face_css = "\n".join(
        f'@font-face{{font-family:"{f.get("family", "PCX")}";src:url(data:font/woff2;base64,{f["src"]}) format("woff2");'
        + (f'font-weight:{f["weight"]};' if f["weight"] else "") + 'font-display:block}'
        for f in faces)
    from .mockups import CSS as MK_CSS, JS as MK_JS, SECTION as MK_SEC, data as mk_data
    page = STUDIO.replace("<!--MOCKUPS-->", MK_SEC).replace("/*MKCSS*/", MK_CSS).replace("//MKJS", MK_JS.replace("__MOCKS__", mk_data()))
    page = page.replace("/*FACES*/", face_css).replace("__DATA__", json.dumps(data, separators=(",", ":")))
    page = page.replace("__ZIP__", _zip(fonts, fid)).replace("__MARK__", brand.mark(0, 0, 32))
    word, ww = brand.wordmark(0, 17, 21, fill="currentColor")
    page = page.replace("__WORD__", word).replace("__WMW__", f"{ww:.0f}")
    hand = spec.get("mode") == "handwriting"
    page = page.replace("__GRAIN__", brand.grain_css(0.14)).replace("__FIELD__", _field_b64(hand))
    page = page.replace("__FIELD2__", _field_b64(not hand, 900, 1200))
    page = page.replace("/*VARS*/", brand.css_vars()).replace("__SITE__", brand.SITE)
    page = page.replace("__FAVICON__", base64.b64encode(brand.favicon_svg().encode()).decode())
    page = page.replace("__TITLE__", brand.esc(fam)).replace("__BRANDFONT__", _b64(brand.font_path("Regular")))
    page = page.replace("__BRANDBOLD__", _b64(brand.font_path("ExtraBold")))
    from . import telemetry
    snip = "" if spec.get("telemetry") is False else telemetry.studio_snippet()
    page = page.replace("</body></html>", snip + "</body></html>") if "</body></html>" in page else page.replace("</body>", snip + "</body>")
    path = os.path.join(fonts, "studio.html")
    with open(path, "w") as f:
        f.write(page)
    return path


STUDIO = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__ · FontWorks Studio</title>
<link rel="icon" href="data:image/svg+xml;base64,__FAVICON__">
<style>
/*FACES*/
@font-face{font-family:"PCUI";src:url(data:font/ttf;base64,__BRANDFONT__);font-weight:400}
@font-face{font-family:"PCUI";src:url(data:font/ttf;base64,__BRANDBOLD__);font-weight:800}
/*VARS*/
*{box-sizing:border-box;margin:0}html{-webkit-text-size-adjust:100%;scroll-behavior:smooth;scroll-padding-top:76px}
body{background:var(--bg) __GRAIN__;color:var(--fg);font:15px/1.45 PCUI,system-ui,sans-serif;transition:background .25s,color .25s}
button,select,input,textarea{font:inherit;color:inherit}a{color:inherit}
code{font:13px ui-monospace,Menlo,monospace;background:var(--card);border:1px solid var(--line);border-radius:6px;padding:1px 5px}
.pc{font-family:"PCX",sans-serif;font-weight:var(--w,400)}
header{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:12px;padding:11px clamp(16px,3vw,32px);background:color-mix(in srgb,var(--bg) 86%,transparent);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
header .brand{display:flex;align-items:center;gap:10px;text-decoration:none}header svg{width:30px;height:30px;flex:none}
header .sub{color:var(--mute)}header nav{display:flex;gap:2px;margin-left:14px;overflow-x:auto;scrollbar-width:none}
header nav a{text-decoration:none;color:var(--mute);padding:7px 11px;border-radius:999px;font-size:14px;white-space:nowrap}
header nav a:hover,header nav a.on{color:var(--fg);background:var(--card)}
header .sp{flex:1}
.btn{border:1px solid var(--line);background:var(--card);border-radius:999px;padding:8px 16px;cursor:pointer;white-space:nowrap;font-size:14px;transition:border-color .15s,transform .1s}
.btn:hover{border-color:var(--fg)}.btn:active{transform:scale(.97)}
.btn.pri{background:var(--acc);border-color:var(--acc);color:var(--acc_fg);font-weight:800}.btn.sm{padding:5px 12px;font-size:13px}
main{max-width:1280px;margin:0 auto;padding:0 clamp(16px,3vw,32px) 80px}
.hero{margin:clamp(14px,2.5vw,24px) 0 0;border-radius:var(--r);overflow:hidden;position:relative;min-height:min(74vh,640px);display:flex;flex-direction:column;justify-content:flex-end;padding:clamp(24px,4vw,48px);background:linear-gradient(rgba(20,24,12,.08),rgba(20,24,12,.38)),#5f6b2f url(data:image/jpeg;base64,__FIELD__) center/cover;color:#fff}
.hero .kick{font-size:12px;letter-spacing:.14em;text-transform:uppercase;opacity:.85}
.hero h1{font-size:clamp(64px,13vw,190px);line-height:.92;letter-spacing:-.015em;overflow-wrap:anywhere;margin:10px 0 14px;text-shadow:0 2px 30px rgba(0,0,0,.15)}
.hero p{max-width:34em;font-size:clamp(16px,1.7vw,20px);opacity:.95}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:1px;margin-top:28px;border-radius:18px;overflow:hidden;background:rgba(255,255,255,.22);backdrop-filter:blur(8px)}
.stats div{background:rgba(20,24,12,.28);padding:14px 16px}.stats b{display:block;font-size:24px;font-weight:800}.stats span{font-size:12px;opacity:.85;letter-spacing:.04em}
section{border-top:1px solid var(--line);padding:clamp(40px,6vw,72px) 0}
.sh{display:flex;align-items:end;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:24px}
h2{font-size:clamp(28px,3.4vw,40px);line-height:1.05;font-weight:800;letter-spacing:-.01em}
.kicker{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--acc);margin-bottom:8px}
.lede{color:var(--mute);max-width:36em;margin-top:8px}
.bar{display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center;padding:12px 14px;background:var(--card);border:1px solid var(--line);border-radius:18px;font-size:13px;color:var(--mute)}
.bar+.bar{margin-top:8px}.bar label{display:flex;align-items:center;gap:8px}.bar b{color:var(--fg);font-weight:400;min-width:38px;font-variant-numeric:tabular-nums}
.bar input[type=range]{accent-color:var(--acc);width:120px}.bar select{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:5px 8px}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden}.seg button{border:0;background:none;padding:5px 11px;cursor:pointer;color:var(--mute)}
.seg button.on{background:var(--fg);color:var(--bg)}
.tog{border:1px solid var(--line);border-radius:999px;padding:4px 11px;cursor:pointer;user-select:none}.tog.on{background:var(--fg);color:var(--bg);border-color:var(--fg)}
.sw{width:24px;height:24px;border-radius:50%;border:2px solid var(--line);cursor:pointer;padding:0}.sw.on{outline:2px solid var(--acc);outline-offset:2px}
.stage{margin-top:14px;border-radius:var(--r);padding:clamp(22px,4vw,48px);background:var(--sbg,transparent);color:var(--sfg,inherit);border:1px solid var(--line);transition:background .2s,color .2s}
#t{outline:none;font-size:96px;line-height:1.08;min-height:1.1em;overflow-wrap:anywhere}
#cmp{margin-top:18px;padding-top:14px;border-top:1px dashed currentColor;opacity:.55;display:none;overflow-wrap:anywhere}
#cmp small,.lab{display:block;font:12px PCUI;letter-spacing:.08em;text-transform:uppercase;opacity:.8;margin-bottom:6px}
.wf div{white-space:nowrap;overflow:hidden;line-height:1.25;padding:4px 0;border-bottom:1px solid var(--line)}.wf span{font:12px PCUI;color:var(--mute);display:inline-block;width:52px}
.wt{display:flex;align-items:baseline;gap:20px;border-bottom:1px solid var(--line);padding:12px 0;white-space:nowrap;overflow:hidden}
.wt span{font-size:12px;color:var(--mute);width:130px;flex:none}.wt div{font-size:clamp(30px,5.4vw,68px);line-height:1.1}
.gtools{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:16px}
.gtools input{flex:1;min-width:200px;background:var(--card);border:1px solid var(--line);border-radius:999px;padding:9px 16px;outline:none}
.gtools input:focus{border-color:var(--acc)}
.cats{display:flex;gap:6px;flex-wrap:wrap}.cats button{border:1px solid var(--line);background:none;border-radius:999px;padding:5px 12px;cursor:pointer;color:var(--mute);font-size:13px}
.cats button.on{background:var(--fg);color:var(--bg);border-color:var(--fg)}.cats i{font-style:normal;opacity:.6;margin-left:4px}
.insp{display:grid;grid-template-columns:minmax(300px,1.35fr) 1fr;gap:24px;margin-bottom:22px}
.big{position:relative;height:clamp(340px,44vw,480px);background:var(--card);border:1px solid var(--line);border-radius:var(--r);overflow:hidden}
.big svg{width:100%;height:100%;display:block}.big .nav{position:absolute;top:12px;right:12px;display:flex;gap:6px}
.big .nav button{width:34px;height:34px;border-radius:50%;border:1px solid var(--line);background:var(--bg);cursor:pointer}
.big .mode{position:absolute;left:12px;top:12px;z-index:2}
.meta{font-size:14px}.meta .ch{font-size:84px;line-height:1.35;height:118px;overflow:hidden;margin-bottom:4px}.meta .nm{color:var(--mute);margin-bottom:16px}
.meta dl{display:grid;grid-template-columns:1fr 1fr;border-top:1px solid var(--line)}.meta dl div{border-bottom:1px solid var(--line);padding:9px 0}
.meta dt{font-size:12px;color:var(--mute)}.meta dd{font-variant-numeric:tabular-nums}.meta .acts{display:flex;gap:8px;margin-top:16px;flex-wrap:wrap}
.gl{display:grid;grid-template-columns:repeat(auto-fill,minmax(62px,1fr));border-left:1px solid var(--line);border-top:1px solid var(--line);border-radius:4px}
.gl div{aspect-ratio:1;display:grid;place-items:center;font-size:30px;border-right:1px solid var(--line);border-bottom:1px solid var(--line);cursor:pointer;transition:background .1s}
.gl div:hover{background:var(--card)}.gl div.sel{background:var(--fg);color:var(--bg)}.empty{color:var(--mute);padding:30px 0}
.kgrid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.kbox{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:20px;text-align:center}
.kbox .k{font-size:clamp(90px,14vw,190px);line-height:1.05;white-space:nowrap}.kbox small{color:var(--mute)}
.kin{display:flex;gap:10px;align-items:center;margin-bottom:16px;flex-wrap:wrap}.kin input{width:110px;text-align:center;font-size:22px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:6px 10px}
.kval{font-size:28px;font-weight:800}.pairs{display:flex;flex-wrap:wrap;gap:6px;margin-top:16px}
.pairs button{border:1px solid var(--line);background:none;border-radius:10px;padding:4px 9px;cursor:pointer;font-size:18px}.pairs button em{font:11px PCUI;color:var(--mute);font-style:normal;margin-left:5px}
.uses{display:grid;grid-template-columns:repeat(12,1fr);gap:16px}
.use{border-radius:var(--r);overflow:hidden;border:1px solid var(--line);position:relative;min-height:300px}
.u-poster{grid-column:span 5;grid-row:span 2;background:#5f6b2f url(data:image/jpeg;base64,__FIELD2__) center/cover;color:#fff;padding:28px;display:flex;flex-direction:column;justify-content:space-between;min-height:620px}
.u-poster h3{font-size:104px;line-height:.92;overflow-wrap:normal;word-break:normal}.u-poster .s{display:flex;justify-content:space-between;font-size:13px;letter-spacing:.08em;text-transform:uppercase}
.u-app{grid-column:span 3;grid-row:span 2;background:var(--sky,#cdd9dc);display:grid;place-items:center;padding:24px;color:#171612}
.phone{width:100%;max-width:240px;aspect-ratio:9/18.5;background:#f4efe4;border-radius:34px;border:8px solid #171612;padding:22px 16px;display:flex;flex-direction:column;gap:10px}
.phone .t{font-size:30px;line-height:1}.phone .c{background:#fff;border-radius:16px;padding:12px}.phone .c b{font-size:20px;display:block}.phone .c span{font-size:12px;color:#8b8578}
.phone .pill{margin-top:auto;background:#5f6b2f;color:#fff;border-radius:999px;text-align:center;padding:10px;font-size:15px}
.u-edit{grid-column:span 4;background:var(--card);padding:28px}.u-edit h3{font-size:42px;line-height:1;margin-bottom:12px}.u-edit p{font-size:15px;line-height:1.55;columns:2;column-gap:18px;color:var(--fg)}
.u-card{grid-column:span 4;background:#171612;color:#f4efe4;padding:28px;display:flex;flex-direction:column;justify-content:space-between}
.u-card .n{font-size:38px;line-height:1}.u-card .r{font-size:14px;opacity:.7}.u-card .row{display:flex;justify-content:space-between;align-items:end;font-size:13px}
.u-label{grid-column:span 5;background:#d8cc98;display:grid;place-items:center;padding:24px;color:#171612}
.jar{width:220px;height:220px;border-radius:50%;background:#f4efe4;border:3px solid #171612;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;box-shadow:0 18px 40px rgba(0,0,0,.15)}
.jar .a{font-size:13px;letter-spacing:.2em;text-transform:uppercase}.jar .b{font-size:44px;line-height:1;margin:6px 0}.jar .c{font-size:12px}
.u-social{grid-column:span 7;background:#5f6b2f;color:#f4efe4;padding:32px;display:flex;flex-direction:column;justify-content:space-between}
.u-social .q{font-size:clamp(30px,3.6vw,52px);line-height:1.05}.u-social .h{display:flex;align-items:center;gap:10px;font-size:14px;opacity:.9}
.langs{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:18px;overflow:hidden}
.langs div{background:var(--bg);padding:12px 14px;display:flex;justify-content:space-between;gap:10px;font-size:14px}.langs .no{color:var(--mute)}.langs em{font-style:normal;font-size:12px;color:var(--mute)}
.langs .ok:after{content:"\2713";color:var(--acc)}
.specs{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:22px}
.tbl{border-top:1px solid var(--line)}.tbl div{display:flex;justify-content:space-between;gap:16px;border-bottom:1px solid var(--line);padding:10px 0;font-size:14px}
.tbl span{color:var(--mute)}.tbl b{font-weight:400;text-align:right;font-variant-numeric:tabular-nums}
.vm{position:relative;height:260px;background:var(--card);border:1px solid var(--line);border-radius:18px;overflow:hidden;margin-bottom:12px}
.vm i{position:absolute;left:0;right:0;border-top:1px dashed var(--line)}.vm i b{position:absolute;left:10px;top:-17px;font:11px PCUI;color:var(--mute);font-style:normal}
.vm i.bl{border-top:1px solid var(--acc)}.vm .s{position:absolute;right:24px;line-height:1}
.files div{display:flex;align-items:center;gap:12px;border-bottom:1px solid var(--line);padding:9px 0;font-size:14px}.files span{flex:1;overflow-wrap:anywhere}.files em{font-style:normal;color:var(--mute);font-size:12px;width:70px;text-align:right}
.qa li{list-style:none;padding:6px 0;border-bottom:1px solid var(--line);font-size:13px}.qa li:before{content:"\2713  ";color:var(--acc)}.qa li.f:before{content:"!  ";color:#b5543c}
.feats div{display:grid;grid-template-columns:70px 1fr auto;gap:12px;align-items:baseline;border-bottom:1px solid var(--line);padding:10px 0}
.feats code{justify-self:start}.feats .ex{font-size:26px;white-space:nowrap}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px}.tabs button{border:1px solid var(--line);background:none;border-radius:999px;padding:7px 14px;cursor:pointer}
.tabs button.on{background:var(--fg);color:var(--bg);border-color:var(--fg)}
.howto{display:grid;grid-template-columns:minmax(260px,1fr) 1.3fr;gap:24px;align-items:start}.howto ol{padding-left:20px;line-height:1.7}
pre{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:16px;overflow:auto;font:13px/1.55 ui-monospace,Menlo,monospace;white-space:pre}
.pw{position:relative}.pw .btn{position:absolute;top:10px;right:10px}
.lic{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:24px;display:flex;gap:20px;align-items:center;flex-wrap:wrap;justify-content:space-between}
footer{border-top:1px solid var(--line);padding:26px 0;color:var(--mute);font-size:13px;display:flex;gap:14px;flex-wrap:wrap;justify-content:space-between;align-items:center}
#lab .sh{align-items:start}.labact{display:flex;gap:8px;flex-wrap:wrap}
.presets{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px}.presets button{border:1px solid var(--line);background:none;border-radius:999px;padding:6px 14px;cursor:pointer}
.presets button:hover{border-color:var(--fg)}.presets button.on{background:var(--fg);color:var(--bg);border-color:var(--fg)}
.labgrid{display:grid;grid-template-columns:300px 1fr;gap:18px;align-items:stretch}
.axes{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:16px 18px;display:flex;flex-direction:column;gap:14px}
.axes label{display:grid;grid-template-columns:1fr auto;gap:4px 10px;font-size:13px;color:var(--mute)}.axes b{color:var(--fg);font-weight:400;font-variant-numeric:tabular-nums}
.axes input{grid-column:1/-1;accent-color:var(--acc);width:100%}.axes small{grid-column:1/-1;font-size:11px;opacity:.75}
.lstage{border:1px solid var(--line);border-radius:var(--r);padding:clamp(22px,4vw,44px);display:flex;flex-direction:column;justify-content:space-between;gap:24px;min-height:420px;overflow:hidden}
#lt{font-family:PCFLEX,sans-serif;font-size:clamp(44px,7vw,104px);line-height:1.02;outline:none;overflow-wrap:anywhere}
.lab2{font-family:PCFLEX,sans-serif;font-size:clamp(18px,2.2vw,28px);line-height:1.3;color:var(--mute)}
#lcss{font:12px/1.5 ui-monospace,Menlo,monospace;color:var(--mute);overflow-wrap:anywhere}
@media(max-width:860px){.labgrid{grid-template-columns:1fr}}
/*MKCSS*/
.toast{position:fixed;bottom:22px;left:50%;transform:translate(-50%,20px);opacity:0;background:var(--fg);color:var(--bg);padding:10px 18px;border-radius:999px;font-size:14px;transition:.2s;pointer-events:none;z-index:50}
.toast.on{opacity:1;transform:translate(-50%,0)}
@media(max-width:980px){.uses{grid-template-columns:1fr 1fr}.uses>*{grid-column:span 1!important;grid-row:auto!important;min-height:300px}.u-poster{grid-column:span 2!important}
 .insp,.howto,.kgrid{grid-template-columns:1fr}header nav{display:none}}
@media(max-width:620px){.uses{grid-template-columns:1fr}.u-poster{grid-column:span 1!important}#t{font-size:56px}header .sub{display:none}}
@media print{header,.bar,.gtools,.tabs,.btn,.big .nav,.big .mode,#install,.toast{display:none!important}body{background:#fff;color:#000}
 section{break-inside:avoid;padding:24px 0}.hero{min-height:360px;-webkit-print-color-adjust:exact;print-color-adjust:exact}.use{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
</style></head><body>
<header><a class="brand" href="#top"><svg viewBox="0 0 32 32">__MARK__</svg><svg viewBox="0 0 __WMW__ 22" style="height:19px;width:auto">__WORD__</svg></a><span class="sub">studio</span>
<nav id="nav"><a href="#tester">Tester</a><a href="#lab" id="navlab">Design lab</a><a href="#glyphs">Glyphs</a><a href="#kerning">Kerning</a><a href="#mockups">In use</a><a href="#languages">Languages</a><a href="#specs">Specs</a><a href="#install">Install</a></nav>
<span class="sp"></span><button class="btn" id="theme" title="Toggle dark mode (D)">Dark</button><button class="btn pri" id="dl">Download family</button></header>
<main id="top">
<div class="hero"><div class="kick" id="kick"></div><h1 class="pc" id="name"></h1><p id="desc"></p><div class="stats" id="stats"></div></div>

<section id="tester"><div class="sh"><div><div class="kicker">Type tester</div><h2>Set anything.</h2><p class="lede">Click the text and type. Every control works live, and the waterfall below follows along.</p></div></div>
<div class="bar" id="bar1"></div><div class="bar" id="bar2"></div>
<div class="stage" id="stage"><div id="t" class="pc" contenteditable spellcheck="false"></div><div id="cmp"><small id="cmpl"></small><div id="cmpt"></div></div></div></section>

<section id="lab"><div class="sh"><div><div class="kicker">Design lab</div><h2>Shape it live.</h2><p class="lede">Every slider is a real axis of a variable font cut from this design, so every setting is still a finished, spaced and kerned font. Find the one you want, then hand the settings back to your AI to cut it as a family.</p></div>
<div class="labact"><button class="btn" id="lreset">Reset</button><button class="btn" id="lrand">Surprise me</button><button class="btn pri" id="lcopy">Copy settings for your AI</button></div></div>
<div class="presets" id="lpre"></div>
<div class="labgrid"><div class="axes" id="laxes"></div><div class="lstage"><div id="lt" contenteditable spellcheck="false">Brand new letters, made to measure.</div><div class="lab2" id="labc">ABCDEFGHIJKLM nopqrstuvwxyz 0123456789 &amp;?!</div><code id="lcss"></code></div></div></section>

<section id="waterfall"><div class="sh"><div><div class="kicker">Waterfall</div><h2>Every size, one rhythm.</h2></div></div><div class="wf pc" id="wf"></div></section>

<section id="weights"><div class="sh"><div><div class="kicker">The family</div><h2 id="wtitle">Weights</h2></div><button class="btn" id="play" style="display:none">Animate weight</button></div><div id="wts"></div></section>

<section id="glyphs"><div class="sh"><div><div class="kicker">Glyph inspector</div><h2 id="gtitle">Glyphs</h2><p class="lede">Pick a glyph to see its outline, every point and handle, and its metrics. Arrow keys step through the set; press / to search.</p></div></div>
<div class="insp"><div class="big" id="big"><div class="mode seg" id="gmode"><button data-m="fill" class="on">Filled</button><button data-m="outline">Outline</button><button data-m="both">Both</button></div>
<div class="nav"><button id="gprev" title="Previous">&larr;</button><button id="gnext" title="Next">&rarr;</button></div><svg id="gsvg"></svg></div><div class="meta" id="meta"></div></div>
<div class="gtools"><input id="gq" placeholder="Search a character, a name or U+0041"><div class="cats" id="cats"></div></div><div class="gl pc" id="gl"></div></section>

<section id="kerning"><div class="sh"><div><div class="kicker">Kerning explorer</div><h2 id="ktitle">Kerning</h2><p class="lede">Type any pair to see how far the foundry moved it. The list shows the pairs that needed the most care.</p></div></div>
<div class="kin"><input id="kp" maxlength="2" value="AV" class="pc"><span class="kval" id="kv"></span><span class="lede" id="kn" style="margin:0"></span></div>
<div class="kgrid"><div class="kbox"><div class="k pc" id="kon"></div><small>Kerned</small></div><div class="kbox"><div class="k pc" id="koff" style="font-kerning:none;font-feature-settings:'kern' 0"></div><small>Without kerning</small></div></div>
<div class="pairs pc" id="pairs"></div></section>



<!--MOCKUPS-->

<section id="languages"><div class="sh"><div><div class="kicker">Language support</div><h2 id="ltitle">Languages</h2><p class="lede">Counted from the font's own character set. A language is supported when every letter it needs is present.</p></div></div><div class="langs" id="langs"></div></section>

<section id="specs"><div class="sh"><div><div class="kicker">Specifications</div><h2>Built like a foundry release.</h2></div><button class="btn" id="print">Print specimen</button></div>
<div class="specs"><div><div class="vm pc" id="vm"></div><div class="tbl" id="tm"></div></div><div><div class="tbl" id="tf"></div><h3 style="margin:26px 0 8px;font-size:18px">OpenType features</h3><div class="feats" id="feats"></div></div>
<div><h3 style="margin-bottom:8px;font-size:18px">Files</h3><div class="files" id="files"></div><h3 style="margin:26px 0 8px;font-size:18px" id="qah">Quality checks</h3><ul class="qa" id="qa"></ul></div></div></section>

<section id="install"><div class="sh"><div><div class="kicker">Install and use</div><h2>Use it everywhere.</h2></div></div>
<div class="tabs" id="itabs"></div><div class="howto" id="ibody"></div>
<div class="lic" style="margin-top:28px"><div><div class="kicker">License</div><b id="lic"></b><p class="lede" id="licp" style="margin-top:4px"></p></div><button class="btn pri" id="dl2">Download family</button></div></section>

<footer><span id="foot"></span><span>Cut with FontWorks</span></footer>
</main><div class="toast" id="toast"></div>
<script>
const D=__DATA__,Z="__ZIP__";
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const el=(t,c,h)=>{const e=document.createElement(t);if(c)e.className=c;if(h!=null)e.innerHTML=h;return e};
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const toast=m=>{const t=$('#toast');t.textContent=m;t.classList.add('on');clearTimeout(toast.h);toast.h=setTimeout(()=>t.classList.remove('on'),1600)};
const copy=(s,m)=>{try{navigator.clipboard.writeText(s).then(()=>toast(m||'Copied'),()=>toast('Select and copy by hand'))}catch(e){toast('Select and copy by hand')}};
const kb=n=>n>1048576?(n/1048576).toFixed(1)+' MB':Math.max(1,Math.round(n/1024))+' KB';
const W=D.weights.map(w=>w[0]),topW=W[W.length-1];
document.documentElement.style.setProperty('--top',topW);
// ---------------------------------------------------------------- hero
$('#kick').textContent=(D.source==='handwriting'?'Handwriting family':'Original typeface')+' · v'+D.version;
$('#name').textContent=D.family;$('#name').style.setProperty('--w',topW);$('#desc').textContent=D.description;
const langsOK=D.languages.filter(l=>l[1]).length;
[[D.glyphs.length,'glyphs'],[D.weights.length,D.weights.length>1?'weights':'weight'],[D.variable?'Variable':'Static','font files'],[D.kern_total.toLocaleString(),'kerning pairs'],[langsOK,'languages'],[D.features.length,'OpenType features']]
 .forEach(([a,b])=>$('#stats').append(el('div','','<b>'+esc(a)+'</b><span>'+esc(b)+'</span>')));
// ---------------------------------------------------------------- tester
const PRESETS={'Pangram':'Sphinx of black quartz, judge my vow.','Headline':'Quick wafting zephyrs vex bold Jim','Paragraph':'Type is the clothing words wear. A good typeface disappears while you read and leaves only the voice of the writer. Spacing is half of that work: the white between letters must feel as even as the black of the strokes.',
 'Alphabet':'ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz','Figures':'0123456789 €$£¥ +−×÷= 25% 3/4 (1,234.50)','Punctuation':'“Quotes,” ‘apostrophes’ — dashes… and (brackets) [ok] {fine}? ¡Sí! ¿Qué?'};
const CW=[['Paper','var(--bg)','var(--fg)'],['Ink','#171612','#f4efe4'],['Meadow','#5f6b2f','#f4efe4'],['Sky','#cdd9dc','#171612'],['Straw','#d8cc98','#171612'],['Clay','#b5543c','#f4efe4']];
const CMP=[['None',''],['Helvetica / Arial','"Helvetica Neue",Helvetica,Arial,sans-serif'],['Georgia','Georgia,serif'],['System UI','system-ui,sans-serif'],['Times','"Times New Roman",Times,serif']];
const st={size:96,w:D.regular,track:0,lh:1.08,f:new Set(),kern:true,align:'left',case:'none',cmp:''};
const t=$('#t');t.textContent=PRESETS.Headline;
function txt(){return t.innerText.replace(/\n+$/,'')||' '}
function apply(){t.style.fontSize=st.size+'px';t.style.setProperty('--w',st.w);t.style.letterSpacing=st.track/1000+'em';t.style.lineHeight=st.lh;t.style.textAlign=st.align;t.style.textTransform=st.case;
 const fs=[...st.f].map(f=>'"'+f+'" 1');if(!st.kern)fs.push('"kern" 0');const ff=fs.join(',')||'normal';t.style.fontFeatureSettings=ff;
 const c=$('#cmp');c.style.display=st.cmp?'block':'none';if(st.cmp){const ct=$('#cmpt');ct.textContent=txt();Object.assign(ct.style,{fontFamily:st.cmp,fontSize:st.size+'px',lineHeight:st.lh,letterSpacing:st.track/1000+'em',textAlign:st.align,textTransform:st.case,fontWeight:st.w>=600?700:400})}
 $$('#wf div').forEach(d=>{d.style.setProperty('--w',st.w);d.lastChild.textContent=txt().replace(/\s+/g,' ');d.style.fontFeatureSettings=ff});
}
function range(bar,label,min,max,step,key,fmt){const l=el('label');const i=el('input');Object.assign(i,{type:'range',min,max,step,value:st[key]});i.id='r-'+key;
 const v=el('b','',fmt(st[key]));i.oninput=()=>{st[key]=+i.value;v.textContent=fmt(st[key]);apply()};l.append(label,i,v);bar.append(l);return i}
const b1=$('#bar1'),b2=$('#bar2');
{const l=el('label','','Text ');const s=el('select');Object.keys(PRESETS).forEach(k=>{const o=el('option','',k);if(k==='Headline')o.selected=true;s.append(o)});s.append(el('option','','Your own'));
 s.onchange=()=>{if(PRESETS[s.value]){t.textContent=PRESETS[s.value];if(s.value==='Paragraph'){st.size=32;$('#r-size').value=32;$('#r-size').nextSibling.textContent='32px';st.lh=1.4;$('#r-lh').value=1.4;$('#r-lh').nextSibling.textContent='1.40'}}else{t.textContent='';t.focus()}apply()};l.append(s);b1.append(l)}
range(b1,'Size',10,260,1,'size',v=>v+'px');
if(D.variable)range(b1,'Weight',D.range[0],D.range[1],1,'w',v=>v);
else{const l=el('label','','Weight ');const s=el('div','seg');D.weights.forEach(([w,n])=>{const b=el('button',w==D.regular?'on':'',n);b.onclick=()=>{st.w=w;$$('.seg.wsel button').forEach(x=>x.classList.remove('on'));b.classList.add('on');apply()};s.append(b)});s.classList.add('wsel');l.append(s);b1.append(l)}
range(b1,'Tracking',-100,250,1,'track',v=>v);range(b1,'Leading',0.8,2,0.01,'lh',v=>(+v).toFixed(2));
{const s=el('div','seg');[['left','Left'],['center','Centre'],['right','Right']].forEach(([a,n])=>{const b=el('button',a==='left'?'on':'',n);b.onclick=()=>{st.align=a;[...s.children].forEach(x=>x.classList.remove('on'));b.classList.add('on');apply()};s.append(b)});b2.append(s)}
{const s=el('div','seg');[['none','Aa'],['uppercase','AA'],['lowercase','aa'],['capitalize','Ab']].forEach(([a,n])=>{const b=el('button',a==='none'?'on':'',n);b.title=a;b.onclick=()=>{st.case=a;[...s.children].forEach(x=>x.classList.remove('on'));b.classList.add('on');apply()};s.append(b)});b2.append(s)}
{const l=el('label','','Colour ');CW.forEach(([n,bg,fg],i)=>{const b=el('button','sw'+(i?'':' on'));b.title=n;b.style.background=bg;b.style.borderColor=fg;b.onclick=()=>{$('#stage').style.setProperty('--sbg',bg);$('#stage').style.setProperty('--sfg',fg);$$('.sw').forEach(x=>x.classList.remove('on'));b.classList.add('on')};l.append(b)});b2.append(l)}
const FN={kern:'Kerning',case:'Case forms',tnum:'Tabular figures',zero:'Slashed zero',ss01:'Alternate a',liga:'Ligatures',onum:'Oldstyle figures',smcp:'Small caps'};
{const k=el('span','tog on','Kerning');k.onclick=()=>{st.kern=!st.kern;k.classList.toggle('on');apply()};b2.append(k)}
D.features.filter(f=>f!=='kern'&&FN[f]).forEach(f=>{const b=el('span','tog',FN[f]);b.onclick=()=>{st.f.has(f)?st.f.delete(f):st.f.add(f);b.classList.toggle('on');apply()};b2.append(b)});
{const l=el('label','','Compare ');const s=el('select');CMP.forEach(([n,v])=>{const o=el('option','',n);o.value=v;s.append(o)});s.onchange=()=>{st.cmp=s.value;$('#cmpl').textContent=s.value?'Same text in '+s.options[s.selectedIndex].text:'';apply()};l.append(s);b2.append(l)}
t.addEventListener('input',()=>{apply()});
[120,96,72,56,42,32,24,18,15,13,11].forEach(s=>{const d=el('div','');d.append(el('span','',s+'px'));d.append(document.createTextNode(''));d.style.fontSize=s+'px';$('#wf').append(d)});
// ---------------------------------------------------------------- weights
$('#wtitle').textContent=D.variable?'One variable font, '+D.range[0]+' to '+D.range[1]:D.weights.length+(D.weights.length>1?' weights':' weight');
D.weights.forEach(([w,n])=>{const r=el('div','wt');r.append(el('span','',n+' · '+w));const g=el('div','pc','Hamburgefonstiv 0123');g.style.setProperty('--w',w);r.append(g);$('#wts').append(r)});
if(D.variable){const p=$('#play');p.style.display='';let on=false,t0=0;function step(ts){if(!on)return;if(!t0)t0=ts;const k=(Math.sin((ts-t0)/900)+1)/2,w=Math.round(D.range[0]+k*(D.range[1]-D.range[0]));
 $$('#wts .pc').forEach(g=>g.style.setProperty('--w',w));$$('#wts span').forEach(s=>s.textContent='wght '+w);requestAnimationFrame(step)}
 p.onclick=()=>{on=!on;p.textContent=on?'Stop':'Animate weight';if(on){t0=0;requestAnimationFrame(step)}else{$$('#wts .wt').forEach((r,i)=>{r.querySelector('.pc').style.setProperty('--w',D.weights[i][0]);r.querySelector('span').textContent=D.weights[i][1]+' · '+D.weights[i][0]})}}}
// ---------------------------------------------------------------- glyphs
const M=D.metrics,G=D.glyphs,CATS=[['all','All'],['upper','Uppercase'],['lower','Lowercase'],['figures','Figures'],['punctuation','Punctuation'],['symbols','Symbols'],['accented','Accented'],['letters','Other letters']];
$('#gtitle').textContent=G.length+' glyphs, every one drawn';
let gcat='all',gq='',gsel=G.findIndex(g=>g[0]==='g');if(gsel<0)gsel=0;let gmode='fill',gw=String(D.regular in D.shapes?D.regular:Object.keys(D.shapes)[0]);
CATS.forEach(([k,n])=>{const c=G.filter(g=>k==='all'||g[4]===k).length;if(!c)return;const b=el('button',k==='all'?'on':'',n+'<i>'+c+'</i>');b.onclick=()=>{gcat=k;$$('#cats button').forEach(x=>x.classList.remove('on'));b.classList.add('on');grid()};$('#cats').append(b)});
function vis(){const q=gq.trim().toLowerCase();return G.map((g,i)=>i).filter(i=>{const g=G[i];if(gcat!=='all'&&g[4]!==gcat)return false;if(!q)return true;
 return g[0]===gq.trim()||g[1].toLowerCase()===q||g[1].toLowerCase()==='u+'+q.replace(/^u\+?/,'')||g[2].toLowerCase().includes(q)||g[5].toLowerCase()===q})}
function grid(){const gl=$('#gl');gl.innerHTML='';const v=vis();if(!v.length){gl.append(el('div','empty','No glyph matches.'));return}
 const fr=document.createDocumentFragment();v.forEach(i=>{const c=el('div',i===gsel?'sel':'',esc(G[i][0]));c.title=G[i][1]+' '+G[i][2];c.onclick=()=>show(i);fr.append(c)});gl.append(fr)}
$('#gq').addEventListener('input',e=>{gq=e.target.value;grid()});
$$('#gmode button').forEach(b=>b.onclick=()=>{gmode=b.dataset.m;$$('#gmode button').forEach(x=>x.classList.remove('on'));b.classList.add('on');show(gsel)});
function show(i){gsel=i;const g=G[i],sh=(D.shapes[gw]||{})[g[5]],adv=g[3];
 $$('#gl div').forEach(d=>d.classList.toggle('sel',d.textContent===g[0]));
 const top=Math.max(M.asc,M.win[0]*.92),bot=Math.min(M.desc,-M.win[1]*.92),pad=(top-bot)*.16,x0=Math.min(-pad,(g[6]?g[6][0]:0)-pad),x1=Math.max(adv+pad,(g[6]?g[6][2]:adv)+pad);
 const H=top-bot+2*pad,Wd=x1-x0,box=$('#big').getBoundingClientRect(),ar=box.width/box.height;let vw=Wd,vh=H;if(vw/vh<ar)vw=vh*ar;else vh=vw/ar;
 const vx=x0-(vw-Wd)/2,vy=-(top+pad)-(vh-H)/2,u=vh/box.height;
 const css=getComputedStyle(document.documentElement),fg=css.getPropertyValue('--fg'),mu=css.getPropertyValue('--mute'),ln=css.getPropertyValue('--line'),ac=css.getPropertyValue('--acc');
 let s='';[['Ascender',M.asc],['Cap height',M.cap],['x-height',M.xh],['Baseline',0],['Descender',M.desc]].forEach(([n,v])=>{s+=`<line x1="${vx}" x2="${vx+vw}" y1="${-v}" y2="${-v}" stroke="${v===0?ac:ln}" stroke-width="${u*(v===0?1.5:1)}" ${v===0?'':`stroke-dasharray="${u*4} ${u*4}"`}/><text x="${vx+u*14}" y="${-v-u*6}" text-anchor="start" font-size="${u*11}" fill="${mu}" font-family="PCUI">${n} ${v}</text>`});
 s+=`<rect x="0" y="${-top-pad*.5}" width="${adv}" height="${top-bot+pad}" fill="none" stroke="${ln}" stroke-width="${u}"/><text x="${adv/2}" y="${-bot+pad*.45}" text-anchor="middle" font-size="${u*11}" fill="${mu}" font-family="PCUI">${adv}</text>`;
 if(sh){const d=sh[0];if(gmode!=='outline')s+=`<path d="${d}" transform="scale(1,-1)" fill="${fg}" fill-opacity="${gmode==='both'?.12:1}"/>`;
  if(gmode!=='fill'){s+=`<path d="${d}" transform="scale(1,-1)" fill="none" stroke="${fg}" stroke-width="${u*1.4}"/>`;const P=sh[1];let h='',dots='';
   for(let k=0;k<P.length;k++){const p=P[k];if(p[2]===0){const a=P[k-1],b=P[k+1];if(a&&a[2])h+=`M${a[0]} ${-a[1]}L${p[0]} ${-p[1]}`;if(b&&b[2]===1)h+=`M${b[0]} ${-b[1]}L${p[0]} ${-p[1]}`;
     dots+=`<circle cx="${p[0]}" cy="${-p[1]}" r="${u*3.2}" fill="var(--bg)" stroke="${ac}" stroke-width="${u*1.2}"/>`}
    else dots+=p[2]===2?`<rect x="${p[0]-u*4.5}" y="${-p[1]-u*4.5}" width="${u*9}" height="${u*9}" fill="${ac}"/>`:`<circle cx="${p[0]}" cy="${-p[1]}" r="${u*3.6}" fill="${fg}"/>`}
   s+=`<path d="${h}" stroke="${ac}" stroke-width="${u}" fill="none"/>`+dots}}
 const svg=$('#gsvg');svg.setAttribute('viewBox',`${vx} ${vy} ${vw} ${vh}`);svg.innerHTML=s;
 const b=g[6],nP=sh?sh[1].length:0,nC=sh?sh[1].filter(p=>p[2]===2).length:0;
 const rows=[['Unicode',g[1]],['Glyph name',g[5]],['Category',g[4]],['Advance width',adv],['Left sidebearing',b?b[0]:'–'],['Right sidebearing',b?adv-b[2]:'–'],['Width × height',b?(b[2]-b[0])+' × '+(b[3]-b[1]):'–'],['Contours · points',nC+' · '+nP]];
 const ws=Object.keys(D.shapes);
 $('#meta').innerHTML=`<div class="ch pc" style="--w:${gw}">${esc(g[0])}</div><div class="nm">${esc(g[2])}</div><dl>${rows.map(([a,v])=>`<div><dt>${a}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl>
 <div class="acts">${ws.length>1?'<span class="seg" id="gws">'+ws.map(w=>`<button data-w="${w}" class="${w===gw?'on':''}">${esc((D.weights.find(x=>String(x[0])===w)||[0,w])[1])}</button>`).join('')+'</span>':''}<button class="btn sm" id="cc">Copy character</button><button class="btn sm" id="cs">Copy SVG</button></div>`;
 $('#cc').onclick=()=>copy(g[0],'Copied '+g[0]);
 $('#cs').onclick=()=>{if(!sh)return;const bb=g[6]||[0,0,adv,M.asc];copy(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 ${-M.asc} ${adv} ${M.asc-M.desc}"><path transform="scale(1,-1)" d="${sh[0]}"/></svg>`,'SVG copied')};
 $$('#gws button').forEach(x=>x.onclick=()=>{gw=x.dataset.w;show(gsel)})}
function stepG(d){const v=vis();if(!v.length)return;let k=v.indexOf(gsel);k=(k+d+v.length)%v.length;show(v[k]);const c=$$('#gl div')[k];if(c)c.scrollIntoView({block:'nearest'})}
$('#gprev').onclick=()=>stepG(-1);$('#gnext').onclick=()=>stepG(1);
document.addEventListener('keydown',e=>{const tag=(e.target.tagName||'').toLowerCase();if(tag==='input'||tag==='textarea'||e.target.isContentEditable)return;
 if(e.key==='/'){e.preventDefault();$('#gq').focus();location.hash='glyphs'}else if(e.key==='ArrowRight'||e.key==='ArrowLeft'){const r=$('#glyphs').getBoundingClientRect();if(r.top<innerHeight&&r.bottom>0){e.preventDefault();stepG(e.key==='ArrowRight'?1:-1)}}
 else if(e.key==='d'||e.key==='D')$('#theme').click()});
// ---------------------------------------------------------------- kerning
const KM=Object.fromEntries(D.kern);$('#ktitle').textContent=D.kern_total.toLocaleString()+' pairs, set by shape';
function kern(){const p=$('#kp').value||'AV';$('#kon').textContent=p;$('#koff').textContent=p;const v=KM[p];$('#kv').textContent=v?(v>0?'+':'')+v+' units':'0';$('#kn').textContent=v?(v<0?'pulled together':'pushed apart'):'no adjustment needed'}
$('#kp').addEventListener('input',kern);
D.kern.slice(0,60).forEach(([p,v])=>{const b=el('button','',esc(p)+'<em>'+v+'</em>');b.onclick=()=>{$('#kp').value=p;kern()};$('#pairs').append(b)});
// ---------------------------------------------------------------- in use

// ---------------------------------------------------------------- languages
$('#ltitle').textContent=langsOK+' of '+D.languages.length+' Latin languages';
D.languages.slice().sort((a,b)=>b[1]-a[1]).forEach(([n,ok,miss])=>$('#langs').append(el('div',ok?'ok':'no',esc(n)+(ok?'':'<em>needs '+esc(miss)+'</em>'))));
// ---------------------------------------------------------------- specs
{const vm=$('#vm'),h=260,span=(M.asc-M.desc)*1.3,px=h/span,base=h-(-M.desc*1.15)*px;
 [['Ascender',M.asc],['Cap height',M.cap],['x-height',M.xh],['Baseline',0,'bl'],['Descender',M.desc]].forEach(([n,v,c])=>{const i=el('i',c||'','<b>'+n+' · '+v+'</b>');i.style.top=(base-v*px)+'px';vm.append(i)});
 const s=el('div','s','Hg');s.style.fontSize=(M.upm*px)+'px';s.style.lineHeight=((M.asc-M.desc)/M.upm);s.style.top=(base-M.asc*px)+'px';s.style.setProperty('--w',D.regular);vm.append(s)}
const tb=(id,rows)=>$(id).innerHTML=rows.map(([a,b])=>`<div><span>${a}</span><b>${esc(b)}</b></div>`).join('');
tb('#tm',[['Units per em',M.upm],['Ascender / descender',M.asc+' / '+M.desc],['Cap height',M.cap],['x-height',M.xh],['Line gap',M.gap],['Win ascent / descent',M.win[0]+' / '+M.win[1]]]);
tb('#tf',[['Family',D.family],['Version',D.version],['Designer',D.designer||'–'],['Weights',D.weights.map(w=>w[1]).join(', ')],['Format',D.variable?'Variable (wght '+D.range[0]+'–'+D.range[1]+') + static':'Static'],['Glyphs',M.glyphs],['Kerning pairs',D.kern_total.toLocaleString()],['Source',D.source==='handwriting'?'Handwriting photo':'Preset: '+D.source],['Made with',D.tool]]);
const FD={kern:['Kerning','AV To'],case:['Case-sensitive forms','(H-I)'],tnum:['Tabular figures','1111'],zero:['Slashed zero','0'],ss01:['Stylistic set 1','a'],liga:['Ligatures','fi fl']};
D.features.forEach(f=>{const d=FD[f]||[f,''];const r=el('div','');r.append(el('code','',f),el('span','',d[0]));const ex=el('span','ex pc',esc(d[1]));if(f!=='kern')ex.style.fontFeatureSettings='"'+f+'" 1';r.append(ex);$('#feats').append(r)});
D.files.forEach(([p,n])=>{const r=el('div','');r.append(el('span','',esc(p)),el('em','',kb(n)));const b=el('button','btn sm','Download');b.onclick=()=>one(p);r.append(b);$('#files').append(r)});
$('#qah').textContent='Quality checks · '+(D.qa||'');(D.qa_lines.length?D.qa_lines:[['Passes OpenType Sanitizer',1],['Vertical metrics cover every glyph',1],['Every glyph point-compatible across masters',1]]).forEach(([s,ok])=>$('#qa').append(el('li',ok?'':'f',esc(s))));
$('#print').onclick=()=>{try{window.print()}catch(e){toast('Printing is not available here')}};
// ---------------------------------------------------------------- install
const fam=D.family,id=D.id,vf=D.variable;
const cssRules=vf?`@font-face {\n  font-family: "${fam}";\n  src: url("webfonts/${id}[wght].woff2") format("woff2");\n  font-weight: ${D.range[0]} ${D.range[1]};\n  font-display: swap;\n}`:D.weights.map(([w,n])=>`@font-face {\n  font-family: "${fam}";\n  src: url("webfonts/${id}-${n}.woff2") format("woff2");\n  font-weight: ${w};\n  font-display: swap;\n}`).join('\n\n');
const IN=[['Mac',`<ol><li>Download the family and unzip it.</li><li>Open the <code>otf</code> folder and double-click each file.</li><li>Click <b>Install</b> in Font Book. ${esc(fam)} now shows in every app.</li></ol>`,''],
 ['Windows',`<ol><li>Download the family and unzip it.</li><li>Open the <code>ttf</code> folder, select every file.</li><li>Right-click and choose <b>Install for all users</b>.</li></ol>`,''],
 ['Linux',`<ol><li>Unzip the family.</li><li>Copy the <code>ttf</code> files to <code>~/.local/share/fonts</code>.</li><li>Run the command to refresh the cache.</li></ol>`,`mkdir -p ~/.local/share/fonts\ncp ${id}/ttf/*.ttf ~/.local/share/fonts/\nfc-cache -f`],
 ['Website',`<ol><li>Copy the <code>webfonts</code> folder to your site.</li><li>Add these rules to your CSS.</li><li>Set <code>font-family</code> where you want it.</li></ol>`,cssRules+`\n\nbody { font-family: "${fam}", system-ui, sans-serif; }`],
 ['Tailwind',`<ol><li>Add the @font-face rules from the Website tab to your global CSS.</li><li>Register the family in your Tailwind theme.</li><li>Use the class <code>font-display</code>.</li></ol>`,`/* Tailwind v4: in your CSS */\n@theme {\n  --font-display: "${fam}", system-ui, sans-serif;\n}\n\n/* Tailwind v3: tailwind.config.js */\ntheme: { extend: { fontFamily: {\n  display: ['"${fam}"', 'system-ui', 'sans-serif'],\n} } }`],
 ['Next.js',`<ol><li>Put the <code>webfonts</code> folder in <code>app/fonts</code>.</li><li>Load it with <code>next/font/local</code>.</li><li>Apply the class to your layout.</li></ol>`,vf?`import localFont from "next/font/local";\n\nexport const display = localFont({\n  src: "./fonts/${id}[wght].woff2",\n  weight: "${D.range[0]} ${D.range[1]}",\n  variable: "--font-display",\n});`:`import localFont from "next/font/local";\n\nexport const display = localFont({\n  src: [\n${D.weights.map(([w,n])=>`    { path: "./fonts/${id}-${n}.woff2", weight: "${w}" },`).join('\n')}\n  ],\n  variable: "--font-display",\n});`],
 ['Figma',`<ol><li>Install the fonts on your computer (Mac or Windows tab).</li><li>Install the Figma desktop app or the font helper for the browser.</li><li>Restart Figma. ${esc(fam)} appears in the font list. Teams on an org plan can upload it as a shared font.</li></ol>`,''],
 ['Canva',`<ol><li>Open <b>Brand Kit</b> (Canva Pro, Teams or Education).</li><li>Under <b>Brand fonts</b>, click <b>Upload a font</b>.</li><li>Choose the <code>otf</code> or <code>ttf</code> files. Only upload fonts you have the rights to; this one is yours.</li></ol>`,''],
 ['Word & Docs',`<ol><li><b>Word, Pages, Keynote:</b> install on your computer and it appears in the font menu.</li><li><b>Google Docs</b> cannot load your own font files; export from Word or use the web route for Google Sites.</li></ol>`,'']];
function itab(k){$$('#itabs button').forEach((b,i)=>b.classList.toggle('on',i===k));const [n,h,c]=IN[k];$('#ibody').innerHTML='<div>'+h+'</div>'+(c?'<div class="pw"><pre>'+esc(c)+'</pre><button class="btn sm">Copy</button></div>':'<div></div>');
 const cb=$('#ibody .pw .btn');if(cb)cb.onclick=()=>copy(c)}
IN.forEach(([n],i)=>{const b=el('button','',n);b.onclick=()=>itab(i);$('#itabs').append(b)});itab(navigator.platform&&/Win/.test(navigator.platform)?1:0);
$('#lic').textContent=D.license;$('#licp').innerHTML=/Open Font License/i.test(D.license)?'Free to use, embed, modify and share, including in commercial work. Do not sell the font files on their own.':/rights reserved/i.test(D.license)?'Yours. You decide who may use it.':'See README.md in the download for the full terms.';
$('#foot').textContent=D.family+' v'+D.version+(D.designer?' · '+D.designer:'')+' · '+D.license+' · '+D.tool;
// ---------------------------------------------------------------- downloads
function bytes(){const b=atob(Z),a=new Uint8Array(b.length);for(let i=0;i<b.length;i++)a[i]=b.charCodeAt(i);return a}
function save(blob,name){try{const u=URL.createObjectURL(blob);const l=el('a');l.href=u;l.download=name;document.body.append(l);l.click();l.remove();setTimeout(()=>URL.revokeObjectURL(u),4000);toast('Downloading '+name)}catch(e){toast('Downloads are blocked here. Open the file in a browser.')}}
function family(){window.pcTrack&&pcTrack('studio_download');save(new Blob([bytes()],{type:'application/zip'}),D.id+'.zip')}
async function one(path){const a=bytes(),v=new DataView(a.buffer);let e=a.length-22;while(e>0&&v.getUint32(e,true)!==0x06054b50)e--;
 const n=v.getUint16(e+10,true);let p=v.getUint32(e+16,true);const want=D.id+'/'+path;
 for(let i=0;i<n;i++){const meth=v.getUint16(p+10,true),cs=v.getUint32(p+20,true),nl=v.getUint16(p+28,true),xl=v.getUint16(p+30,true),cl=v.getUint16(p+32,true),off=v.getUint32(p+42,true);
  const name=new TextDecoder().decode(a.subarray(p+46,p+46+nl));
  if(name===want){const ln=v.getUint16(off+26,true),lx=v.getUint16(off+28,true),data=a.subarray(off+30+ln+lx,off+30+ln+lx+cs);let out=data;
   if(meth===8){if(!window.DecompressionStream){toast('Use Download family in this browser');return}out=new Uint8Array(await new Response(new Blob([data]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).arrayBuffer())}
   save(new Blob([out]),path.split('/').pop());return}
  p+=46+nl+xl+cl}toast('File not found')}
$('#dl').onclick=family;$('#dl2').onclick=family;
// ---------------------------------------------------------------- design lab
if(!D.flex){$('#lab').remove();$('#navlab').remove()}else{
 const AX=D.flex.axes,HELP={wght:'Stem thickness',wdth:'Letter width and spacing',YTLC:'Height of the lowercase',YOPQ:'Horizontal strokes, relative to stems',
  SQAR:'Round curves to squarish ones',SOFT:'Radius of every corner',APRT:'How open c e s a are',slnt:'Lean, in degrees'};
 const lv={};if(D.flex.remix){$('#lab .lede').textContent='Every slider is a real axis of '+D.flex.base_name+', the open-source font this family is remixed from. Find the setting you want, then hand it back to your AI to cut it as a family.'}const defs=()=>AX.forEach(a=>lv[a[0]]=a[3]);defs();
 const clamp=(t,v)=>{const a=AX.find(x=>x[0]===t);return a?Math.min(a[4],Math.max(a[2],v)):v};
 function lapply(){const fv=AX.map(a=>`'${a[0]}' ${Math.round(lv[a[0]])}`).join(', ');['#lt','#labc'].forEach(q=>$(q).style.fontVariationSettings=fv);
  $('#lcss').textContent=`font-family: "${D.family} Flex"; font-variation-settings: ${fv};`;
  AX.forEach(a=>{const i=$('#ax-'+a[0]);if(i){i.value=lv[a[0]];i.nextSibling&&0;$('#axv-'+a[0]).textContent=Math.round(lv[a[0]])}})}
 AX.forEach(a=>{const [tag,name,mn,df,mx]=a;const l=el('label');const i=el('input');Object.assign(i,{type:'range',min:mn,max:mx,step:1,value:df});i.id='ax-'+tag;
  const v=el('b','',df);v.id='axv-'+tag;i.oninput=()=>{lv[tag]=+i.value;$$('#lpre button').forEach(b=>b.classList.remove('on'));lapply()};
  l.append(name,v,i,el('small','',HELP[tag]||''));$('#laxes').append(l)});
 const Y=(AX.find(a=>a[0]==='YTLC')||[0,0,0,500])[3];
 const LP={'Text':{wght:420,YTLC:Y+30,APRT:60,wdth:102},'Display':{wght:760,YTLC:Y-30,wdth:92,YOPQ:78},'Condensed':{wght:620,wdth:75},'Wide':{wght:520,wdth:122,YTLC:Y+10},
  'Soft':{wght:640,SOFT:100,SQAR:8},'Technical':{wght:520,SQAR:92,SOFT:4,APRT:8},'Hairline':{wght:300,YOPQ:62,wdth:108},'Leaning':{slnt:-10,wght:560}};
 Object.keys(LP).forEach(k=>{const b=el('button','',k);b.onclick=()=>{defs();Object.entries(LP[k]).forEach(([t,v])=>{if(AX.some(a=>a[0]===t))lv[t]=clamp(t,v)});$$('#lpre button').forEach(x=>x.classList.toggle('on',x===b));lapply()};$('#lpre').append(b)});
 $('#lreset').onclick=()=>{defs();$$('#lpre button').forEach(b=>b.classList.remove('on'));lapply()};
 $('#lrand').onclick=()=>{AX.forEach(([t,,mn,df,mx])=>{const r=Math.random(),k=t==='slnt'?(r<.7?0:mn*Math.random()):df+(r-.5)*(mx-mn)*.8;lv[t]=clamp(t,k)});$$('#lpre button').forEach(b=>b.classList.remove('on'));lapply()};
 $('#lcopy').onclick=()=>{window.pcTrack&&pcTrack('lab_copy',{remix:!!D.flex.remix});if(D.flex.remix){const ax={};AX.forEach(([t,,,df])=>{if(t!=='wght'&&Math.round(lv[t])!==Math.round(df))ax[t]=Math.round(lv[t])});
  return copy(`Cut a new version of ${D.family} with FontWorks (remix of ${D.flex.base_name}) using these axis settings from the Design lab:\n\n"remix": {"axes": ${JSON.stringify(ax)}}\n\nMerge them into the existing remix axes, keep everything else the same and build the full family.`,'Settings copied. Paste them to your AI.')}
 const b=D.flex.base,sf=D.flex.stemf;const f=w=>{const ks=Object.keys(sf).map(Number).sort((x,y)=>x-y);for(let i=0;i<ks.length-1;i++)if(w>=ks[i]&&w<=ks[i+1])return sf[ks[i]]+(sf[ks[i+1]]-sf[ks[i]])*(w-ks[i])/(ks[i+1]-ks[i]);return w<ks[0]?sf[ks[0]]:sf[ks[ks.length-1]]};
  const g=t=>lv[t]===undefined?null:lv[t];const d={};
  if(g('wght')!==null)d.stem=Math.round(b.stem*f(g('wght')));if(g('wdth')!==null)d.width=+(b.width*g('wdth')/100).toFixed(3);if(g('YTLC')!==null)d.xh=Math.round(g('YTLC'));
  if(g('YOPQ')!==null)d.hratio=+(g('YOPQ')/100).toFixed(3);if(g('SQAR')!==null)d.roundness=+(0.5523+0.2277*g('SQAR')/100).toFixed(4);
  if(g('SOFT')!==null)d.soften=+(0.01+0.31*g('SOFT')/100).toFixed(3);if(g('APRT')!==null)d.aperture=+(g('APRT')/100).toFixed(2);if(g('slnt')!==null&&g('slnt')!==0)d.slant=-Math.round(g('slnt'));
  copy(`Cut a new version of ${D.family} with FontWorks using these design settings from the Design lab:\n\n"design": ${JSON.stringify(d,null,1)}\n\nKeep everything else the same and build the full family.`,'Settings copied. Paste them to your AI.')};
 lapply()}
//MKJS
// ---------------------------------------------------------------- theme, nav
const isDark=()=>{const t=document.documentElement.dataset.theme;return t?t==='dark':matchMedia('(prefers-color-scheme: dark)').matches};
const setTheme=t=>{document.documentElement.dataset.theme=t;$('#theme').textContent=t==='dark'?'Light':'Dark';try{localStorage.setItem('pc-theme',t)}catch(e){}show(gsel)};
$('#theme').onclick=()=>setTheme(isDark()?'light':'dark');
try{const t=localStorage.getItem('pc-theme');if(t)document.documentElement.dataset.theme=t}catch(e){}$('#theme').textContent=isDark()?'Light':'Dark';
const secs=['tester','lab','glyphs','kerning','mockups','languages','specs','install'];
addEventListener('scroll',()=>{let cur='';secs.forEach(s=>{const r=document.getElementById(s).getBoundingClientRect();if(r.top<140)cur=s});$$('#nav a').forEach(a=>a.classList.toggle('on',a.getAttribute('href')==='#'+cur))},{passive:true});
apply();grid();kern();document.fonts.ready.then(()=>show(gsel));addEventListener('resize',()=>show(gsel));
</script></body></html>
"""
