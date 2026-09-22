# -*- coding: utf-8 -*-
"""Illustrative service photos through the kie.ai market API (GPT Image 2.5).

    python3 tools/kie_images.py --balance            # remaining credits
    python3 tools/kie_images.py --dry-run            # print the final prompts, call nothing
    python3 tools/kie_images.py --only sinomontaz    # one or several slugs
    python3 tools/kie_images.py                      # every item of data/service_photos.json without a file yet

The key comes from the KIE_API_KEY environment variable or from .env in the project root (git-ignored).
Task ids are kept in tools/.kie_tasks.json: an interrupted run continues polling instead of paying for the image twice.
Results are saved as JPEG to src/assets/img/photo/<slug>.jpg; build.py turns them into WebP.
"""
from __future__ import annotations

import argparse
import http.client
import io
import json
import logging
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
JOBS_FILE = ROOT / "data" / "service_photos.json"
STATE_FILE = ROOT / "tools" / ".kie_tasks.json"
OUT_DIR = ROOT / "src" / "assets" / "img" / "photo"

API = "https://api.kie.ai"
MODELS = {
    "sunburst": "gpt-image-2-5-sunburst-text-to-image",  # premium quality
    "flare": "gpt-image-2-5-flare-text-to-image",        # faster, default tier on kie.ai
}
POLL_SECONDS = 6
JOB_TIMEOUT_SECONDS = 9 * 60
HTTP_TIMEOUT_SECONDS = 40
GET_ATTEMPTS = 3
DOWNLOAD_ATTEMPTS = 6
RETRY_PAUSE_SECONDS = 3
CHUNK_BYTES = 256 * 1024
MAX_DOWNLOAD_BYTES = 40 * 1024 * 1024
JPEG_QUALITY = 90
MAX_SOURCE_SIDE = 2000  # build.py serves 1600 px at most; keeping 2.5K originals would bloat the repository
ESTIMATED_CREDITS = 10  # measured for sunburst 2K on 2026-09-21, used only for the pre-flight balance check

# One photographic look for the whole set; the scene itself comes from service_photos.json.
STYLE = (
    "Photorealistic documentary photograph taken in a real working car repair shop, shot on a full-frame mirrorless camera "
    "with a 35mm lens at f/2.8, available light plus workshop lamps, natural white balance, restrained slightly desaturated colour, "
    "fine sensor grain, realistic depth of field. True-to-life materials: dust, fingerprints, oil stains, scratched tools, worn paint, "
    "nothing staged, glossy or symmetrical. Correct mechanical detail and correct human hands. "
    "No text, no lettering, no numbers, no logos, no brand badges, no licence plates, no signage, no watermark. "
    "Not an illustration, not a 3D render, not an advertisement."
)

log = logging.getLogger("kie")


class KieError(RuntimeError):
    """The API answered, but refused the request or the task failed."""


def load_key() -> str:
    key = os.environ.get("KIE_API_KEY", "").strip()
    env_file = ROOT / ".env"
    if not key and env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            name, _, value = line.partition("=")
            if name.strip() == "KIE_API_KEY":
                key = value.strip().strip("'\"")
    if not key:
        raise SystemExit("KIE_API_KEY не найден: задайте переменную окружения или строку KIE_API_KEY=... в .env")
    return key


