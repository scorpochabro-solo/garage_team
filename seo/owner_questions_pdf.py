#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Анкета владельца в PDF: вопросы с полями для ответов и согласование новых названий страниц из seo/renames.md.

Две версии:
  полная   — все вопросы по каждой странице из seo/owner-questions.md;
  короткая — seo/owner-questions-short.md: общие вопросы один раз, остальное — таблицы с отметками «да / нет».

Поля заполняются в «Просмотре» на Mac, в Adobe Acrobat Reader и других программах для PDF;
распечатанная анкета заполняется ручкой (поля печатаются рамками).

  python3 seo/owner_questions_pdf.py            # -> seo/owner-questions.pdf
  python3 seo/owner_questions_pdf.py --short    # -> seo/owner-questions-short.pdf
  python3 seo/owner_questions_pdf.py -o x.pdf

Таблица в исходнике идёт сразу после вопроса: строка заголовков, строка `|---|`, строки ответов. Ячейки: `( )` — выбор
одного варианта в строке, `[ ]` — отметка, `___` — поле для текста, остальное — текст. Строка, где заполнена только
первая ячейка, — подзаголовок.

Нужны reportlab, fonttools и brotli (pip install reportlab fonttools brotli).
Шрифты — шрифты сайта: вариативные woff2 из src/assets/fonts при запуске превращаются в статичные TTF
нужной жирности, латиница и кириллица склеиваются в один файл. Знаки ₽ и → берутся из PT Mono (есть в macOS),
если его нет — пишутся как «руб.» и «->».
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEO = ROOT / "seo"
FONTS_SRC = ROOT / "src" / "assets" / "fonts"
LOGO = SEO / "assets" / "logo-on-dark.png"
PT_MONO = Path("/System/Library/Fonts/Supplemental/PTMono.ttc")

try:
    from fontTools.merge import Merger
    from fontTools.ttLib import TTFont as FTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import (ArrayObject, BooleanObject, DecodedStreamObject, DictionaryObject, NameObject, NumberObject,
                               TextStringObject)
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Flowable, Frame, KeepTogether, NextPageTemplate,
                                    PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle)
    from reportlab.platypus.tableofcontents import TableOfContents
except ImportError as exc:  # the site build does not need these; only this tool does
    sys.exit(f"нет библиотеки {exc.name}: pip install reportlab fonttools brotli pypdf")

INK = colors.HexColor("#0c0d0c")
GREEN = colors.HexColor("#00963d")
GREEN_BRIGHT = colors.HexColor("#1fc463")
GRAY = colors.HexColor("#6b716b")
GRAY_LIGHT = colors.HexColor("#9aa09a")
LINE = colors.HexColor("#c9cec9")
FIELD_BG = colors.HexColor("#f5f7f5")
PAGE_W, PAGE_H = A4
MARGIN_X, MARGIN_TOP, MARGIN_BOTTOM = 18 * mm, 22 * mm, 18 * mm
ANSWER_H = 38          # pt: two or three typed lines, a comfortable box on paper
NUM_W = 30             # pt: the column with the question number
GRID_FIELD_H = 22      # pt: a comment box in a table row, two typed lines
GRID_MARK = 11         # pt: a checkbox or a radio button in a table row
GENERAL = "Общие вопросы"   # the section of the short version that is asked once for the whole site
CELL_CHOICE, CELL_CHECK, CELL_FIELD = "( )", "[ ]", "___"


# ---------- fonts ----------
def build_fonts(tmp: Path) -> bool:
    """Static TTFs from the site's variable woff2 subsets; returns True when PT Mono (₽, →) is available."""
    def make(family: str, weight: int, name: str) -> None:
        parts = []
        for subset in ("latin", "cyrillic", "cyrillic-ext"):
            src = FONTS_SRC / f"{family}-{subset}.woff2"
            if not src.exists():
                continue
            font = FTFont(src)
            font.flavor = None
            static = instantiateVariableFont(font, {"wght": weight}, updateFontNames=False)
            part = tmp / f"{name}-{subset}.ttf"
            static.save(part)
            parts.append(str(part))
        if not parts:
            sys.exit(f"нет файлов шрифта {family} в {FONTS_SRC}")
        out = tmp / f"{name}.ttf"
        merged = Merger().merge(parts)
        # every instance keeps the variable font's own name («Manrope-ExtraLight»); reportlab embeds fonts by that
        # name, so without a name of its own the bold instance silently turned into the regular one
        for record in merged["name"].names:
            if record.nameID in (4, 6):
                record.string = name
        merged.save(out)
        pdfmetrics.registerFont(TTFont(name, str(out)))

    make("manrope", 400, "Manrope")
    make("manrope", 700, "Manrope-Bold")
    make("unbounded", 800, "Unbounded")
    make("jetbrains-mono", 500, "Mono")
    pdfmetrics.registerFontFamily("Manrope", normal="Manrope", bold="Manrope-Bold", italic="Manrope", boldItalic="Manrope-Bold")
    if PT_MONO.exists():
        pdfmetrics.registerFont(TTFont("PTMono", str(PT_MONO), subfontIndex=1))
        return True
    return False


