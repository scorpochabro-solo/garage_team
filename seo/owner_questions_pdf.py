#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Анкета владельца в PDF: все вопросы из seo/owner-questions.md с полями для ответов
и согласование новых названий страниц из seo/renames.md.

Поля заполняются в «Просмотре» на Mac, в Adobe Acrobat Reader и других программах для PDF;
распечатанная анкета заполняется ручкой (поля печатаются рамками).

  python3 seo/owner_questions_pdf.py          # -> seo/owner-questions.pdf
  python3 seo/owner_questions_pdf.py -o x.pdf
  python3 seo/owner_questions_pdf.py --short  # seo/owner-questions-short.md -> seo/owner-questions-short.pdf,
                                              # без согласования названий: её отправляют владельцу

Нужны reportlab, fonttools и brotli (pip install reportlab fonttools brotli).
Шрифты — шрифты сайта: вариативные woff2 из src/assets/fonts при запуске превращаются в статичные TTF
нужной жирности, латиница и кириллица склеиваются в один файл. Знаки ₽ и → берутся из PT Mono (есть в macOS),
если его нет — пишутся как «руб.» и «->».
"""
from __future__ import annotations

import argparse
import html
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
        Merger().merge(parts).save(out)
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
    """seo/owner-questions.md: «## направление», «### страница», `путь`, «- вопрос», «  - вариант», «  пояснение»."""
    directions: list[Direction] = []
    page: Page | None = None
    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
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
    return [d for d in directions if d.pages]


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
}


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


class DirectionHeading(Paragraph):
    """Direction title: goes to the table of contents and the PDF bookmarks."""

    def __init__(self, text: str, key: str):
        super().__init__(inline(text), STYLES["dir"])
        self.toc_text, self.key = text, key


# ---------- document ----------
class Questionnaire(BaseDocTemplate):
    def __init__(self, filename: str, **kw):
        super().__init__(filename, pagesize=A4, leftMargin=MARGIN_X, rightMargin=MARGIN_X, topMargin=MARGIN_TOP,
                         bottomMargin=MARGIN_BOTTOM, title="Анкета владельца: вопросы по страницам услуг garage.team",
                         author="Автосервис «Гараж»", subject="Вопросы владельцу для страниц услуг сайта", **kw)
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


COVER = {"kicker": "// АНКЕТА ВЛАДЕЛЬЦА · GARAGE.TEAM"}
SHORT = False


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
    canv.drawString(MARGIN_X, PAGE_H - 72 * mm, "ВОПРОСЫ ПО СТРАНИЦАМ")
    canv.drawString(MARGIN_X, PAGE_H - 84 * mm, "УСЛУГ САЙТА")
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


