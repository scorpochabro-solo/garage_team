#!/usr/bin/env python3
"""Preview of design variants and perks for the owner: every card of a manifest is a full copy of the site built from
its own git ref under <out>/v/<key>/, closed to search engines and marked with a «← все варианты» badge;
<out>/v/index.html lists the cards in groups. The same layout as the GitHub Pages previews (docs/v/ on main).

    python3 tools/preview_variants.py _preview/manifest.json              # build every card, write the index
    python3 tools/preview_variants.py _preview/manifest.json --only pogoda,stena
    python3 tools/preview_variants.py _preview/manifest.json --index-only # only rewrite v/index.html
    python3 -m http.server 5182 --directory _preview                       # http://localhost:5182/v/

A card is built in a temporary `git worktree` of its ref, so the working copy is never touched. For GitHub Pages set
"base": "/garage_team/v" in the manifest and --out to the docs folder of a main checkout.
Thumbnails are <out>/v/thumbs/<key>.webp, 960×600 (tools/preview_thumbs.cjs makes them with Playwright).

Manifest:
{
  "base": "/v",                         # URL of the index; a card lives at <base>/<key>/
  "title": "…", "lead": "…", "notes": ["…"], "foot": ["…"],
  "groups": [{"id": "plushki", "eyebrow": "// 01 — …", "title": "…", "lead": "…",
              "cards": [{"key": "pogoda", "ref": "perk/pogoda", "num": "// Н1", "title": "…", "text": "…",
                         "try": "…", "open": "#pogoda", "open_label": "К блоку", "base_card": false,
                         "tag": "в сайте", "tag_on": true}]}]
}
"open" is the page and anchor inside the copy ("" = its home page, "services/sinomontaz.html#shiny").
"""
import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BADGE_STYLE = (
    '<style>.vbadge{position:fixed;left:12px;bottom:12px;z-index:250;display:inline-flex;align-items:center;gap:.5em;'
    'padding:.55em .9em;border:1px solid rgba(255,255,255,.18);background:rgba(9,10,9,.88);color:#f3f4f4;'
    'font:500 12px/1.2 "JetBrains Mono",ui-monospace,Menlo,monospace;letter-spacing:.04em;text-decoration:none;'
    'border-radius:4px}.vbadge b{color:#1fc463;font-weight:500}.vbadge:hover{border-color:#1fc463}'
    '@media (max-width:640px){.vbadge{bottom:calc(80px + env(safe-area-inset-bottom));left:8px;font-size:11px;'
    'padding:.45em .7em}.vbadge__all{display:none}}.is-menu-open .vbadge{display:none}</style>')
KEY = re.compile(r"^[a-z0-9-]+$")


def esc(text):
    return html.escape(str(text), quote=True)


def load(path):
    try:
        man = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"манифест {path}: {exc}")
    keys = set()
    for g in man.get("groups", []):
        for c in g.get("cards", []):
            for field in ("key", "ref", "title", "text"):
                if not c.get(field):
                    raise SystemExit(f"манифест: у карточки {c.get('key', '?')} нет поля «{field}»")
            if not KEY.match(c["key"]) or c["key"] in keys or c["key"] in ("thumbs", "index.html"):
                raise SystemExit(f"манифест: плохой или повторный ключ «{c['key']}»")
            keys.add(c["key"])
    if not keys:
        raise SystemExit("манифест: нет ни одной карточки")
    man.setdefault("base", "/v")
    man["base"] = "/" + man["base"].strip("/")
    return man


def git(*args, cwd=ROOT):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def build_card(card, base, out_v):
    """Build the card's ref into out_v/<key> from a throwaway worktree, then mark every page as a preview."""
    key, ref = card["key"], card["ref"]
    sha = git("rev-parse", "--verify", f"{ref}^{{commit}}")
    dest = out_v / key
    tmp = Path(tempfile.mkdtemp(prefix=f"preview-{key}-"))
    wt = tmp / "wt"
    try:
        git("worktree", "add", "--detach", str(wt), sha)
        run = subprocess.run([sys.executable, "build.py", "--base", f"{base}/{key}", "--out", str(dest)],
                             cwd=wt, capture_output=True, text=True)
        if run.returncode:
            raise SystemExit(f"{key}: сборка {ref} упала\n{run.stdout[-2000:]}\n{run.stderr[-2000:]}")
        print(f"{key:>10}  {ref} {sha[:7]}  {run.stdout.strip().splitlines()[-1].split('|')[-1].strip()}")
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=ROOT, capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)
    mark(dest, base, card["title"])
    return sha