def add_field_font(writer: "PdfWriter", ttf: Path, size: float = 9) -> None:
    """Typed answers in Russian: the answer boxes get Manrope with a Windows-1251 style encoding instead of Helvetica.

    reportlab can only give form fields the standard PDF fonts, which have no Cyrillic: a reader that draws the typed
    text from the field's font turns «Нет» into garbage. The whole font (Latin + Cyrillic, ~55 KB) is embedded, codes
    128–255 are mapped to Cyrillic glyphs by name, so any reader can draw what the owner types.
    """
    ft = FTFont(str(ttf))
    upem, cmap, hmtx = ft["head"].unitsPerEm, ft.getBestCmap(), ft["hmtx"].metrics

    def scaled(v: float) -> NumberObject:
        return NumberObject(round(v * 1000 / upem))

    def unicode_of(code: int) -> int | None:
        try:
            return ord(bytes([code]).decode("cp1251"))
        except UnicodeDecodeError:
            return None

    differences, widths = [], []
    for code in range(32, 256):
        u = unicode_of(code)
        glyph = cmap.get(u) if u else None
        widths.append(scaled(hmtx[glyph][0]) if glyph else NumberObject(0))
        if code >= 128 and u:
            differences += [NumberObject(code), NameObject(f"/uni{u:04X}")]
    program = DecodedStreamObject()
    data = ttf.read_bytes()
    program.set_data(data)
    program[NameObject("/Length1")] = NumberObject(len(data))
    head, hhea = ft["head"], ft["hhea"]
    descriptor = DictionaryObject({
        NameObject("/Type"): NameObject("/FontDescriptor"), NameObject("/FontName"): NameObject("/Manrope-Regular"),
        NameObject("/Flags"): NumberObject(32),
        NameObject("/FontBBox"): ArrayObject([scaled(head.xMin), scaled(head.yMin), scaled(head.xMax), scaled(head.yMax)]),
        NameObject("/ItalicAngle"): NumberObject(0), NameObject("/Ascent"): scaled(hhea.ascent),
        NameObject("/Descent"): scaled(hhea.descent), NameObject("/CapHeight"): scaled(getattr(ft["OS/2"], "sCapHeight", 700)),
        NameObject("/StemV"): NumberObject(80), NameObject("/FontFile2"): writer._add_object(program)})
    encoding = DictionaryObject({NameObject("/Type"): NameObject("/Encoding"),
                                 NameObject("/BaseEncoding"): NameObject("/WinAnsiEncoding"),
                                 NameObject("/Differences"): ArrayObject(differences)})
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/TrueType"),
        NameObject("/BaseFont"): NameObject("/Manrope-Regular"), NameObject("/FirstChar"): NumberObject(32),
        NameObject("/LastChar"): NumberObject(255), NameObject("/Widths"): ArrayObject(widths),
        NameObject("/FontDescriptor"): writer._add_object(descriptor), NameObject("/Encoding"): writer._add_object(encoding)})
    form = writer._root_object["/AcroForm"]
    resources = form.get("/DR", DictionaryObject())
    fonts = resources.get("/Font", DictionaryObject())
    fonts[NameObject("/GtMn")] = writer._add_object(font)
    resources[NameObject("/Font")] = fonts
    form[NameObject("/DR")] = resources
    da = TextStringObject(f"/GtMn {size} Tf 0.047 0.051 0.047 rg")
    form[NameObject("/DA")] = da
    for page in writer.pages:
        for annot in page.get("/Annots", []) or []:
            annot = annot.get_object()
            if annot.get("/FT") == "/Tx":
                annot[NameObject("/DA")] = da


# ---------- source ----------
@dataclass
class Question:
    text: str
    subs: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    grid: list[list[str]] = field(default_factory=list)    # header row + answer rows; empty for a text answer

    def answer_rows(self) -> list[list[str]]:
        return [r for r in self.grid[1:] if not is_group_row(r)]


def is_group_row(row: list[str]) -> bool:
    return bool(row[0]) and not any(row[1:])


@dataclass
class Page:
    name: str
    path: str = ""
    is_direction: bool = False
    notes: list[str] = field(default_factory=list)
    questions: list[Question] = field(default_factory=list)


@dataclass
class Direction:
    name: str
    pages: list[Page] = field(default_factory=list)


def parse_questions(md: str) -> list[Direction]:
    """«## направление», «### страница», `путь`, «- вопрос», «  - вариант», «  пояснение», «| таблица |» после вопроса."""
    directions: list[Direction] = []
    page: Page | None = None
    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.lstrip().startswith("|") and page is not None:
            if not page.questions:
                raise SystemExit(f"таблица без вопроса перед ней: {line}")
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):     # the |---| line under the header
                page.questions[-1].grid.append(cells)
            continue
        if line.startswith("## "):
            directions.append(Direction(line[3:].strip()))
            page = Page(line[3:].strip(), is_direction=True)
            directions[-1].pages.append(page)
        elif line.startswith("### "):
            if not directions:
                raise SystemExit(f"страница вне направления: {line}")
            page = Page(line[4:].strip())
            directions[-1].pages.append(page)
        elif line.startswith("# ") or page is None:
            continue                                   # the file's own title and intro
        elif re.fullmatch(r"`[^`]+`", line.strip()):
            page.path = line.strip().strip("`")
        elif line.startswith("- ") or line.startswith("* "):
            page.questions.append(Question(line[2:].strip()))
        elif re.match(r"^\s{2,}[-*] ", line):
            if not page.questions:
                raise SystemExit(f"вложенный пункт без вопроса: {line}")
            page.questions[-1].subs.append(re.sub(r"^\s+[-*] ", "", line))
        elif line.startswith(" ") and page.questions:
            page.questions[-1].notes.append(line.strip())
        else:
            page.notes.append(line.strip())
    for d in directions:
        d.pages = [p for p in d.pages if p.questions or p.notes]
        for p in d.pages:
            for q in p.questions:
                check_grid(q)
    return [d for d in directions if d.pages]


