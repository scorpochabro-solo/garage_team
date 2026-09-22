# -*- coding: utf-8 -*-
"""SVG icon set (24x24, stroke-based) rendered as one inline sprite per page."""

_S = 'fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"'

ICONS = {
    # ---------- service / category icons ----------
    "diag": f'<g {_S}><rect x="3" y="5" width="18" height="12" rx="1.5"/><path d="M2 20h20"/><path d="M6.5 11h2l1.5-3 2 6 1.5-3h4"/></g>',
    "engine": f'<g {_S}><path d="M4 10h2.5l1.5-2h6l1.5 2H20v7h-2.5l-1 2H8l-1.5-2H4z"/><path d="M9 8V5h4v3"/><path d="M4 13H2v2h2"/><path d="M20 12h2"/></g>',
    "suspension": f'<g {_S}><path d="M12 3v2"/><path d="M8 5h8"/><path d="M8 7l8 2-8 2 8 2-8 2 8 2"/><path d="M8 19h8"/><path d="M12 19v2"/></g>',
    "chip": f'<g {_S}><rect x="7" y="7" width="10" height="10" rx="1"/><rect x="10" y="10" width="4" height="4"/><path d="M9 4v3M12 4v3M15 4v3M9 17v3M12 17v3M15 17v3M4 9h3M4 12h3M4 15h3M17 9h3M17 12h3M17 15h3"/></g>',
    "brake": f'<g {_S}><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="3"/><path d="M12 3.5v2M12 18.5v2M3.5 12h2M18.5 12h2"/><path d="M17 5.5a8.5 8.5 0 0 1 2.9 3.9" stroke-width="3"/></g>',
    "cooling": f'<g {_S}><rect x="3" y="6" width="14" height="12" rx="1"/><path d="M6 6v12M9 6v12M12 6v12"/><path d="M19 8v8"/><path d="M17 12h5"/><path d="M20.5 9.5 22 8M20.5 14.5 22 16"/></g>',
    "electric": f'<g {_S}><path d="M13 2 4 14h7l-1 8 9-12h-7z"/></g>',
    "ac": f'<g {_S}><path d="M12 2v20M2 12h20M5 5l14 14M19 5 5 19"/><path d="M12 2l-2 2M12 2l2 2M12 22l-2-2M12 22l2-2M2 12l2-2M2 12l2 2M22 12l-2-2M22 12l-2 2"/></g>',
    "injector": f'<g {_S}><path d="M5 21V5a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v16"/><path d="M3 21h14"/><rect x="8" y="6" width="3" height="4"/><path d="M15 9h2l2 2v7a1.5 1.5 0 0 0 3 0v-6l-2-2"/></g>',
    "diesel": f'<g {_S}><path d="M12 3s-6 6.5-6 11a6 6 0 0 0 12 0c0-4.5-6-11-6-11z"/><path d="M10 12v6M10 12h2.5a3 3 0 0 1 0 6H10"/></g>',
    "exhaust": f'<g {_S}><rect x="3" y="9" width="13" height="7" rx="3.5"/><path d="M16 12.5h3l2-2"/><path d="M19 12.5l2 2"/><path d="M6 12.5h7"/><path d="M8 5v2M11 4v3"/></g>',
    "clutch": f'<g {_S}><circle cx="9" cy="12" r="7"/><circle cx="15" cy="12" r="7"/><circle cx="12" cy="12" r="1.5"/></g>',
    "mkpp": f'<g {_S}><path d="M6 5v14M12 5v14M18 5v14M6 12h12"/><circle cx="6" cy="5" r="2"/><circle cx="12" cy="5" r="2"/><circle cx="18" cy="5" r="2"/><circle cx="6" cy="19" r="2"/><circle cx="12" cy="19" r="2"/><circle cx="18" cy="19" r="2"/></g>',
    "akpp": f'<g {_S}><path d="M12 2.5l2.2 1.3 2.6-.2 1.2 2.3 2.3 1.2-.2 2.6L21.5 12l-1.4 2.2.2 2.6-2.3 1.2-1.2 2.3-2.6-.2L12 21.5l-2.2-1.4-2.6.2-1.2-2.3-2.3-1.2.2-2.6L2.5 12l1.4-2.2-.2-2.6 2.3-1.2 1.2-2.3 2.6.2z"/><circle cx="12" cy="12" r="3.5"/></g>',
    "paint": f'<g {_S}><rect x="3" y="4" width="13" height="6" rx="1.5"/><path d="M16 7h3a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-8v2"/><rect x="9.5" y="14" width="3" height="7" rx="1"/></g>',
    "equipment": f'<g {_S}><path d="M4 7h16M4 12h16M4 17h16"/><circle cx="9" cy="7" r="2" fill="var(--bg,#0a0a0a)"/><circle cx="15" cy="12" r="2" fill="var(--bg,#0a0a0a)"/><circle cx="8" cy="17" r="2" fill="var(--bg,#0a0a0a)"/></g>',
    "polish": f'<g {_S}><path d="M12 3c.6 4.2 4.8 8.4 9 9-4.2.6-8.4 4.8-9 9-.6-4.2-4.8-8.4-9-9 4.2-.6 8.4-4.8 9-9z"/><path d="M5 3l.5 1.5L7 5l-1.5.5L5 7l-.5-1.5L3 5l1.5-.5z"/></g>',
    "body": f'<g {_S}><path d="M3 14l1.5-4.5A2 2 0 0 1 6.4 8h9.2l3.6 4H21a1 1 0 0 1 1 1v3h-2"/><path d="M3 14v2h2"/><circle cx="7.5" cy="16.5" r="2"/><circle cx="17.5" cy="16.5" r="2"/><path d="M9.5 16.5h6"/><path d="M11 8v4h5"/></g>',
    "inspection": f'<g {_S}><rect x="5" y="4" width="14" height="17" rx="1.5"/><path d="M9 4V2.5h6V4"/><path d="M8.5 13l2.5 2.5 4.5-5"/></g>',
    "plastidip": f'<g {_S}><path d="M12 3s-6 6.5-6 11a6 6 0 0 0 12 0c0-4.5-6-11-6-11z"/><circle cx="9.5" cy="14" r="1"/><circle cx="13.5" cy="16.5" r="1.3"/><circle cx="13" cy="11.5" r=".8"/></g>',
    "alignment": f'<g {_S}><rect x="3" y="7" width="4" height="10" rx="1.5"/><rect x="17" y="7" width="4" height="10" rx="1.5"/><path d="M7 12h10"/><path d="M12 9v6"/><path d="M9.5 10.5 12 9l2.5 1.5M9.5 13.5 12 15l2.5-1.5"/></g>',
    "clean": f'<g {_S}><path d="M9 21h6l1-9H8z"/><path d="M10 12V7a2 2 0 0 1 2-2h4"/><path d="M16 3v4"/><circle cx="19" cy="9" r="1.2"/><circle cx="20" cy="13.5" r=".9"/><circle cx="16.5" cy="9.5" r=".7"/></g>',
    "turbo": f'<g {_S}><circle cx="11" cy="13" r="7"/><circle cx="11" cy="13" r="2.5"/><path d="M11 6a7 7 0 0 1 7 7h4"/><path d="M4 13a7 7 0 0 0 7 7"/></g>',
    "tnvd": f'<g {_S}><rect x="6" y="8" width="12" height="10" rx="1.5"/><path d="M9 8V4h6v4"/><path d="M12 11v4M10 13h4"/><path d="M6 13H3M21 13h-3"/><path d="M12 18v3"/></g>',
    "tire": f'<g {_S}><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/><path d="M12 3v2.5M12 18.5V21M3 12h2.5M18.5 12H21M5.6 5.6l1.8 1.8M16.6 16.6l1.8 1.8M18.4 5.6l-1.8 1.8M7.4 16.6l-1.8 1.8"/></g>',
    "parts": f'<g {_S}><path d="M3 8l9-4 9 4-9 4z"/><path d="M3 8v9l9 4 9-4V8"/><path d="M12 12v9"/><path d="M7.5 6l9 4"/></g>',
    "maintenance": f'<g {_S}><path d="M14.5 6.5a3.5 3.5 0 0 0 4 4l2.5 2.5-3 3-2.5-2.5a3.5 3.5 0 0 0-4-4L4 3l3-3"/><path d="M14 11l-9.5 9.5a1.4 1.4 0 0 1-2-2L12 9"/></g>',
    "oil": f'<g {_S}><path d="M12 3s-5.5 6-5.5 10a5.5 5.5 0 0 0 11 0C17.5 9 12 3 12 3z"/><path d="M9.5 14a2.5 2.5 0 0 0 2.5 2.5"/></g>',
    "storage": f'<g {_S}><ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v4c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/><path d="M4 10v4c0 1.7 3.6 3 8 3s8-1.3 8-3v-4"/><path d="M4 14v4c0 1.7 3.6 3 8 3s8-1.3 8-3v-4"/></g>',
    "headlight": f'<g {_S}><path d="M9 6a6 6 0 0 0 0 12h2c1.5 0 2-1 2-2V8c0-1-.5-2-2-2z"/><path d="M15 8h5M15 11h6M15 14h6M15 17h5"/></g>',
    "steering": f'<g {_S}><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="2.5"/><path d="M3.2 11c3-1.3 5.5-1.6 8.8-1.6s5.8.3 8.8 1.6"/><path d="M12 14.5V21M9.8 13.3 5 18M14.2 13.3 19 18"/></g>',
    "glass": f'<g {_S}><path d="M4 16L6.5 7h11L20 16z"/><path d="M2 16h20"/><path d="M8 12.5l5-3"/><path d="M6 20l4-3"/></g>',
    "vinyl": f'<g {_S}><rect x="3" y="7" width="13" height="10" rx="1"/><path d="M16 9h2.5a2.5 2.5 0 0 1 0 5H16"/><path d="M3 11h13M3 14h13" stroke-dasharray="1.5 2"/></g>',
    "climate": f'<g {_S}><path d="M10 14.5V5a2 2 0 1 1 4 0v9.5a3.5 3.5 0 1 1-4 0z"/><path d="M12 9v6"/><path d="M18 5h3M18 8h3"/></g>',
    "spray": f'<g {_S}><path d="M4 9h8l2-3h2l1 2v6l-1 2h-2l-2-3H4z"/><path d="M4 9v4"/><path d="M8 13v6a1 1 0 0 0 2 0v-6"/><path d="M19 6h2M19 9h3M19 12h2"/></g>',
    # ---------- UI icons ----------
    "phone": f'<g {_S}><path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2z"/></g>',
    "mail": f'<g {_S}><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></g>',
    "pin": f'<g {_S}><path d="M12 22s7-6.5 7-12a7 7 0 0 0-14 0c0 5.5 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/></g>',
    "clock": f'<g {_S}><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></g>',
    "user": f'<g {_S}><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></g>',
    "cart": f'<g {_S}><path d="M3 4h2l2.5 11h11L21 7H7"/><circle cx="9" cy="19" r="1.5"/><circle cx="17" cy="19" r="1.5"/></g>',
    "check": f'<g {_S}><path d="M5 12.5l4.5 4.5L19 7.5"/></g>',
    "arrow": f'<g {_S}><path d="M4 12h16M13 5l7 7-7 7"/></g>',
    "arrow-up-right": f'<g {_S}><path d="M7 17L17 7M8 7h9v9"/></g>',
    "arrow-left": f'<g {_S}><path d="M20 12H4M11 5l-7 7 7 7"/></g>',
    "close": f'<g {_S}><path d="M6 6l12 12M18 6L6 18"/></g>',
    "menu": f'<g {_S}><path d="M3 7h18M3 12h18M3 17h18"/></g>',
    "zoom": f'<g {_S}><circle cx="11" cy="11" r="7"/><path d="M16.5 16.5L21 21M8 11h6M11 8v6"/></g>',
    "chevron": f'<g {_S}><path d="M6 9l6 6 6-6"/></g>',
    "chevron-left": f'<g {_S}><path d="M15 6l-6 6 6 6"/></g>',
    "chevron-right": f'<g {_S}><path d="M9 6l6 6-6 6"/></g>',
    "shield": f'<g {_S}><path d="M12 2l8 3v6c0 5-3.5 9-8 11-4.5-2-8-6-8-11V5z"/><path d="M8.5 12l2.5 2.5 4.5-5"/></g>',
    "star": '<path fill="currentColor" d="M12 2.5l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4 6.1 20.5l1.2-6.5L2.5 9.4l6.6-.9z"/>',
    "quote": '<path fill="currentColor" d="M6.5 5C4 5 2 7.2 2 10.2c0 2.6 1.8 4.6 4.3 4.6.3 0 .6 0 .9-.1-.6 1.9-2 3.4-4 4.1l.9 1.7C8.3 19 11 15.3 11 10.7 11 7.4 9.1 5 6.5 5zm11 0C15 5 13 7.2 13 10.2c0 2.6 1.8 4.6 4.3 4.6.3 0 .6 0 .9-.1-.6 1.9-2 3.4-4 4.1l.9 1.7C19.3 19 22 15.3 22 10.7 22 7.4 20.1 5 17.5 5z"/>',
    "plus": f'<g {_S}><path d="M12 5v14M5 12h14"/></g>',
    "minus": f'<g {_S}><path d="M5 12h14"/></g>',
    "search": f'<g {_S}><circle cx="11" cy="11" r="7"/><path d="M16.5 16.5L21 21"/></g>',
    "external": f'<g {_S}><path d="M14 4h6v6M20 4l-9 9"/><path d="M19 13v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h6"/></g>',
    "send": f'<g {_S}><path d="M21 3L10 14"/><path d="M21 3l-7 18-4-7-7-4z"/></g>',
    "info": f'<g {_S}><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8v.5"/></g>',
    "hazard": f'<g {_S}><path d="M12 3l10 18H2z"/><path d="M12 10v4M12 17v.5"/></g>',
    "calendar": f'<g {_S}><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/></g>',
    "ruble": f'<g {_S}><path d="M8 20V4h5.5a4 4 0 0 1 0 8H6"/><path d="M6 16h7"/></g>',
    "vk": '<path fill="currentColor" d="M15.07 2H8.93C3.33 2 2 3.33 2 8.93v6.14C2 20.67 3.33 22 8.93 22h6.14c5.6 0 6.93-1.33 6.93-6.93V8.93C22 3.33 20.67 2 15.07 2zm3.08 14.27h-1.46c-.55 0-.72-.44-1.71-1.43-.87-.83-1.24-.94-1.46-.94-.3 0-.38.08-.38.49v1.31c0 .35-.11.56-1.04.56-1.53 0-3.23-.93-4.42-2.65-1.8-2.52-2.29-4.42-2.29-4.81 0-.21.08-.41.49-.41h1.46c.37 0 .51.17.65.56.72 2.09 1.93 3.92 2.42 3.92.19 0 .27-.08.27-.55V9.87c-.06-1-.58-1.08-.58-1.43 0-.17.14-.34.36-.34h2.29c.31 0 .42.17.42.53v2.94c0 .31.14.42.23.42.19 0 .34-.11.68-.45 1.05-1.18 1.8-2.99 1.8-2.99.1-.21.27-.41.63-.41h1.46c.44 0 .53.23.44.53-.18.85-1.97 3.37-1.97 3.37-.15.25-.21.36 0 .64.15.21.65.64.98 1.03.61.69 1.07 1.27 1.2 1.67.13.4-.08.6-.48.6z"/>',
    "facebook": '<path fill="currentColor" d="M13.5 22v-8h2.7l.4-3.2h-3.1V8.8c0-.9.3-1.6 1.6-1.6h1.7V4.4c-.3 0-1.3-.1-2.5-.1-2.5 0-4.1 1.5-4.1 4.2v2.3H7.4V14h2.8v8z"/>',
    "instagram": f'<g {_S}><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r=".8" fill="currentColor"/></g>',
    "logo-mark": '<path fill="currentColor" d="M4 4h16a2 2 0 0 1 2 2v9l-10 6L2 15V6a2 2 0 0 1 2-2z"/>',
}