def _ssl_context() -> ssl.SSLContext:
    """python.org builds on macOS ship without a CA bundle; certifi fixes that. Verification is never switched off."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


SSL_CONTEXT = _ssl_context()


def api(key: str, method: str, path: str, payload: dict | None = None, params: dict | None = None) -> dict:
    url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    # Only reads are retried: a POST that timed out may still have created (and billed) a task.
    attempts = GET_ATTEMPTS if method == "GET" else 1
    for attempt in range(1, attempts + 1):
        req = urllib.request.Request(url, data=body, method=method, headers={
            "Authorization": f"Bearer {key}", "Content-Type": "application/json", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SECONDS, context=SSL_CONTEXT) as resp:
                raw = resp.read().decode("utf-8")
            break
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            raise KieError(f"HTTP {exc.code} на {path}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == attempts:
                raise KieError(f"сеть недоступна на {path}: {exc}") from exc
            log.warning("сеть: %s, попытка %d из %d", exc, attempt + 1, attempts)
            time.sleep(RETRY_PAUSE_SECONDS * attempt)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise KieError(f"не JSON в ответе {path}: {raw[:200]}") from exc
    if data.get("code") != 200:
        raise KieError(f"{path}: code={data.get('code')} msg={data.get('msg')}")
    return data


def balance(key: str) -> float:
    return float(api(key, "GET", "/api/v1/chat/credit")["data"])


def load_jobs(only: list[str]) -> list[dict]:
    items = json.loads(JOBS_FILE.read_text(encoding="utf-8"))["items"]
    known = {j["slug"] for j in items}
    unknown = [s for s in only if s not in known]
    if unknown:
        raise SystemExit(f"нет таких slug в {JOBS_FILE.name}: {', '.join(unknown)} (есть: {', '.join(sorted(known))})")
    return [j for j in items if not only or j["slug"] in only]


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        log.warning("файл состояния %s повреждён, начинаю с пустого", STATE_FILE.name)
        return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def full_prompt(job: dict) -> str:
    return f"{job['scene'].strip()} {STYLE}"


def submit(key: str, job: dict, model: str, aspect: str, resolution: str) -> str:
    data = api(key, "POST", "/api/v1/jobs/createTask", {
        "model": model,
        "input": {"prompt": full_prompt(job), "aspect_ratio": aspect, "resolution": resolution, "background": "opaque"},
    })
    task_id = (data.get("data") or {}).get("taskId")
    if not task_id:
        raise KieError(f"createTask не вернул taskId: {data}")
    return task_id


def _read_into(buf: bytearray, url: str) -> None:
    """Append the response body to buf. A non-empty buf is continued with a Range request instead of starting over."""
    headers = {"User-Agent": "garage-2027/kie_images"}
    if buf:
        headers["Range"] = f"bytes={len(buf)}-"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SECONDS, context=SSL_CONTEXT) as resp:
        ctype = resp.headers.get("Content-Type", "")
        if ctype and not ctype.startswith(("image/", "application/octet-stream", "binary/")):
            raise KieError(f"результат не картинка: {ctype}")
        if buf and resp.status != 206:  # the server ignored Range and sends the whole file again
            buf.clear()
        while chunk := resp.read(CHUNK_BYTES):
            buf.extend(chunk)
            if len(buf) > MAX_DOWNLOAD_BYTES:
                raise KieError("результат больше 40 МБ, не сохраняю")


def _decode(raw: bytes) -> Image.Image:
    try:
        Image.open(io.BytesIO(raw)).verify()
        return Image.open(io.BytesIO(raw)).convert("RGB")  # convert() decodes every pixel: a cut-off file fails here
    except Exception as exc:  # Pillow raises several unrelated types for broken files
        raise KieError(f"файл результата не читается как изображение: {exc}") from exc


def fetch_image(url: str) -> Image.Image:
    """Results are ~6 MB PNGs on a slow host that drops long transfers, hence chunked reading with resume."""
    if not url.lower().startswith("https://"):
        raise KieError(f"результат не по https: {url[:80]}")
    buf = bytearray()
    for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
        try:
            _read_into(buf, url)
            return _decode(bytes(buf))
        except http.client.IncompleteRead as exc:
            buf.extend(exc.partial)
            problem = f"соединение оборвалось на {len(buf) // 1024} КБ"
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            problem = f"сеть: {exc} (получено {len(buf) // 1024} КБ)"
        except KieError as exc:
            if "не читается" not in str(exc):
                raise
            buf.clear()  # complete by HTTP rules but broken: download it again from the start
            problem = str(exc)
        if attempt < DOWNLOAD_ATTEMPTS:
            log.warning("%s, попытка %d из %d", problem, attempt + 1, DOWNLOAD_ATTEMPTS)
            time.sleep(RETRY_PAUSE_SECONDS * attempt)
    raise KieError(f"не удалось скачать результат за {DOWNLOAD_ATTEMPTS} попыток: {problem}")


def finish(job: dict, record: dict) -> Path:
    urls = json.loads(record.get("resultJson") or "{}").get("resultUrls") or []
    if not urls:
        raise KieError(f"{job['slug']}: задача успешна, но resultUrls пуст")
    image = fetch_image(urls[0])
    if max(image.size) > MAX_SOURCE_SIDE:
        image.thumbnail((MAX_SOURCE_SIDE, MAX_SOURCE_SIDE), Image.LANCZOS)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dest = OUT_DIR / f"{job['slug']}.jpg"
    image.save(dest, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    log.info("готово %s: %dx%d, %d КБ, списано %s кредитов, %s с", job["slug"], image.width, image.height,
             dest.stat().st_size // 1024, record.get("creditsConsumed", "?"), (record.get("costTime") or 0) // 1000)
    return dest


def run(key: str, jobs: list[dict], model: str, aspect: str, resolution: str, force: bool, credits: float) -> int:
    state = load_state()
    todo = []
    for job in jobs:
        if (OUT_DIR / f"{job['slug']}.jpg").exists() and not force:
            log.info("пропуск %s: файл уже есть (--force чтобы перегенерировать)", job["slug"])
            continue
        if force:
            state.pop(job["slug"], None)
        todo.append(job)

    to_pay = [j for j in todo if j["slug"] not in state]
    estimate = len(to_pay) * ESTIMATED_CREDITS
    if estimate > credits:
        raise KieError(f"нужно примерно {estimate} кредитов на {len(to_pay)} фото, на балансе {credits:.0f}: "
                       "пополните баланс или ограничьте список через --only")
    if to_pay:
        log.info("новых фото: %d, ожидаемый расход около %d кредитов", len(to_pay), estimate)

    for job in todo:
        slug = job["slug"]
        if slug in state:
            log.info("продолжаю ждать %s -> %s", slug, state[slug]["taskId"])
            continue
        state[slug] = {"taskId": submit(key, job, model, aspect, resolution), "model": model, "submitted": int(time.time())}
        save_state(state)
        log.info("отправлено %s -> %s", slug, state[slug]["taskId"])

    # 1) wait for generation; downloads come later so that a slow transfer does not eat the waiting time of other tasks
    pending = {j["slug"]: j for j in todo}
    ready: dict[str, dict] = {}
    failed = 0
    deadline = time.time() + JOB_TIMEOUT_SECONDS
    while pending and time.time() < deadline:
        time.sleep(POLL_SECONDS)
        for slug in list(pending):
            try:
                record = api(key, "GET", "/api/v1/jobs/recordInfo", params={"taskId": state[slug]["taskId"]})["data"]
            except KieError as exc:
                log.warning("опрос %s: %s", slug, exc)
                continue
            status = record.get("state")
            if status == "success":
                ready[slug] = record
                del pending[slug]
            elif status == "fail":
                log.error("%s: генерация не удалась: %s %s", slug, record.get("failCode"), record.get("failMsg"))
                failed += 1
                state.pop(slug, None)
                save_state(state)
                del pending[slug]
    for slug in pending:
        log.error("%s: не дождался за %d с, taskId сохранён, запустите скрипт ещё раз", slug, JOB_TIMEOUT_SECONDS)

    # 2) download; a paid task leaves the state file only after its image is safely on disk
    by_slug = {j["slug"]: j for j in todo}
    for slug, record in ready.items():
        try:
            finish(by_slug[slug], record)
        except KieError as exc:
            log.error("%s: %s. taskId сохранён, повторный запуск докачает результат без новой оплаты", slug, exc)
            failed += 1
            continue
        state.pop(slug, None)
        save_state(state)
    return failed + len(pending)


def main() -> int:
    ap = argparse.ArgumentParser(description="Сгенерировать фото услуг через kie.ai")
    ap.add_argument("--only", nargs="+", default=[], metavar="SLUG", help="только эти slug из data/service_photos.json")
    ap.add_argument("--model", choices=sorted(MODELS), default="sunburst")
    ap.add_argument("--aspect", default="3:2")
    ap.add_argument("--resolution", choices=["1K", "2K", "4K"], default="2K")
    ap.add_argument("--force", action="store_true", help="перегенерировать, даже если файл уже есть")
    ap.add_argument("--dry-run", action="store_true", help="показать итоговые промты и ничего не вызывать")
    ap.add_argument("--balance", action="store_true", help="показать остаток кредитов и выйти")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")

    jobs = load_jobs(args.only)
    if args.dry_run:
        for job in jobs:
            log.info("[%s] %s\n%s\n", job["slug"], job["page"], full_prompt(job))
        return 0

    key = load_key()
    try:
        before = balance(key)
        log.info("баланс: %.2f кредитов", before)
        if args.balance:
            return 0
        problems = run(key, jobs, MODELS[args.model], args.aspect, args.resolution, args.force, before)
    except KieError as exc:
        log.error("%s", exc)
        return 1
    try:
        after = balance(key)
        log.info("баланс: %.2f кредитов, потрачено за запуск %.2f", after, before - after)
    except KieError as exc:
        log.warning("итоговый баланс не получен: %s", exc)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
