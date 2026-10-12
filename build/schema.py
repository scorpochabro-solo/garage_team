# -*- coding: utf-8 -*-
"""schema.org structured data shared by the home page and the service pages."""
from __future__ import annotations

import json
import re

from . import data as D

ORG_ID = D.SITE_URL + "/#autorepair"
SHOP_ID = D.SITE_URL + "/avtozapchasti/#store"
CITY = "Нижний Новгород"
PHONE = "+7 831 416-16-77"
_DAYS = {"Понедельник – пятница": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
         "Суббота": ["Saturday"], "Воскресенье": ["Sunday"]}
_RANGE = re.compile(r"(\d{1,2}:\d{2})\s*[–-]\s*(\d{1,2}:\d{2})")


def _opening_hours(hours: list[tuple[str, str]]) -> list[dict]:
    """D.HOURS / D.SHOP_HOURS as schema.org specs; a day without a time range («по предварительной записи») is left out."""
    specs = []
    for label, value in hours:
        if label not in _DAYS:
            raise ValueError(f"неизвестные дни в часах работы: {label!r}")
        m = _RANGE.search(value)
        if m:
            opens, closes = (t.zfill(5) for t in m.groups())
            specs.append({"@type": "OpeningHoursSpecification", "dayOfWeek": _DAYS[label], "opens": opens, "closes": closes})
    return specs


def _address() -> dict:
    return {"@type": "PostalAddress", "streetAddress": "ул. Красная слобода, 9", "addressLocality": CITY,
            "postalCode": "603155", "addressCountry": "RU"}


def org() -> dict:
    """The full AutoRepair entity (home page)."""
    lat, lon = D.COORDS
    return {
        "@type": "AutoRepair",
        "@id": ORG_ID,
        "name": "Автосервис «Гараж»",
        "alternateName": ["Автотехцентр «Гараж»", "Garage Team"],
        "url": D.SITE_URL + "/",
        "telephone": PHONE,
        "email": D.EMAIL,
        "image": D.SITE_URL + "/assets/img/misc/advantages-bg.webp",
        "logo": D.SITE_URL + "/assets/logo/logo.svg",
        "address": _address(),
        "geo": {"@type": "GeoCoordinates", "latitude": lat, "longitude": lon},
        "areaServed": {"@type": "City", "name": CITY},
        "openingHoursSpecification": _opening_hours(D.HOURS),
        "sameAs": [D.VK_URL],
        "foundingDate": str(D.FOUNDED),
    }


def org_ref() -> dict:
    """The same entity in short form: enough to be understood on a page that does not repeat the whole card."""
    return {"@type": "AutoRepair", "@id": ORG_ID, "name": "Автосервис «Гараж»", "url": D.SITE_URL + "/",
            "telephone": PHONE, "address": _address()}


def shop() -> dict:
    """The parts shop at the same address: the same company, its own opening hours (the shop page)."""
    lat, lon = D.COORDS
    return {
        "@type": "AutoPartsStore",
        "@id": SHOP_ID,
        "name": "Магазин автозапчастей «Гараж»",
        "url": D.SITE_URL + "/avtozapchasti/",
        "telephone": PHONE,
        "email": D.EMAIL,
        "address": _address(),
        "geo": {"@type": "GeoCoordinates", "latitude": lat, "longitude": lon},
        "areaServed": {"@type": "City", "name": CITY},
        "openingHoursSpecification": _opening_hours(D.SHOP_HOURS),
        "parentOrganization": {"@id": ORG_ID},
    }


def shop_ref() -> dict:
    return {"@type": "AutoPartsStore", "@id": SHOP_ID, "name": "Магазин автозапчастей «Гараж»",
            "url": D.SITE_URL + "/avtozapchasti/", "telephone": PHONE, "address": _address()}


def dump(node: dict | list) -> str:
    """JSON for a <script type="application/ld+json">; "</" is escaped so the text cannot close the script tag."""
    doc = {"@context": "https://schema.org", "@graph": node} if isinstance(node, list) else {"@context": "https://schema.org", **node}
    return json.dumps(doc, ensure_ascii=False).replace("</", "<\\/")


def breadcrumbs(items: list[tuple[str, str | None]], page_url: str) -> dict:
    """items: [(name, path or None for the current page)] as rendered in the page's breadcrumbs."""
    elements = []
    for pos, (name, path) in enumerate(items, 1):
        url = D.SITE_URL + path if path else page_url
        elements.append({"@type": "ListItem", "position": pos, "name": name, "item": url})
    return {"@type": "BreadcrumbList", "itemListElement": elements}


def service(name: str, service_type: str, description: str, page_url: str, low_price: int | None,
            provider: dict | None = None) -> dict:
    node = {
        "@type": "Service",
        "@id": page_url + "#service",
        "name": name,
        "serviceType": service_type,
        "description": description,
        "url": page_url,
        "areaServed": {"@type": "City", "name": CITY},
        "provider": provider or org_ref(),
    }
    if low_price:
        node["offers"] = {"@type": "AggregateOffer", "priceCurrency": "RUB", "lowPrice": low_price,
                          "availability": "https://schema.org/InStock", "url": page_url}
    return node


def faq(items: list[tuple[str, str]]) -> dict:
    """items: [(question, answer as plain text)]"""
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items]}