def cover_story(directions: list[Direction], n_questions: int, n_renames: int) -> list:
    n_pages = sum(len(d.pages) for d in directions)
    cells = ((n_questions, "вопросов"), (len(directions), "разделов")) if SHORT else \
        ((n_questions, "вопросов"), (n_pages, "страниц услуг"), (len(directions), "направлений"), (n_renames, "новых названий"))
    stats = Table([[Paragraph(f'<font name="Unbounded" size="18">{v}</font><br/>{inline(k)}', STYLES["body"])
                    for v, k in cells]], colWidths=[(PAGE_W - 2 * MARGIN_X) / 4] * len(cells), hAlign="LEFT")
    stats.setStyle(TableStyle([("LINEBEFORE", (1, 0), (-1, 0), 0.5, LINE), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                               ("LEFTPADDING", (0, 0), (0, 0), 0), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    intro = [
        "Эта анкета нужна, чтобы дописать страницы услуг сайта фактами. Сейчас на сайте нет ничего, что не подтверждено "
        "старым сайтом, прайсом или общими техническими знаниями. Ваши ответы позволят указать сроки, оборудование "
        "и работы, которые вы делаете сами. О ценах анкета не спрашивает.",
    ]
    how = [
        "Отвечайте прямо в полях: их заполняют в «Просмотре» на Mac или в Adobe Acrobat Reader. Можно распечатать и написать ручкой.",
        "Не знаете ответа — пропустите вопрос. Если работу не делаете, так и напишите: «не делаем» — это тоже важный ответ.",
        "Направления идут в порядке меню сайта, каждое начинается с новой страницы. Разделы можно раздать мастерам.",
        "В конце — новые названия страниц: отметьте «согласен» или впишите свой вариант.",
    ]
    if SHORT:
        intro = ["Здесь только главные вопросы: от ответов зависит, какие работы, оборудование и сроки сайт может "
                 "обещать клиентам, и какие картинки останутся на страницах. О ценах анкета не спрашивает."]
        how = how[:2] + ["В конце есть поле для всего, что не вошло в вопросы."]
    story = [Spacer(1, 6), stats, Spacer(1, 14)]
    story += [Paragraph(inline(t), STYLES["body"]) for t in intro]
    story += [Spacer(1, 10), Paragraph("Как заполнять", STYLES["page"]), Spacer(1, 4)]
    story += [Paragraph(inline(t), STYLES["sub"], bulletText="—") for t in how]
    story += [Spacer(1, 14)]
    fields = Table([[labelled_field("Кто заполнил", "cover_name"), labelled_field("Дата", "cover_date")],
                    [labelled_field("Телефон для уточнений", "cover_phone"), labelled_field("Должность", "cover_role")]],
                   colWidths=[(PAGE_W - 2 * MARGIN_X) / 2] * 2)
    fields.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (0, -1), 10),
                                ("RIGHTPADDING", (1, 0), (1, -1), 0), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(fields)
    return story


def question_block(number: int, q: Question, page_name: str) -> Flowable:
    body = [Paragraph(inline(q.text), STYLES["q"])]
    body += [Paragraph(inline(s), STYLES["sub"], bulletText="•") for s in q.subs]
    body += [Paragraph(inline(n), STYLES["note"]) for n in q.notes]
    body += [Spacer(1, 4), AnswerField(f"q{number:03d}", ANSWER_H, f"Ответ на вопрос {number} ({page_name})")]
    t = Table([[Paragraph(f"{number:03d}", STYLES["num"]), body]], colWidths=[NUM_W, PAGE_W - 2 * MARGIN_X - NUM_W])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    return t


def questions_story(directions: list[Direction]) -> tuple[list, int]:
    story, number = [], 0
    for di, d in enumerate(directions, 1):
        kicker = f"// РАЗДЕЛ {di} ИЗ {len(directions)}" if SHORT else f"// НАПРАВЛЕНИЕ {di:02d} ИЗ {len(directions):02d}"
        story += [CondPageBreak(200) if SHORT and di > 1 else PageBreak(), Paragraph(kicker, STYLES["dir_kicker"]),
                  Spacer(1, 4), DirectionHeading(d.name, f"dir{di}"), Spacer(1, 6)]
        for p in d.pages:
            title = "Страница направления" if p.is_direction else p.name
            head = [] if SHORT and p.is_direction else [Paragraph(inline(title), STYLES["page"])]
            if p.path:
                head.append(Paragraph(html.escape("garage.team" + p.path), STYLES["path"]))
            head.append(Spacer(1, 6))
            head += [Paragraph(inline(n), STYLES["note"]) for n in p.notes]
            blocks = []
            for q in p.questions:
                number += 1
                blocks.append(question_block(number, q, p.name))
            story.append(CondPageBreak(90))
            story.append(KeepTogether(head + blocks[:1]))   # a page title never stays alone at the bottom of a sheet
            story += blocks[1:]
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
    story += notes_story()
    return story


def notes_story() -> list:
    notes_heading = Paragraph("Что ещё важно знать", STYLES["h2"])
    return [Spacer(1, 16), notes_heading,
              Paragraph("Всё, что не вошло в вопросы: новые услуги, ошибки на сайте, пожелания.", STYLES["note"]),
              Spacer(1, 6), AnswerField("notes", 150, "Что ещё важно знать")]


def build(out: Path) -> tuple[int, int, int]:
    global HAS_PT_MONO
    source = "owner-questions-short.md" if SHORT else "owner-questions.md"
    directions = parse_questions((SEO / source).read_text(encoding="utf-8"))
    renames = [] if SHORT else parse_renames((SEO / "renames.md").read_text(encoding="utf-8"))
    # same order as the questions: the site menu, a direction first, then its pages
    order = {p.path: i for i, p in enumerate(p for d in directions for p in d.pages)}
    renames.sort(key=lambda r: order.get(r["path"], len(order)))
    with tempfile.TemporaryDirectory() as tmp:
        HAS_PT_MONO = build_fonts(Path(tmp))
        STYLES["sub"].bulletFontName = "Manrope"
        n_questions = sum(len(p.questions) for d in directions for p in d.pages)
        if SHORT:
            COVER["kicker"] = "// КОРОТКАЯ АНКЕТА ВЛАДЕЛЬЦА · GARAGE.TEAM"
        COVER.update(subtitle=f"Автосервис «Гараж», Нижний Новгород · {n_questions} вопросов с полями для ответов",
                     date=date.today().strftime("%d.%m.%Y"))
        toc = TableOfContents(levelStyles=[STYLES["toc0"]], dotsMinLevel=0)
        story = [NextPageTemplate("content")] + cover_story(directions, n_questions, len(renames))
        if not SHORT:
            story += [PageBreak(), Paragraph("// СОДЕРЖАНИЕ", STYLES["dir_kicker"]), Spacer(1, 4),
                      Paragraph("Содержание", STYLES["h2"]), Spacer(1, 6), toc]
        q_story, numbered = questions_story(directions)
        story += q_story + (notes_story() if SHORT else renames_story(renames))
        raw = out.with_suffix(".tmp.pdf")
        Questionnaire(str(raw)).multiBuild(story)
        writer = PdfWriter(clone_from=PdfReader(str(raw)))
        add_field_font(writer, Path(tmp) / "Manrope.ttf")
    # readers draw the typed text themselves, with the field font above, instead of a pre-made appearance
    writer._root_object["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(True)
    writer.page_mode = "/UseOutlines"
    with open(out, "wb") as fh:
        writer.write(fh)
    raw.unlink()
    return numbered, len(renames), len(writer.pages)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--short", action="store_true", help="короткая анкета для владельца")
    args = ap.parse_args()
    global SHORT
    SHORT = args.short
    args.out = args.out or SEO / ("owner-questions-short.pdf" if SHORT else "owner-questions.pdf")
    n, r, pages = build(args.out)
    print(f"записано {args.out.relative_to(ROOT) if args.out.is_relative_to(ROOT) else args.out}: "
          f"{n} вопросов, {r} названий на согласование, {pages} стр.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
