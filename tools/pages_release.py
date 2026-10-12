"""Stage the approved site and refresh legacy preview links without changing Git refs."""
import argparse
import html
import json
from pathlib import Path
import shutil

from preview_variants import index_html, load


ROOT = Path(__file__).resolve().parents[1]


def stage(source: Path, docs: Path):
    if not (source / "index.html").is_file() or not docs.is_dir():
        raise ValueError("Expected a built site and an existing docs checkout")
    manifest = load(ROOT / "tools/pages_previews.json")
    cards = {c["key"]: c for g in manifest["groups"] for c in g["cards"]}
    base = manifest["base"].removesuffix("/v")
    old_pages = list((docs / "v").rglob("*.html"))
    for path in docs.rglob("*"):
        relative = path.relative_to(docs)
        if path.is_file() and relative.parts[0] != "v" and not (source / relative).is_file():
            path.unlink()
    shutil.copytree(source, docs, dirs_exist_ok=True)
    for page in old_pages:
        relative = page.relative_to(docs / "v")
        if len(relative.parts) < 2:
            continue
        key, *rest = relative.parts
        suffix = Path(*rest)
        if key not in cards:
            target = base + "/v/"
        elif str(suffix) == "index.html":
            target = base + "/" + cards[key].get("open", "")
        elif (docs / suffix).is_file():
            target = base + "/" + suffix.as_posix()
            if suffix.name == "index.html":
                target = target.removesuffix("index.html")
        else:
            target = base + "/404.html"
        escaped = html.escape(target, quote=True)
        page.write_text('<!doctype html><html lang="ru"><meta charset="utf-8">'
                        '<meta name="robots" content="noindex">'
                        '<title>Актуальная версия · Гараж</title>'
                        f'<meta http-equiv="refresh" content="0; url={escaped}">'
                        f'<a href="{escaped}">Открыть актуальную версию</a>'
                        f'<script>location.replace({json.dumps(target)});</script></html>', encoding="utf-8")
    (docs / "v/index.html").write_text(index_html(manifest, set(), "base"), encoding="utf-8")
    (docs / "release.json").write_text(json.dumps({"edition": "2026-10-12", "source": "photos",
                                                    "features": len(cards) - 1}, indent=2) + "\n")
    print(f"Staged site, {len(cards)} showcase links, {len(old_pages) - 1} legacy links")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("docs", type=Path)
    args = parser.parse_args()
    stage(args.source.resolve(), args.docs.resolve())