# category href fragment -> icon key
CATEGORY_ICONS = {
    "diagnostika": "diag", "remont-dvigatela": "engine", "remont-hodovoj": "suspension", "cip-tuning": "chip",
    "remont-zamena-regulirovka-prokacka-tormozov": "brake", "remont-i-promyvka-sistem-ohlazdenia": "cooling",
    "remont-elektrooborudovania-avtomobila": "electric", "zapravka-i-remont-avtokondicionerov": "ac",
    "remont-promyvka-inzektorov-i-monovpryskov": "injector", "remont-dizela": "diesel",
    "remont-vyhlopnoj-sistemy": "exhaust", "zamena-sceplenia": "clutch", "remont-mkpp-zamena-korobki-peredac": "mkpp",
    "remont-akpp-i-zamena-masla-v-akpp": "akpp", "polnaa-i-lokalnaa-pokraska-avtomobila": "paint",
    "ustanovka-dopolnitelnogo-oborudovania": "equipment", "polirovka-kuzova-avtomobila": "polish",
    "kuzovnoj-remont": "body", "tehosmotr-avto-diagnosticeskaa-karta-dla-osago": "inspection",
    "pokraska-avtomobilej-plasti-dip": "plastidip", "shod-razval-regulirovka-i-diagnostika": "alignment",
    "himcistka-salona": "clean", "remont-turbin-i-turbokompressorov": "turbo", "remont-tnvd": "tnvd",
    "sinomontaz": "tire", "avtozapcasti": "parts", "planovoe-to": "maintenance", "hranenie-sin": "storage",
}


def icon_for_href(href):
    """Return the icon key for a service/category href."""
    slug = href.strip("/").replace("services/", "").split("/")[0].replace(".html", "")
    return CATEGORY_ICONS.get(slug, "maintenance")


def sprite():
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" class="sprite" aria-hidden="true" focusable="false" style="position:absolute;width:0;height:0;overflow:hidden">']
    for name, body in ICONS.items():
        parts.append(f'<symbol id="i-{name}" viewBox="0 0 24 24">{body}</symbol>')
    parts.append('</svg>')
    return "".join(parts)


def icon(name, cls=""):
    if name not in ICONS:
        raise KeyError(f"unknown icon: {name}")
    c = ("ic " + cls).strip()
    return f'<svg class="{c}" aria-hidden="true" focusable="false"><use href="#i-{name}"/></svg>'