def mark(dest, base, title):
    """noindex + the badge back to the index on every page; no robots.txt / sitemap.xml in a copy."""
    for name in ("robots.txt", "sitemap.xml"):
        (dest / name).unlink(missing_ok=True)
    badge = (f'<a class="vbadge" href="{base}/">← <span class="vbadge__all">все варианты · </span>'
             f'<b>{esc(title)}</b></a>')
    n = 0
    for page in dest.rglob("*.html"):
        text = page.read_text(encoding="utf-8")
        if "</head>" not in text or "</body>" not in text:
            continue
        text = text.replace("</head>", f'<meta name="robots" content="noindex, nofollow">{BADGE_STYLE}</head>', 1)
        head, body_end, tail = text.rpartition("</body>")
        text = head + badge + body_end + tail
        page.write_text(text, encoding="utf-8")
        n += 1
    if not n:
        raise SystemExit(f"{dest}: не нашлось ни одной страницы")


def make_thumbs(folder):
    """Screenshots (<key>.png from tools/preview_thumbs.cjs) -> <key>.webp, 960×600, cropped from the top."""
    folder.mkdir(parents=True, exist_ok=True)
    pngs = list(folder.glob("*.png"))
    if pngs:
        from PIL import Image   # the build needs Pillow anyway
        for png in pngs:
            with Image.open(png) as im:
                im = im.convert("RGB")
                scale = max(960 / im.width, 600 / im.height)
                im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS).crop((0, 0, 960, 600))
                im.save(png.with_suffix(".webp"), "WEBP", quality=80, method=6)
            png.unlink()
    return {p.stem for p in folder.glob("*.webp")}


def card_html(card, base, thumbs):
    key = card["key"]
    href = f"{key}/{card.get('open', '')}"
    thumb = (f'<a class="shot" href="{esc(href)}" aria-hidden="true" tabindex="-1"><img src="thumbs/{esc(key)}.webp" '
             f'alt="" width="960" height="600" loading="lazy"></a>') if key in thumbs else ""
    tryit = f'<p class="try"><b>Что попробовать</b>{esc(card["try"])}</p>' if card.get("try") else ""
    more = f'<a class="btn" href="{esc(key)}/">С начала</a>' if card.get("open") else ""
    cls = "card card--base" if card.get("base_card") else "card"
    # «в сайте» / «не выбрано»: what became of a card shown earlier (tag_on: true = it is in the site now)
    tag = (f'<span class="tag{" tag--on" if card.get("tag_on") else ""}">{esc(card["tag"])}</span>'
           if card.get("tag") else "")
    return f"""  <article class="{cls}" id="card-{esc(key)}">
    {thumb}
    <div class="body">
      <span class="num">{esc(card.get("num", ""))}{tag}</span>
      <h2>{esc(card["title"])}</h2>
      <p>{esc(card["text"])}</p>
      {tryit}
      <div class="actions"><a class="btn btn--primary" href="{esc(href)}">{esc(card.get("open_label", "Открыть"))}</a>{more}</div>
    </div>
  </article>"""