def check_grid(q: Question) -> None:
    if not q.grid:
        return
    if not q.answer_rows():
        raise SystemExit(f"в таблице нет строк для ответа: {q.text}")
    width = len(q.grid[0])
    for row in q.grid:
        if len(row) != width:
            raise SystemExit(f"в строке таблицы {len(row)} ячеек, в заголовке {width}: {' | '.join(row)}")
    kinds = [column_kind(q, c) for c in range(width)]
    if kinds[0] != "text":
        raise SystemExit(f"первая колонка таблицы должна быть текстом: {q.text}")
    for row in q.answer_rows():
        for c, cell in enumerate(row):
            if kinds[c] != "text" and cell != {"choice": CELL_CHOICE, "check": CELL_CHECK, "field": CELL_FIELD}[kinds[c]]:
                raise SystemExit(f"в колонке «{q.grid[0][c]}» разные типы ячеек: {' | '.join(row)}")


def column_kind(q: Question, c: int) -> str:
    """text, choice, check or field — by the cells of the answer rows."""
    cells = {r[c] for r in q.answer_rows()}
    for kind, token in (("choice", CELL_CHOICE), ("check", CELL_CHECK), ("field", CELL_FIELD)):
        if token in cells:
            return kind
    return "text"


def parse_renames(md: str) -> list[dict]:
    rows = []
    for line in md.splitlines():
        if not line.startswith("| `"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        rows.append({"path": cells[0].strip("`"), "old": cells[1], "h1": cells[2], "nav": cells[3],
                     "query": cells[4], "freq": cells[5]})
    return rows


def site_order() -> dict[str, int]:
    """Page path -> position in the site menu: a direction, then its pages."""
    data = json.loads((ROOT / "data" / "services.json").read_text(encoding="utf-8"))
    paths = [p for c in data["categories"] for p in (c["href"], *(s["href"] for s in c["subs"]))]
    return {p: i for i, p in enumerate(paths)}


# ---------- text ----------
HAS_PT_MONO = True


def inline(text: str) -> str:
    """Markdown inline -> reportlab paragraph markup (bold, code, ₽ and → from a font that has them)."""
    s = html.escape(text, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\1", s)
    s = re.sub(r"`([^`]+)`", r'<font name="Mono" size="8">\1</font>', s)
    if HAS_PT_MONO:
        s = s.replace("₽", '<font name="PTMono">₽</font>').replace("→", '<font name="PTMono">→</font>')
    else:
        s = s.replace("₽", "руб.").replace("→", "->")
    return s


STYLES = {
    "body": ParagraphStyle("body", fontName="Manrope", fontSize=9.6, leading=13.6, textColor=INK, alignment=TA_LEFT),
    "q": ParagraphStyle("q", fontName="Manrope", fontSize=9.6, leading=13.6, textColor=INK),
    "sub": ParagraphStyle("sub", fontName="Manrope", fontSize=9.2, leading=12.8, textColor=INK, leftIndent=10, bulletIndent=0),
    "note": ParagraphStyle("note", fontName="Manrope", fontSize=8.6, leading=12, textColor=GRAY),
    "num": ParagraphStyle("num", fontName="Mono", fontSize=8.6, leading=13.6, textColor=GREEN),
    "dir": ParagraphStyle("dir", fontName="Unbounded", fontSize=17, leading=20, textColor=INK, spaceAfter=4),
    "dir_kicker": ParagraphStyle("dir_kicker", fontName="Mono", fontSize=7.8, leading=10, textColor=GREEN),
    "page": ParagraphStyle("page", fontName="Manrope-Bold", fontSize=11.5, leading=15, textColor=INK),
    "path": ParagraphStyle("path", fontName="Mono", fontSize=7.6, leading=10, textColor=GRAY_LIGHT),
    "h2": ParagraphStyle("h2", fontName="Unbounded", fontSize=13, leading=16, textColor=INK, spaceAfter=6),
    "label": ParagraphStyle("label", fontName="Mono", fontSize=7.4, leading=9.5, textColor=GRAY),
    "toc0": ParagraphStyle("toc0", fontName="Manrope", fontSize=10, leading=17, textColor=INK, leftIndent=0),
    "cell": ParagraphStyle("cell", fontName="Manrope", fontSize=8.6, leading=11.4, textColor=INK),
    "cell_b": ParagraphStyle("cell_b", fontName="Manrope-Bold", fontSize=8.6, leading=11.4, textColor=INK),
    "cell_small": ParagraphStyle("cell_small", fontName="Manrope", fontSize=7.8, leading=10.4, textColor=GRAY),
    "group": ParagraphStyle("group", fontName="Manrope-Bold", fontSize=8.6, leading=11.4, textColor=GREEN),
}


def plural(n: int, one: str, few: str, many: str) -> str:
    """plural(21, "вопрос", "вопроса", "вопросов") -> "вопрос"."""
    if 11 <= n % 100 <= 14:
        return many
    return {1: one, 2: few, 3: few, 4: few}.get(n % 10, many)


# ---------- form fields ----------
class AnswerField(Flowable):
    """A fillable text box; printed, it is an empty frame to write in."""

    def __init__(self, name: str, height: float, tooltip: str, indent: float = 0, multiline: bool = True):
        super().__init__()
        self.name, self.height, self.tooltip, self.indent, self.multiline = name, height, tooltip, indent, multiline

    def wrap(self, avail_w: float, avail_h: float):
        self.box_w = avail_w - self.indent
        return avail_w, self.height

    def draw(self):
        self.canv.acroForm.textfield(
            name=self.name, tooltip=self.tooltip, value="", x=self.indent, y=0, width=self.box_w, height=self.height,
            relative=True, fieldFlags="multiline" if self.multiline else "", maxlen=4000,
            borderStyle="solid", borderWidth=0.6, borderColor=LINE, fillColor=FIELD_BG, textColor=INK,
            fontName="Helvetica", fontSize=9 if self.multiline else 10, forceBorder=True)


class CheckField(Flowable):
    def __init__(self, name: str, tooltip: str, size: float = 13):
        super().__init__()
        self.name, self.tooltip, self.size = name, tooltip, size

    def wrap(self, avail_w, avail_h):
        return self.size, self.size

    def draw(self):
        self.canv.acroForm.checkbox(name=self.name, tooltip=self.tooltip, x=0, y=0, size=self.size, relative=True,
                                    buttonStyle="check", borderWidth=0.8, borderColor=GREEN, fillColor=colors.white,
                                    textColor=GREEN, forceBorder=True, fieldFlags="")


class ChoiceField(Flowable):
    """One radio button; the buttons of a table row share a name, so only one of them can be on."""

    def __init__(self, name: str, value: str, tooltip: str, size: float = GRID_MARK):
        super().__init__()
        self.name, self.value, self.tooltip, self.size = name, value, tooltip, size

    def wrap(self, avail_w, avail_h):
        return self.size, self.size

    def draw(self):
        # a square with a check mark, like the checkboxes: reportlab's round buttons look the same on and off in
        # «Просмотр» (PDFKit). No noToggleToOff flag, so a second click clears a wrong answer.
        self.canv.acroForm.radio(name=self.name, value=self.value, tooltip=self.tooltip, x=0, y=0, size=self.size,
                                 relative=True, buttonStyle="check", shape="square", borderWidth=0.8,
                                 borderColor=GREEN, fillColor=colors.white, textColor=GREEN, forceBorder=True,
                                 fieldFlags="radio")


class DirectionHeading(Paragraph):
    """Direction title: goes to the table of contents and the PDF bookmarks."""

    def __init__(self, text: str, key: str):
        super().__init__(inline(text), STYLES["dir"])
        self.toc_text, self.key = text, key


# ---------- document ----------
class Questionnaire(BaseDocTemplate):
    def __init__(self, filename: str, title: str, **kw):
        super().__init__(filename, pagesize=A4, leftMargin=MARGIN_X, rightMargin=MARGIN_X, topMargin=MARGIN_TOP,
                         bottomMargin=MARGIN_BOTTOM, title=title, author="Автосервис «Гараж»",
                         subject="Вопросы владельцу для страниц услуг сайта", **kw)
        self.section = ""
        frame = Frame(MARGIN_X, MARGIN_BOTTOM, PAGE_W - 2 * MARGIN_X, PAGE_H - MARGIN_TOP - MARGIN_BOTTOM, id="f",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        cover_frame = Frame(MARGIN_X, MARGIN_BOTTOM, PAGE_W - 2 * MARGIN_X, PAGE_H - 118 * mm - MARGIN_BOTTOM, id="c",
                            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate("cover", [cover_frame], onPage=draw_cover),
                               PageTemplate("content", [frame], onPageEnd=draw_chrome)])

    def handle_documentBegin(self):
        self.section = ""          # multiBuild runs several passes: the running header starts empty in each
        super().handle_documentBegin()

    def afterFlowable(self, flowable):
        if isinstance(flowable, DirectionHeading):
            self.section = flowable.toc_text
            self.canv.bookmarkPage(flowable.key)
            self.canv.addOutlineEntry(flowable.toc_text, flowable.key, level=0, closed=True)
            self.notify("TOCEntry", (0, flowable.toc_text, self.page, flowable.key))
        elif getattr(flowable, "outline", None):
            key, text = flowable.outline
            self.section = text
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=0, closed=True)
            self.notify("TOCEntry", (0, text, self.page, key))


def hazard(canv, x, y, w, h, color=GREEN, step=9):
    """The site's diagonal hazard stripe."""
    canv.saveState()
    p = canv.beginPath()
    p.rect(x, y, w, h)
    canv.clipPath(p, stroke=0, fill=0)
    canv.setFillColor(color)
    i = -h
    while i < w + h:
        q = canv.beginPath()
        q.moveTo(x + i, y)
        q.lineTo(x + i + step / 2, y)
        q.lineTo(x + i + step / 2 + h, y + h)
        q.lineTo(x + i + h, y + h)
        q.close()
        canv.drawPath(q, stroke=0, fill=1)
        i += step
    canv.restoreState()


COVER = {}


def draw_cover(canv, doc):
    band = 118 * mm
    canv.saveState()
    canv.setFillColor(INK)
    canv.rect(0, PAGE_H - band, PAGE_W, band, stroke=0, fill=1)
    hazard(canv, 0, PAGE_H - band - 5, PAGE_W, 5)
    if LOGO.exists():
        canv.drawImage(str(LOGO), MARGIN_X, PAGE_H - 22 * mm - 17 * mm, width=49 * mm, height=17 * mm, mask="auto",
                       preserveAspectRatio=True, anchor="sw")
    canv.setFillColor(GREEN_BRIGHT)
    canv.setFont("Mono", 8.5)
    canv.drawString(MARGIN_X, PAGE_H - 58 * mm, COVER["kicker"])
    canv.setFillColor(colors.white)
    canv.setFont("Unbounded", 28)
    first, second = COVER["title"]
    canv.drawString(MARGIN_X, PAGE_H - 72 * mm, first)
    canv.drawString(MARGIN_X, PAGE_H - 84 * mm, second)
    canv.setFillColor(colors.HexColor("#b8bdb8"))
    canv.setFont("Manrope", 10.5)
    canv.drawString(MARGIN_X, PAGE_H - 96 * mm, COVER["subtitle"])
    canv.setFont("Mono", 8)
    canv.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 22 * mm - 11 * mm, COVER["date"])
    canv.restoreState()


