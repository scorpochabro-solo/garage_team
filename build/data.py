# -*- coding: utf-8 -*-
"""Site data: loads JSON extracted from garage.team plus shared constants and helpers."""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SRC = ROOT / "src"
DIST = ROOT / "dist"

SITE = json.loads((DATA / "site.json").read_text(encoding="utf-8"))
_SERVICES = json.loads((DATA / "services.json").read_text(encoding="utf-8"))
DESCR = json.loads((DATA / "descriptions.json").read_text(encoding="utf-8"))
HOTSPOTS = json.loads((DATA / "hotspots.json").read_text(encoding="utf-8"))["items"]

CATEGORIES = _SERVICES["categories"]
SERVICES = _SERVICES["services"]
BY_PATH = {s["path"]: s for s in SERVICES}
CAT_BY_HREF = {c["href"]: c for c in CATEGORIES}

# ---------- constants (verbatim from the current site) ----------
BRAND = "Гараж"
SITE_URL = "https://garage.team"
PHONE = "(831) 416-16-77"
PHONE_CODE = "(831)"
PHONE_NUM = "416-16-77"
PHONE_TEL = "+78314161677"
EMAIL = "info@garage.team"
ADDRESS_SHORT = "Н. Новгород, ул. Красная слобода, 9"
ADDRESS_FULL = "603155, г. Нижний Новгород, ул. Красная слобода, 9"
HOURS = [("Понедельник – пятница", "9:00 – 19:00"), ("Суббота", "9:00 – 17:00")]
SHOP_HOURS = [("Понедельник – пятница", "10:00 – 19:00"), ("Суббота", "10:00 – 17:00"), ("Воскресенье", "по предварительной записи")]
VK_URL = "https://vk.com/garagebest"
FB_URL = ("https://www.facebook.com/%D0%90%D0%B2%D1%82%D0%BE%D1%81%D0%B5%D1%80%D0%B2%D0%B8%D1%81-%D0%B3%D0%B0%D1%80%D0%B0%D0%B6-"
          "wwwgarageteam-1811807572418855/?ref=bookmarks")
COORDS = (56.328949, 44.027199)
FOUNDED = 2011
COPYRIGHT_FROM = 2011
COMPANY = "ООО «Гараж»"
COMPANY_LINE_2 = "Сеть магазинов запчастей «Гараж»"
META_KEYWORDS = "Гараж - поиск и подбор запчастей, автозапчасти, запчасти для иномарок, каталог запчастей, магазин запчастей"

NAV = [
    ("Услуги", "/services.html"),
    ("Автозапчасти", "/avtozapchasti/"),
    ("Оплата", "/oplata.html"),
    ("О компании", "/about/"),
    ("Контакты", "/contacts/"),
]
FOOTER_LINKS = [
    ("Все услуги", "/services.html"),
    ("Автозапчасти", "/avtozapchasti/"),
    ("Каталоги запчастей", "/cats/"),
    ("Поиск по номеру", "/search/"),
    ("Доставка", "/delivery.html"),
    ("Оплата", "/oplata.html"),
    ("О компании", "/about/"),
    ("Отзывы", "/otzyvy.html"),
    ("Контакты", "/contacts/"),
    ("Оставить заявку", "/call/request/"),
    ("Звонок менеджеру", "/call/manager/"),
    ("Регистрация", "/registration/"),
    ("Пользовательское соглашение", "/page/soglashenie/"),
]


def esc(s):
    return html.escape(str(s), quote=True)


# ---------- base path (GitHub Pages project sites live under /<repo>/) ----------
BASE = ""
_ROOT_LINK = re.compile(r'(href|src|action|content)="/(?!/)')
_ROOT_URL = re.compile(r"url\('/(?!/)")


def set_base(base):
    global BASE
    BASE = (base or "").rstrip("/")


def rebase(text):
    """Prefix every root-relative URL (/assets/…, /services/…, /call/…) with BASE. No-op when BASE is empty."""
    if not BASE:
        return text
    text = _ROOT_LINK.sub(lambda m: f'{m.group(1)}="{BASE}/', text)
    text = _ROOT_URL.sub(f"url('{BASE}/", text)
    text = text.replace("location.href = '/'", f"location.href = '{BASE}/'")
    return text


# ---------- image url mapping (original url -> dist url) ----------
def img(url):
    """Map an original garage.team image path to its optimized asset path in dist."""
    if not url:
        return ""
    u = url
    if u.startswith("/data/images/"):
        u = "/assets/img/" + u[len("/data/images/"):]
    elif u.startswith("/img/example/brands/"):
        u = "/assets/img/brands/" + u[len("/img/example/brands/"):]
    elif u.startswith("/img/example/"):
        u = "/assets/img/misc/" + u[len("/img/example/"):]
    elif u.startswith("/img/content/"):
        u = "/assets/img/misc/content-" + u[len("/img/content/"):]
    elif u.startswith("/img/v2/"):
        u = "/assets/img/misc/" + u[len("/img/v2/"):]
    elif u.startswith("/img/"):
        u = "/assets/img/misc/" + u[len("/img/"):]
    u = u.replace(" ", "_")
    if re.search(r"\.(jpe?g)$", u, re.I):
        u = re.sub(r"\.(jpe?g)$", ".webp", u, flags=re.I)
    return u


# ---------- price helpers ----------
def parse_amount(cell):
    """'от 1800 рублей' -> (True, 1800); '1500' -> (False, 1500); '' -> None"""
    if not cell:
        return None
    digits = re.sub(r"[^\d]", "", cell)
    if not digits:
        return None
    return ("от" in cell.lower(), int(digits))


def fmt_amount(n):
    return f"{n:,}".replace(",", " ") + " ₽"


def fmt_price(cell):
    p = parse_amount(cell)
    if not p:
        return None
    from_, n = p
    return ("от " if from_ else "") + fmt_amount(n)


def price_from(svc):
    """Lowest 'иномарки' price for a service page or, for a category, among its sub-pages."""
    candidates = [svc]
    if not svc.get("price_rows"):
        cat = CAT_BY_HREF.get(svc["path"])
        if cat:
            candidates = [BY_PATH[s["href"]] for s in cat["subs"] if s["href"] in BY_PATH]
    best = None
    for s in candidates:
        for row in s.get("price_rows") or []:
            if len(row) > 1:
                p = parse_amount(row[1])
                if p and (best is None or p[1] < best):
                    best = p[1]
    return best


def category_of(svc):
    if svc["path"] in CAT_BY_HREF:
        return CAT_BY_HREF[svc["path"]]
    return CAT_BY_HREF.get(svc.get("category_href"))


def description_for(svc):
    """Original description text if the page had one, otherwise the neutral text from descriptions.json."""
    original = svc.get("description_html") or ""
    if original:
        return original, False
    return DESCR.get(svc["path"], ""), True


def strip_tags(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def slug_of(path):
    return re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-")


def year_now():
    import datetime
    return datetime.date.today().year


def total_service_pages():
    return len(SERVICES)