def index_html(man, thumbs, fonts_from):
    base = man["base"]
    faces = ""
    if fonts_from:
        faces = "".join(
            f'@font-face{{font-family:"{fam}";font-weight:{w};font-display:swap;src:url("{base}/{fonts_from}/assets/fonts/{f}-{s}.woff2") format("woff2");'
            f'unicode-range:{"U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116" if s == "cyrillic" else "U+0000-00FF, U+2000-206F"};}}\n'
            for fam, f, w in (("Unbounded", "unbounded", "200 900"), ("Manrope", "manrope", "200 800"), ("JetBrains Mono", "jetbrains-mono", "100 800"))
            for s in ("cyrillic", "latin"))
    notes = "".join(f"<li>{esc(n)}</li>" for n in man.get("notes", []))
    groups = []
    for g in man["groups"]:
        cards = "\n".join(card_html(c, base, thumbs) for c in g["cards"])
        groups.append(f"""<section class="wrap part" id="{esc(g['id'])}" aria-labelledby="part-{esc(g['id'])}">
  <p class="eyebrow part__eyebrow">{esc(g.get('eyebrow', ''))}</p>
  <h2 class="part__title" id="part-{esc(g['id'])}">{esc(g['title'])}</h2>
  <p class="lead">{esc(g.get('lead', ''))}</p>
</section>
<div class="wrap grid">
{cards}
</div>""")
    foot = "".join(f"<p>{esc(p)}</p>" for p in man.get("foot", []))
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex, nofollow">
<title>{esc(man.get('title', 'Варианты для сайта · Гараж'))}</title>
<style>
{faces}:root {{ color-scheme: dark; --bg: #0c0d0c; --card: #121412; --line: rgba(255,255,255,.10); --line-2: rgba(255,255,255,.18);
  --text: #f3f4f4; --text-2: #b8bdb8; --text-3: #7c827c; --green: #00963d; --green-bright: #1fc463; --brick: #b5553a; --lamp: #ffcf8a;
  --gutter: clamp(16px, .6rem + 2.6vw, 56px); }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--bg); color: var(--text); font: 400 16px/1.6 "Manrope", system-ui, -apple-system, "Segoe UI", sans-serif; -webkit-font-smoothing: antialiased; }}