def draw_chrome(canv, doc):
    canv.saveState()
    hazard(canv, 0, PAGE_H - 3, PAGE_W, 3)
    canv.setFont("Mono", 7.2)
    canv.setFillColor(GRAY)
    canv.drawString(MARGIN_X, PAGE_H - 12 * mm, "АНКЕТА ВЛАДЕЛЬЦА · GARAGE.TEAM")
    if doc.section:
        canv.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 12 * mm, doc.section.upper()[:70])
    canv.setStrokeColor(LINE)
    canv.setLineWidth(0.5)
    canv.line(MARGIN_X, 11 * mm, PAGE_W - MARGIN_X, 11 * mm)
    canv.drawString(MARGIN_X, 7 * mm, "Автосервис «Гараж», Нижний Новгород, ул. Красная слобода, 9 · (831) 416-16-77")
    canv.drawRightString(PAGE_W - MARGIN_X, 7 * mm, f"стр. {doc.page}")
    canv.restoreState()


# ---------- story ----------
def labelled_field(label: str, name: str, height: float = 20, multiline: bool = False):
    return [Paragraph(label, STYLES["label"]), Spacer(1, 2), AnswerField(name, height, label, multiline=multiline), Spacer(1, 8)]


@dataclass(frozen=True)
class Profile:
    source: str
    out: str
    doc_title: str
    kicker: str
    title: tuple[str, str]
    intro: str
    how: tuple[str, ...]
    page_per_direction: bool      # the full version starts every direction on a new sheet


