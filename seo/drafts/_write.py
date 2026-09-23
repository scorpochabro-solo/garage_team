"""Helper for authoring content files: python3 seo/drafts/<file>.py writes data/content/<slug>.json.

write() checks the file with the same rules as the build (build/content.py) BEFORE saving and saves atomically,
so a half-written or invalid file never lands in data/content/ and never breaks the build for others.
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from build.content import ContentError, slug_of_path, validate  # noqa: E402

_SERVICES = json.loads((ROOT / "data" / "services.json").read_text(encoding="utf-8"))["services"]
_KNOWN = {s["path"] for s in _SERVICES}
_TEAM = {t["name"] for t in json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8")).get("team", [])}
_SLUGS = {slug_of_path(p) for p in _KNOWN}


def a(path: str, text: str) -> str:
    if path.startswith("/services/") and path not in _KNOWN:
        raise ContentError(f"ссылка на несуществующую страницу: {path}")
    return f'<a href="{path}">{text}</a>'


def p(*paras: str) -> str:
    return "".join(f"<p>{x}</p>" for x in paras)


def ul(*items: str) -> str:
    return "<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>"


def write(slug: str, content: dict) -> None:
    if slug not in _SLUGS:
        raise ContentError(f"нет страницы услуги со slug {slug!r}")
    validate(content, f"{slug}.json", _KNOWN, _TEAM)
    out = ROOT / "data" / "content" / f"{slug}.json"
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, out)
    print("written", out.name)