a {{ color: inherit; }}
.wrap {{ max-width: 1280px; margin: 0 auto; padding: 0 var(--gutter); }}
.head {{ padding: clamp(40px, 7vw, 96px) 0 clamp(28px, 4vw, 48px); border-bottom: 1px solid var(--line); }}
.eyebrow {{ font: 500 12px/1 "JetBrains Mono", ui-monospace, Menlo, monospace; letter-spacing: .14em; text-transform: uppercase; color: var(--green-bright); display: flex; align-items: center; gap: 10px; margin: 0 0 18px; }}
.eyebrow::before {{ content: ""; width: 9px; height: 9px; background: var(--green-bright); }}
h1 {{ font: 800 clamp(30px, 1.2rem + 4vw, 64px)/1.02 "Unbounded", "Manrope", sans-serif; text-transform: uppercase; margin: 0 0 20px; letter-spacing: -.01em; }}
h1 span {{ color: var(--brick); }}
.lead {{ color: var(--text-2); max-width: 760px; margin: 0; font-size: clamp(16px, .95rem + .3vw, 19px); }}
.notes {{ display: flex; flex-wrap: wrap; gap: 8px 10px; margin: 24px 0 0; padding: 0; list-style: none; }}
.notes li {{ font: 500 12px/1.3 "JetBrains Mono", ui-monospace, Menlo, monospace; color: var(--text-2); border: 1px solid var(--line-2); padding: 7px 10px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 380px), 1fr)); gap: 20px; padding: clamp(28px, 4vw, 56px) 0; }}
.card {{ background: var(--card); border: 1px solid var(--line); display: flex; flex-direction: column; scroll-margin-top: 24px; }}
.card--base {{ border-style: dashed; }}
.shot {{ display: block; aspect-ratio: 16 / 10; overflow: hidden; border-bottom: 1px solid var(--line); background: #070807; }}
.shot img {{ display: block; width: 100%; height: 100%; object-fit: cover; transition: transform .6s cubic-bezier(.22, 1, .36, 1); }}
.body {{ padding: 22px 22px 24px; display: flex; flex-direction: column; gap: 12px; flex: 1; }}
.num {{ font: 500 12px/1 "JetBrains Mono", ui-monospace, Menlo, monospace; color: var(--green-bright); letter-spacing: .1em; }}
.tag {{ display: inline-block; margin-left: 12px; padding: 4px 7px; font: 500 11px/1 "JetBrains Mono", ui-monospace, Menlo, monospace; letter-spacing: .08em; text-transform: uppercase; color: var(--text-3); border: 1px solid var(--line-2); vertical-align: 1px; }}
.tag--on {{ color: var(--green-bright); border-color: rgba(31, 196, 99, .45); }}
h2 {{ font: 800 22px/1.15 "Unbounded", "Manrope", sans-serif; margin: 0; text-transform: uppercase; }}
.body p {{ margin: 0; color: var(--text-2); font-size: 15px; }}
.try {{ color: var(--text); font-size: 14px; border-left: 2px solid var(--lamp); padding-left: 12px; }}
.try b {{ color: var(--lamp); font: 500 11px/1 "JetBrains Mono", ui-monospace, Menlo, monospace; letter-spacing: .1em; text-transform: uppercase; display: block; margin-bottom: 6px; }}
.actions {{ margin-top: auto; padding-top: 6px; display: flex; flex-wrap: wrap; gap: 10px; }}
.btn {{ display: inline-flex; align-items: center; justify-content: center; min-height: 44px; padding: 0 18px; font: 600 14px/1 "Manrope", sans-serif; text-decoration: none; border: 1px solid var(--line-2); }}
.btn--primary {{ background: var(--green); border-color: var(--green); color: #fff; }}
.btn:focus-visible {{ outline: 2px solid var(--green-bright); outline-offset: 3px; }}
.part {{ padding-top: clamp(28px, 4vw, 56px); border-top: 1px solid var(--line); }}
.part__eyebrow {{ margin: 0 0 12px; }}
.part h2.part__title {{ font-size: clamp(24px, 1rem + 2vw, 40px); margin: 0 0 12px; }}
.part .lead {{ font-size: 16px; }}
.foot {{ border-top: 1px solid var(--line); padding: 28px 0 48px; color: var(--text-3); font-size: 14px; }}
.foot p {{ margin: 0 0 8px; max-width: 820px; }}
@media (hover: hover) and (pointer: fine) {{ .card:hover .shot img {{ transform: scale(1.03); }} .btn:hover {{ border-color: var(--green-bright); }} .btn--primary:hover {{ background: #0c6e34; }} }}
@media (prefers-reduced-motion: reduce) {{ .shot img {{ transition: none; }} }}
</style>
</head>
<body>
<header class="head">
  <div class="wrap">
    <p class="eyebrow">{esc(man.get('eyebrow', 'garage.team · черновики'))}</p>
    <h1>{man.get('h1_html', 'Варианты <span>для сайта</span> «Гаража»')}</h1>
    <p class="lead">{esc(man.get('lead', ''))}</p>
    <ul class="notes">{notes}</ul>
  </div>
</header>
{chr(10).join(groups)}
<footer class="foot"><div class="wrap">{foot}</div></footer>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("manifest")
    ap.add_argument("--out", default=str(ROOT / "_preview"))
    ap.add_argument("--only", default="", help="ключи через запятую")
    ap.add_argument("--index-only", action="store_true")
    args = ap.parse_args()
    man = load(args.manifest)
    out_v = Path(args.out).resolve() / "v"
    out_v.mkdir(parents=True, exist_ok=True)
    cards = [c for g in man["groups"] for c in g["cards"]]
    only = {k for k in args.only.split(",") if k}
    unknown = only - {c["key"] for c in cards}
    if unknown:
        raise SystemExit(f"нет таких карточек: {', '.join(sorted(unknown))}")
    if not args.index_only:
        for card in cards:
            if not only or card["key"] in only:
                build_card(card, man["base"], out_v)
    thumbs = make_thumbs(out_v / "thumbs")
    fonts_from = next((c["key"] for c in cards if (out_v / c["key"] / "assets" / "fonts").is_dir()), "")
    (out_v / "index.html").write_text(index_html(man, thumbs, fonts_from), encoding="utf-8")
    root_index = out_v.parent / "index.html"
    if not root_index.exists():   # a local preview root; in a docs/ folder index.html is the site itself
        root_index.write_text(f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={man["base"]}/">'
                              f'<a href="{man["base"]}/">Все варианты</a>', encoding="utf-8")
    missing = [c["key"] for c in cards if c["key"] not in thumbs]
    print(f"index: {out_v / 'index.html'}  ({len(cards)} cards{', no thumbnail: ' + ', '.join(missing) if missing else ''})")


if __name__ == "__main__":
    main()