FILL_IN = ("Отвечайте прямо в полях: их заполняют в «Просмотре» на Mac или в Adobe Acrobat Reader. "
           "Можно распечатать и написать ручкой.")
RENAMES_HOW = "В конце — новые названия страниц: отметьте «согласен» или впишите свой вариант."

PROFILES = {
    "full": Profile(
        source="owner-questions.md", out="owner-questions.pdf",
        doc_title="Анкета владельца: вопросы по страницам услуг garage.team",
        kicker="// АНКЕТА ВЛАДЕЛЬЦА · GARAGE.TEAM", title=("ВОПРОСЫ ПО СТРАНИЦАМ", "УСЛУГ САЙТА"),
        intro="Эта анкета нужна, чтобы дописать страницы услуг сайта фактами. Сейчас на сайте нет ничего, что не "
              "подтверждено старым сайтом, прайсом или общими техническими знаниями. Ваши ответы позволят указать сроки, "
              "оборудование и работы, которые вы делаете сами. О ценах анкета не спрашивает.",
        how=(FILL_IN,
             "Не знаете ответа — пропустите вопрос. Если работу не делаете, так и напишите: «не делаем» — это тоже важный ответ.",
             "Направления идут в порядке меню сайта, каждое начинается с новой страницы. Разделы можно раздать мастерам.",
             RENAMES_HOW),
        page_per_direction=True),
    "short": Profile(
        source="owner-questions-short.md", out="owner-questions-short.pdf",
        doc_title="Анкета владельца, короткая версия: вопросы для страниц услуг garage.team",
        kicker="// АНКЕТА ВЛАДЕЛЬЦА · GARAGE.TEAM · КОРОТКАЯ ВЕРСИЯ", title=("КОРОТКАЯ АНКЕТА", "ДЛЯ ВЛАДЕЛЬЦА"),
        intro="Ответы нужны, чтобы дописать страницы услуг сайта фактами: сейчас там нет ничего, что не подтверждено "
              "старым сайтом, прайсом или общими техническими знаниями. Гарантию, мастеров, оборудование, сроки "
              "и подрядчиков спрашиваем один раз, в разделе «Общие вопросы». Где хватит «да» или «нет», вместо вопроса "
              "строка в таблице. О ценах анкета не спрашивает. Это короткая версия: полную, owner-questions.pdf, "
              "заполнять не нужно.",
        how=(FILL_IN,
             "В таблицах отметьте один вариант в каждой строке. Если нужно пояснить, впишите в поле «комментарий». "
             "Повторный щелчок снимает отметку.",
             "Не знаете ответа — пропустите строку. «Не делаем» — тоже важный ответ: такую работу мы не будем обещать на сайте.",
             "Разделы по направлениям можно раздать мастерам.",
             RENAMES_HOW),
        page_per_direction=False),
}


@dataclass(frozen=True)
class Stats:
    text: int          # questions answered in a text box
    rows: int          # table rows answered with a mark
    pages: int
    directions: int
    renames: int


def count(directions: list[Direction], n_renames: int) -> Stats:
    questions = [q for d in directions for p in d.pages for q in p.questions]
    return Stats(text=sum(1 for q in questions if not q.grid), rows=sum(len(q.answer_rows()) for q in questions),
                 pages=sum(len(d.pages) for d in directions if d.name != GENERAL),
                 directions=sum(1 for d in directions if d.name != GENERAL), renames=n_renames)


def stat_cells(s: Stats) -> list[tuple[int, str]]:
    if s.rows:
        return [(s.text, plural(s.text, "вопрос с ответом текстом", "вопроса с ответом текстом", "вопросов с ответом текстом")),
                (s.rows, plural(s.rows, "строка, где хватит отметки", "строки, где хватит отметки", "строк, где хватит отметки")),
                (s.directions, plural(s.directions, "направление", "направления", "направлений")),
                (s.renames, plural(s.renames, "новое название", "новых названия", "новых названий"))]
    return [(s.text, plural(s.text, "вопрос", "вопроса", "вопросов")),
            (s.pages, plural(s.pages, "страница услуг", "страницы услуг", "страниц услуг")),
            (s.directions, plural(s.directions, "направление", "направления", "направлений")),
            (s.renames, plural(s.renames, "новое название", "новых названия", "новых названий"))]


def cover_story(profile: Profile, s: Stats) -> list:
    stats = Table([[Paragraph(f'<font name="Unbounded" size="18">{v}</font><br/>{inline(k)}', STYLES["body"])
                    for v, k in stat_cells(s)]],
                  colWidths=[(PAGE_W - 2 * MARGIN_X) / 4] * 4)
    stats.setStyle(TableStyle([("LINEBEFORE", (1, 0), (-1, 0), 0.5, LINE), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                               ("LEFTPADDING", (0, 0), (0, 0), 0), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story = [Spacer(1, 6), stats, Spacer(1, 14), Paragraph(inline(profile.intro), STYLES["body"])]
    story += [Spacer(1, 10), Paragraph("Как заполнять", STYLES["page"]), Spacer(1, 4)]
    story += [Paragraph(inline(t), STYLES["sub"], bulletText="—") for t in profile.how]
    story += [Spacer(1, 14)]
    fields = Table([[labelled_field("Кто заполнил", "cover_name"), labelled_field("Дата", "cover_date")],
                    [labelled_field("Телефон для уточнений", "cover_phone"), labelled_field("Должность", "cover_role")]],
                   colWidths=[(PAGE_W - 2 * MARGIN_X) / 2] * 2)
    fields.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (0, -1), 10),
                                ("RIGHTPADDING", (1, 0), (1, -1), 0), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(fields)
    return story


def question_block(number: int, q: Question, page_name: str) -> Flowable:
    """The number and the question; a text question also gets its answer box, a table question is followed by the table."""
    body = [Paragraph(inline(q.text), STYLES["q"])]
    body += [Paragraph(inline(s), STYLES["sub"], bulletText="•") for s in q.subs]
    body += [Paragraph(inline(n), STYLES["note"]) for n in q.notes]
    if not q.grid:
        body += [Spacer(1, 4), AnswerField(f"q{number:03d}", ANSWER_H, f"Ответ на вопрос {number} ({page_name})")]
    t = Table([[Paragraph(f"{number:03d}", STYLES["num"]), body]], colWidths=[NUM_W, PAGE_W - 2 * MARGIN_X - NUM_W])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 4 if q.grid else 10)]))
    return t


def grid_widths(q: Question, kinds: list[str]) -> list[float]:
    """Mark columns as wide as their heading; comment boxes about a third of the rest; text shares what is left."""
    marks = {c: max(11 * mm, pdfmetrics.stringWidth(q.grid[0][c].upper(), "Mono", 7.4) + 8)
             for c, k in enumerate(kinds) if k in ("choice", "check")}
    rest = PAGE_W - 2 * MARGIN_X - NUM_W - sum(marks.values())
    fields = [c for c, k in enumerate(kinds) if k == "field"]
    texts = [c for c, k in enumerate(kinds) if k == "text"]
    field_w = rest * (0.36 if marks else 0.45) / len(fields) if fields else 0
    text_rest = rest - field_w * len(fields)
    # every text column fits its longest word (reportlab would cut «моторист-дефектовщик» in two);
    # the rest goes to longer texts, but never more than twice to one column as to another
    rows = q.answer_rows()
    least = {c: max(pdfmetrics.stringWidth(w, "Manrope", STYLES["cell"].fontSize)
                    for r in rows for w in re.sub(r"\*\*|`", "", r[c]).split() or [""]) + 10 for c in texts}
    avg = {c: sum(len(r[c]) for r in rows) / len(rows) for c in texts}
    weight = {c: min(max(avg[c], 1), 2 * max(min(avg.values()), 1)) for c in texts}
    spare = text_rest - sum(least.values())
    if spare < 0:
        raise SystemExit(f"таблица не помещается по ширине: {q.text}")
    widths = []
    for c, k in enumerate(kinds):
        if c in marks:
            widths.append(marks[c])
        elif k == "field":
            widths.append(field_w)
        else:
            widths.append(least[c] + spare * weight[c] / sum(weight.values()))
    return widths


def grid_table(number: int, q: Question) -> Table:
    kinds = [column_kind(q, c) for c in range(len(q.grid[0]))]
    header = [""] + [Paragraph(html.escape(h.upper()), STYLES["label"]) for h in q.grid[0]]
    data, style = [header], [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (1, -1), 0), ("LINEBELOW", (1, 0), (-1, 0), 0.8, INK),
    ]
    for c, k in enumerate(kinds, 1):
        if k in ("choice", "check"):
            style.append(("ALIGN", (c, 0), (c, -1), "CENTER"))
    last = len(q.grid) - 1
    # a sheet never starts or ends a table with a lone row, and a subheading stays with the row under it
    style += [("NOSPLIT", (0, 0), (-1, min(3, last))), ("NOSPLIT", (0, max(0, last - 1)), (-1, last))]
    for r, row in enumerate(q.grid[1:], 1):
        if is_group_row(row):
            data.append([""] + [Paragraph(inline(row[0].strip("*")), STYLES["group"])] + [""] * (len(row) - 1))
            style += [("SPAN", (1, r), (-1, r)), ("TOPPADDING", (1, r), (-1, r), 10),
                      ("NOSPLIT", (0, r), (-1, min(r + 1, last)))]
            continue
        label = re.sub(r"\*\*|`", "", row[0])
        cells = [""]
        for c, (cell, kind) in enumerate(zip(row, kinds)):
            key = f"q{number:03d}_{r:02d}"
            if kind == "text":
                cells.append(Paragraph(inline(cell), STYLES["cell"]))
            elif kind == "choice":
                cells.append(ChoiceField(key, f"v{c}", label))
            elif kind == "check":
                cells.append(CheckField(f"{key}_c{c}", f"{label}: {q.grid[0][c]}", size=GRID_MARK))
            else:
                cells.append(AnswerField(f"{key}_f{c}", GRID_FIELD_H, f"{label}: {q.grid[0][c]}"))
        data.append(cells)
        style.append(("LINEBELOW", (1, r), (-1, r), 0.4, LINE))
    t = Table(data, colWidths=[NUM_W] + grid_widths(q, kinds), repeatRows=1)
    t.setStyle(TableStyle(style))
    return t


def direction_opening(d: Direction, di: int, total: int, page_per_direction: bool) -> list:
    kicker = "// ДЛЯ ВСЕХ УСЛУГ СРАЗУ" if d.name == GENERAL else f"// НАПРАВЛЕНИЕ {di:02d} ИЗ {total:02d}"
    opening = [Paragraph(kicker, STYLES["dir_kicker"]), Spacer(1, 4), DirectionHeading(d.name, f"dir{di}"), Spacer(1, 6)]
    if page_per_direction or d.name == GENERAL:
        return [PageBreak()] + opening
    return [Spacer(1, 18), CondPageBreak(170)] + opening


def questions_story(directions: list[Direction], profile: Profile) -> tuple[list, int]:
    story, number = [], 0
    total = sum(1 for d in directions if d.name != GENERAL)
    di = 0
    for d in directions:
        if d.name != GENERAL:
            di += 1
        story += direction_opening(d, di, total, profile.page_per_direction)
        for p in d.pages:
            head = []
            if not (p.is_direction and not p.path):       # the short version asks about the direction as a whole
                head.append(Paragraph(inline("Страница направления" if p.is_direction else p.name), STYLES["page"]))
            if p.path:
                head.append(Paragraph(html.escape("garage.team" + p.path), STYLES["path"]))
            if head:
                head.append(Spacer(1, 6))
            head += [Paragraph(inline(n), STYLES["note"]) for n in p.notes]
            blocks = []
            for q in p.questions:
                number += 1
                block = [question_block(number, q, p.name)]
                if q.grid:
                    block.append(grid_table(number, q))
                blocks.append(block)
            if not blocks:
                story += head
            for i, block in enumerate(blocks):
                has_table = len(block) > 1
                # a page title never stays alone at the bottom of a sheet, nor does a question without its table
                story.append(CondPageBreak(170 if has_table else 90 if i == 0 else 0))
                story.append(KeepTogether((head if i == 0 else []) + block[:1]))
                story += block[1:]
                if has_table:
                    story.append(Spacer(1, 12))
            story.append(Spacer(1, 8))
    return story, number


def searches(n: int) -> str:
    """«1 321 запрос в месяц», «23 запроса…», «644 запроса…», «12 запросов…»."""
    word = "запросов" if 11 <= n % 100 <= 14 else {1: "запрос", 2: "запроса", 3: "запроса", 4: "запроса"}.get(n % 10, "запросов")
    return f"{n:,}".replace(",", "\u00a0") + f" {word} в месяц"


def renames_story(rows: list[dict]) -> list:
    heading = Paragraph("Новые названия страниц", STYLES["h2"])
    heading.outline = ("renames", "Новые названия страниц")
    story = [PageBreak(), Paragraph("// СОГЛАСОВАНИЕ", STYLES["dir_kicker"]), Spacer(1, 4), heading,
             Paragraph("Адреса страниц не менялись. Новые заголовки выбраны по тому, как люди ищут услугу в Яндексе. "
                       "В колонке «Как ищут в Яндексе» — фраза, которую набирают в поиске, и сколько раз в месяц её ищут "
                       "в Нижнем Новгороде (Яндекс Wordstat). Это не цена. Отметьте «согласен» или впишите свой вариант.",
                       STYLES["note"]), Spacer(1, 10)]
    w = PAGE_W - 2 * MARGIN_X
    cols = [w * 0.27, w * 0.37, w * 0.24, w * 0.12]
    head = Table([[Paragraph("БЫЛО", STYLES["label"]), Paragraph("СТАНЕТ", STYLES["label"]),
                   Paragraph("КАК ИЩУТ В ЯНДЕКСЕ", STYLES["label"]), Paragraph("СОГЛАСЕН", STYLES["label"])]], colWidths=cols)
    head.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 0.8, INK), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    story.append(head)
    for i, r in enumerate(rows, 1):
        new = inline(r["h1"])
        if r["nav"] and r["nav"] != r["h1"]:
            new += f'<br/><font color="#6b716b" size="7.8">в меню: {inline(r["nav"])}</font>'
        # searches a month in Yandex, not a price: the wording has to say so
        freq = searches(int(r["freq"])) if r["freq"].isdigit() else r["freq"]
        row = Table([[Paragraph(inline(r["old"]), STYLES["cell"]), Paragraph(new, STYLES["cell_b"]),
                      Paragraph(f'{inline(r["query"])}<br/>{freq}', STYLES["cell_small"]),
                      CheckField(f"rename_ok_{i:02d}", f"Согласен: {r['h1']}")]], colWidths=cols)
        row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                 ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 7),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        alt = AnswerField(f"rename_alt_{i:02d}", 18, f"Свой вариант названия вместо: {r['h1']}", multiline=False)
        story.append(KeepTogether([row, Paragraph("свой вариант", STYLES["label"]), Spacer(1, 1), alt, Spacer(1, 5),
                                   Table([[""]], colWidths=[w], style=[("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE)])]))
    notes_heading = Paragraph("Что ещё важно знать", STYLES["h2"])
    story += [Spacer(1, 16), notes_heading,
              Paragraph("Всё, что не вошло в вопросы: новые услуги, ошибки на сайте, пожелания.", STYLES["note"]),
              Spacer(1, 6), AnswerField("notes", 150, "Что ещё важно знать")]
    return story


def subtitle(s: Stats) -> str:
    where = "Автосервис «Гараж», Нижний Новгород"
    if s.rows:
        return (f"{where} · {s.text} {plural(s.text, 'вопрос', 'вопроса', 'вопросов')} "
                f"и {s.rows} {plural(s.rows, 'строка', 'строки', 'строк')} с отметками")
    return f"{where} · {s.text} {plural(s.text, 'вопрос', 'вопроса', 'вопросов')} с полями для ответов"


def build(profile: Profile, out: Path) -> tuple[Stats, int]:
    global HAS_PT_MONO
    directions = parse_questions((SEO / profile.source).read_text(encoding="utf-8"))
    renames = parse_renames((SEO / "renames.md").read_text(encoding="utf-8"))
    order = site_order()           # same order as the questions: a direction first, then its pages
    missing = [r["path"] for r in renames if r["path"] not in order]
    if missing:
        raise SystemExit(f"в seo/renames.md страницы, которых нет в data/services.json: {', '.join(missing)}")
    renames.sort(key=lambda r: order[r["path"]])
    stats = count(directions, len(renames))
    with tempfile.TemporaryDirectory() as tmp:
        HAS_PT_MONO = build_fonts(Path(tmp))
        STYLES["sub"].bulletFontName = "Manrope"
        COVER.update(kicker=profile.kicker, title=profile.title, subtitle=subtitle(stats),
                     date=date.today().strftime("%d.%m.%Y"))
        toc = TableOfContents(levelStyles=[STYLES["toc0"]], dotsMinLevel=0)
        story = [NextPageTemplate("content")] + cover_story(profile, stats)
        story += [PageBreak(), Paragraph("// СОДЕРЖАНИЕ", STYLES["dir_kicker"]), Spacer(1, 4),
                  Paragraph("Содержание", STYLES["h2"]), Spacer(1, 6), toc]
        q_story, _ = questions_story(directions, profile)
        story += q_story + renames_story(renames)
        raw = out.with_suffix(".tmp.pdf")
        Questionnaire(str(raw), profile.doc_title).multiBuild(story)
        writer = PdfWriter(clone_from=PdfReader(str(raw)))
        add_field_font(writer, Path(tmp) / "Manrope.ttf")
    # readers draw the typed text themselves, with the field font above, instead of a pre-made appearance
    writer._root_object["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(True)
    writer.page_mode = "/UseOutlines"
    with open(out, "wb") as fh:
        writer.write(fh)
    raw.unlink()
    return stats, len(writer.pages)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--short", action="store_true", help="короткая версия из seo/owner-questions-short.md")
    ap.add_argument("-o", "--out", type=Path, help="куда записать PDF")
    args = ap.parse_args()
    profile = PROFILES["short" if args.short else "full"]
    out = args.out or SEO / profile.out
    s, pages = build(profile, out)
    rows = f", {s.rows} строк с отметками" if s.rows else ""
    print(f"записано {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}: "
          f"{s.text} вопросов с ответом текстом{rows}, {s.renames} названий на согласование, {pages} стр.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
