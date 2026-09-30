# -*- coding: utf-8 -*-
"""«Расшифровка кода ошибки» on the computer diagnostics page (block id="kod", right after the lead).

The visitor types an OBD-II trouble code — «P0301», «p0301», «P0 301», Cyrillic «Р0301», several at once — and
src/assets/js/kod.js splits it into its parts after SAE J2012: the system letter, a generic or a manufacturer's code,
the group of systems (P and U codes) and the fault number. For the 100 generic codes in the table below it also shows
the standard meaning retold in plain Russian, what is usually checked and a link to the fitting service page; any
other code gets the structure and «точную расшифровку для вашей машины даст компьютерная диагностика».

Everything the visitor reads is rendered here. The table is the reference list of the block (grouped <details>, so
without JavaScript and for search engines every code is on the page), and kod.js reads the rows back from the page:
there is no second copy of the table and every link carries the base path through D.rebase(). The phrases of the
structure part travel as one JSON object inside the block. explain() below is the Python twin of explain() in kod.js
(the worked example P0301 is rendered with it; tests/test_kod.py compares the two for hundreds of codes).

Wording rules (the owner confirms every text, see notes/perk-kod.md): meanings are the generic SAE definitions only,
«что обычно проверяют» is general knowledge worded as usual practice, never a diagnosis; no prices, no promises, no
safety verdicts — at most «Проверку лучше не откладывать»; nothing leads to the removal or chip-tuning pages. The build
fails on a malformed or repeated code, a page that does not exist, a forbidden page or a link to this page itself.
"""
from __future__ import annotations

import json
import re

from . import data as D
from .icons import icon

esc = D.esc

PAGE = "/services/diagnostika/komputernaa-diagnostika.html"
ANCHOR = "kod"
MAX_CODES = 10                                   # codes decoded from one input; the rest is cut with a note
CODE_RE = re.compile(r"^[PBCU][0-3][0-9A-F]{3}$")

# ---------- service pages the codes link to (short key -> path in data/services.json) ----------
PAGES = {
    "engine": "/services/remont-dvigatela.html",
    "inj": "/services/remont-promyvka-inzektorov-i-monovpryskov.html",
    "plugs": "/services/remont-promyvka-inzektorov-i-monovpryskov/zamena-svecej.html",
    "temp_sensor": "/services/remont-i-promyvka-sistem-ohlazdenia/zamena-datcikov-temperatury-ohlazdausej-zidkosti.html",
    "thermostat": "/services/remont-i-promyvka-sistem-ohlazdenia/zamena-termostata.html",
    "exhaust": "/services/remont-vyhlopnoj-sistemy.html",
    "electric": "/services/remont-elektrooborudovania-avtomobila.html",
    "generator": "/services/remont-elektrooborudovania-avtomobila/remont-generatora.html",
    "tnvd": "/services/remont-tnvd.html",
    "diesel": "/services/remont-dizela.html",
    "diesel_engine": "/services/remont-dizela/remont-dizelnogo-dvigatela.html",
    "turbo": "/services/remont-turbin-i-turbokompressorov.html",
    "akpp": "/services/remont-akpp-i-zamena-masla-v-akpp.html",
    "akpp_diag": "/services/diagnostika/diagnostika-akpp.html",
}
# never a target of a perk (removal, disabling, chip tuning, xenon, inspection): a link here fails the build
FORBIDDEN = ("udalenie", "otklucenie", "cip-tuning", "ksenon", "tehosmotr")

# ---------- the structure of a code (SAE J2012), in plain words ----------
LETTERS = {
    "P": "Powertrain — двигатель, коробка передач и связанные с ними системы",
    "B": "Body — кузов и салон: подушки безопасности, ремни, замки, климат, свет",
    "C": "Chassis — шасси: тормоза и ABS, система стабилизации, рулевое управление, подвеска",
    "U": "Network — сеть: обмен данными между блоками управления",
}
# second character: 0 (and P2, P3400–P3FFF) generic; 1, 2 (and P3000–P33FF) the manufacturer's; B3, C3, U3 reserved
TYPE = {
    "generic": "общий код: по стандарту SAE он значит одно и то же у всех марок",
    "maker": "код производителя: что он значит, решает автопроизводитель",
    "reserved": "запасной диапазон стандарта: такие коды встречаются редко",
    "p3-maker": "код производителя: у кодов на P3 это диапазон P3000–P33FF",
    "p3-generic": "общий код стандарта: у кодов на P3 это диапазон P3400–P3FFF",
}
# third character: the group of systems. Only where the standard fixes it and only the groups known for certain;
# for P1 (the manufacturer's) the standard asks makers to keep the same groups, hence «обычно».
_P0 = {
    "0": "топливо, воздух и контроль выбросов",
    "1": "подача топлива и воздуха",
    "2": "подача топлива и воздуха, цепи форсунок",
    "3": "зажигание и пропуски воспламенения",
    "4": "системы снижения выбросов: EGR, катализатор, пары топлива",
    "5": "скорость, холостой ход и вспомогательные сигналы",
    "6": "блок управления и его выходные цепи",
    "7": "коробка передач",
    "8": "коробка передач",
    "9": "коробка передач",
}
SUB = {
    "P0": {**_P0, "A": "гибридная силовая установка", "B": "гибридная силовая установка", "C": "гибридная силовая установка"},
    "P1": {k: "обычно " + v for k, v in _P0.items()},
    "P2": {"0": _P0["0"], "1": _P0["0"], "2": _P0["0"], "3": _P0["3"], "4": "системы снижения выбросов",
           "5": "вспомогательные сигналы", "6": _P0["6"], "7": _P0["7"], "8": _P0["8"], "A": _P0["1"]},
    "U0": {"0": "электрическая часть сети: провода и шина обмена данными",
           "1": "связь между блоками: обычно один из них перестал выходить на связь",
           "2": "связь между блоками: обычно один из них перестал выходить на связь",
           "3": "программы блоков: несовместимость или сбой программы",
           "4": "данные: блок получил от другого блока неверные сведения"},
}
NUM = {"sub": "номер неисправности в этой группе", "all": "номер неисправности"}
NOTE = {
    "known": "Это общее значение кода по стандарту SAE. Одну и ту же ошибку дают разные причины — какая из них "
             "у вашей машины, покажет диагностика.",
    "maker": "Это код производителя: его значение зависит от марки и модели. Точную расшифровку для вашей машины "
             "даст компьютерная диагностика.",
    "unknown": "Этого кода нет в нашем справочнике. Точную расшифровку для вашей машины даст компьютерная диагностика.",
    "reserved": "Такие коды встречаются редко. Точную расшифровку для вашей машины даст компьютерная диагностика.",
}
ROLES = {"sys": "Система", "type": "Тип кода", "sub": "Группа", "num": "Номер"}
KEYS = {"sys": "система", "type": "тип", "sub": "группа", "num": "номер"}
URGE = "Проверку лучше не откладывать."

# ---------- block texts ----------
TAG = "// расшифровка"
TITLE = "Расшифровка кода ошибки"
INTRO = ("Код ошибки — например, P0301 — читается по знакам: буква называет систему машины, а цифры — тип кода, "
         "группу и номер неисправности.")
INTRO_JS = "Введите свой код: покажем, что он значит и что обычно проверяют при такой ошибке. Можно несколько кодов сразу."
SCREEN = ("OBD-II", "SAE J2012")                 # the status line of the scan tool (decoration)
FIELD = "Код ошибки"
HINT = "Можно несколько кодов через запятую или пробел."
GO = "Расшифровать"
EXAMPLE = "P0301"
EXAMPLES_LABEL = "Например:"
EXAMPLES = ["P0300", "P0171", "P0420", "P0700"]
CTA = "Записаться на компьютерную диагностику"
CHECK_LABEL = "Обычно проверяют:"
LAMP_LINK = "Есть код ошибки? Расшифруйте"     # in the Check Engine card of «Что горит на панели?»
REF_TITLE = "Справочник частых кодов"
REF_INTRO = "Значения — по стандарту SAE, одинаковые для всех марок. Точную причину на конкретной машине покажет диагностика."
REF_INTRO_JS = "Нажмите на код, чтобы разобрать его по знакам."
LEGEND = [
    ("Банк 1", "ряд цилиндров, в котором стоит цилиндр 1. У рядного двигателя ряд один, у V-образного — два."),
    ("Датчик 1 и 2", "датчик кислорода до катализатора и после него."),
    ("«A» и «B»", "у распредвалов: A — обычно впускной, B — выпускной."),
]
# every phrase the script may put on the page; the code table itself is read from the reference rows
TEXTS = {
    "letters": LETTERS, "type": TYPE, "sub": SUB, "num": NUM, "note": NOTE, "roles": ROLES, "keys": KEYS, "urge": URGE,
    "labels": {"example": "Пример", "mean": "Что означает", "check": "Что обычно проверяют", "code": "Код {code}",
               "list": "Коды · {n}", "more": "Показаны первые {max} кодов.", "pick": "Разобрать код {code}"},
    "status": {"maker": "Код производителя", "unknown": "Нет в справочнике", "reserved": "Редкий код"},
    "err": {
        "empty": "Введите код ошибки — например, P0301.",
        "none": "В тексте нет кода ошибки. Код выглядит так: буква и четыре знака, например P0301.",
        "noletter": "«{t}»: в начале кода нужна буква — P, B, C или U, например {fix}.",
        "letter": "«{t}»: код начинается с буквы P, B, C или U.",
        "second": "«{t}»: второй знак кода — только 0, 1, 2 или 3.",
        "chars": "«{t}»: после буквы идут цифры, иногда буквы от A до F.",
        "length": "«{t}»: в коде пять знаков — буква и четыре цифры, например P0301.",
        "other": "«{t}» не похоже на код ошибки.",
    },
    "msg": {"none": "Хочу записаться на компьютерную диагностику.",
            "codes": "Хочу записаться на компьютерную диагностику. Коды ошибок: {codes}."},
    "ctaNote": "Коды {codes} попадут в комментарий к заявке.",
    "live": {"one": "{code}: {text}", "many": "Кодов: {n}. Показан {code}: {text}"},
    "max": MAX_CODES,
}

# ---------- the table: generic codes (SAE J2012), grouped for the reference list ----------
# (code, meaning, what is usually checked, page key or None, urge)
_BANK = {1: "банк 1", 2: "банк 2"}


def _o2() -> list:
    """Oxygen sensors: banks 1–2, sensors 1–2 (before and after the catalyst), six faults each — P0130–P0141, P0150–P0161."""
    faults = [
        ("Неисправность в цепи датчика кислорода", "разъём и проводку датчика, сам датчик"),
        ("Низкое напряжение в цепи датчика кислорода", "проводку на замыкание, сам датчик, герметичность выпуска перед датчиком"),
        ("Высокое напряжение в цепи датчика кислорода", "проводку и разъём, сам датчик, состав смеси"),
        ("Датчик кислорода медленно реагирует", "сам датчик — с пробегом он реагирует медленнее, — герметичность выпуска перед ним"),
        ("Датчик кислорода не подаёт признаков работы", "разъём и проводку, подогрев датчика, сам датчик"),
        ("Неисправность в цепи подогрева датчика кислорода", "предохранитель, разъём и проводку подогрева, сам датчик — нагреватель встроен в него"),
    ]
    where = {1: "до катализатора", 2: "после катализатора"}
    out = []
    # the numbers run as decimals (P0139 is followed by P0140), although a code may hold the letters A–F
    for bank, sensor, first in ((1, 1, 130), (1, 2, 136), (2, 1, 150), (2, 2, 156)):
        for i, (name, what) in enumerate(faults):
            out.append((f"P0{first + i}", f"{name} ({_BANK[bank]}, датчик {sensor} — {where[sensor]})", what, "exhaust", False))
    return out


def _cylinders() -> list:
    return [(f"P030{n}", f"Пропуски воспламенения в цилиндре {n}",
             "свечу и катушку зажигания этого цилиндра, его форсунку и компрессию", "plugs", True) for n in range(1, 9)]


def _knock() -> list:
    """Knock sensor 1 (bank 1 or the only one) P0325–P0328 and sensor 2 (bank 2) P0330–P0333."""
    out = []
    for first, sensor, where in ((325, 1, "банк 1 или единственный датчик"), (330, 2, "банк 2")):
        out += [
            (f"P0{first}", f"Неисправность в цепи датчика детонации {sensor} ({where})", "разъём и проводку, крепление датчика, сам датчик", "electric", False),
            (f"P0{first + 1}", f"Сигнал датчика детонации {sensor} неправдоподобен ({where})", "крепление и сам датчик, проводку, а также посторонние стуки в двигателе", "engine", False),
            (f"P0{first + 2}", f"Слишком низкий сигнал датчика детонации {sensor} ({where})", "разъём и проводку на обрыв, крепление датчика, сам датчик", "electric", False),
            (f"P0{first + 3}", f"Слишком высокий сигнал датчика детонации {sensor} ({where})", "проводку и разъём, сам датчик", "electric", False),
        ]
    return out


_LEAN = "подсос воздуха во впуске, датчик расхода воздуха, давление топлива, форсунки"
_RICH = "форсунки — не подтекают ли, — давление топлива, датчик расхода воздуха, воздушный фильтр"
_CAM = "метки и натяжение цепи или ремня ГРМ — цепь могла растянуться, а ремень перескочить, — датчики коленвала и распредвала, регулятор фаз"
_CAT = "сначала устраняют другие ошибки — пропуски и состав смеси, — затем проверяют датчики кислорода, герметичность выпуска и сам катализатор"
_EGR = "клапан EGR и его каналы — не забиты ли нагаром, — привод клапана и его датчик"
_RATIO = "уровень и состояние масла в коробке, гидроблок и соленоиды, износ фрикционов"

GROUPS = [
    ("sensors", "Датчики и состав смеси", [
        ("P0101", "Датчик расхода воздуха (ДМРВ) показывает неправдоподобные значения", "подсос воздуха после датчика, воздушный фильтр, загрязнение и исправность датчика", "inj", False),
        ("P0102", "Слишком низкий сигнал датчика расхода воздуха (ДМРВ)", "разъём и проводку датчика, его питание, сам датчик", "inj", False),
        ("P0103", "Слишком высокий сигнал датчика расхода воздуха (ДМРВ)", "проводку и массу датчика, сам датчик", "inj", False),
        ("P0106", "Датчик абсолютного давления во впускном коллекторе (ДАД) показывает неправдоподобные значения", "подсос воздуха во впуске, трубку и разъём датчика, сам датчик", "inj", False),
        ("P0107", "Слишком низкий сигнал датчика абсолютного давления (ДАД)", "разъём и проводку, питание датчика, сам датчик", "inj", False),
        ("P0108", "Слишком высокий сигнал датчика абсолютного давления (ДАД)", "проводку и массу датчика, его трубку к коллектору, сам датчик", "inj", False),
        ("P0112", "Слишком низкий сигнал датчика температуры воздуха на впуске: обычно блок видит слишком высокую температуру", "проводку на замыкание, сам датчик — на многих машинах он встроен в датчик расхода воздуха", "inj", False),
        ("P0113", "Слишком высокий сигнал датчика температуры воздуха на впуске: обычно блок видит слишком низкую температуру", "разъём — надет ли он, — проводку на обрыв, сам датчик", "inj", False),
        ("P0117", "Слишком низкий сигнал датчика температуры охлаждающей жидкости: обычно блок видит слишком горячий двигатель", "проводку на замыкание, сам датчик", "temp_sensor", False),
        ("P0118", "Слишком высокий сигнал датчика температуры охлаждающей жидкости: обычно блок видит слишком холодный двигатель", "разъём и проводку на обрыв, сам датчик", "temp_sensor", False),
        ("P0122", "Слишком низкий сигнал датчика «A» положения дроссельной заслонки или педали газа", "разъём и проводку, питание датчика, сам датчик или дроссельный узел", "inj", False),
        ("P0123", "Слишком высокий сигнал датчика «A» положения дроссельной заслонки или педали газа", "проводку и массу датчика, сам датчик или дроссельный узел", "inj", False),
        ("P0128", "Двигатель слишком долго прогревается: охлаждающая жидкость не доходит до рабочей температуры", "в первую очередь термостат — он мог остаться приоткрытым, — затем датчик температуры и уровень антифриза", "thermostat", False),
        ("P0171", "Слишком бедная смесь (банк 1): блок управления добавляет топливо, но не может выровнять состав", _LEAN, "inj", False),
        ("P0172", "Слишком богатая смесь (банк 1): блок управления убавляет топливо, но не может выровнять состав", _RICH, "inj", False),
        ("P0174", "Слишком бедная смесь (банк 2): блок управления добавляет топливо, но не может выровнять состав", _LEAN, "inj", False),
        ("P0175", "Слишком богатая смесь (банк 2): блок управления убавляет топливо, но не может выровнять состав", _RICH, "inj", False),
    ]),
    ("o2", "Датчики кислорода (лямбда-зонды)", _o2()),
    ("ignition", "Пропуски воспламенения и свечи накаливания", [
        ("P0300", "Пропуски воспламенения в нескольких или случайных цилиндрах", "свечи и катушки зажигания, форсунки, подсос воздуха, давление топлива, компрессию", "plugs", True),
        *_cylinders(),
        ("P0380", "Неисправность в цепи свечей накаливания «A» (дизель)", "свечи накаливания, их реле или блок управления, проводку", "diesel_engine", False),
    ]),
    ("timing", "Коленвал, распредвал и детонация", [
        ("P0011", "Распредвал «A» повёрнут раньше заданного, или система изменения фаз работает неправильно (банк 1)", "уровень и состояние масла — регулятор фаз обычно работает от его давления, — клапан регулятора фаз, метки и натяжение цепи или ремня ГРМ", "engine", False),
        ("P0016", "Положение распредвала «A» не согласуется с положением коленвала (банк 1)", _CAM, "engine", False),
        ("P0017", "Положение распредвала «B» не согласуется с положением коленвала (банк 1)", _CAM, "engine", False),
        ("P0018", "Положение распредвала «A» не согласуется с положением коленвала (банк 2)", _CAM, "engine", False),
        ("P0019", "Положение распредвала «B» не согласуется с положением коленвала (банк 2)", _CAM, "engine", False),
        *_knock(),
        ("P0335", "Неисправность в цепи датчика положения коленвала «A»", "разъём и проводку, сам датчик и зубчатый диск, по которому он считывает обороты", "electric", False),
        ("P0340", "Неисправность в цепи датчика положения распредвала «A» (банк 1 или единственный датчик)", "разъём и проводку, сам датчик, метки ГРМ", "electric", False),
    ]),
    ("fuel", "Давление топлива и наддув", [
        ("P0087", "Давление топлива в рампе или системе слишком низкое", "топливный фильтр, подкачивающий насос, насос высокого давления, датчик и регулятор давления", "tnvd", False),
        ("P0088", "Давление топлива в рампе или системе слишком высокое", "регулятор и датчик давления в рампе, у дизеля — дозирующий клапан насоса высокого давления", "tnvd", False),
        ("P0093", "Обнаружена большая утечка в топливной системе", "трубки и соединения высокого давления, обратный слив форсунок, регулятор и датчик давления", "diesel", True),
        ("P0234", "Давление наддува выше допустимого (турбина или компрессор «A»)", "управление турбиной — клапан или привод, — датчик давления наддува и его трубки", "turbo", False),
        ("P0299", "Давление наддува ниже нужного (турбина или компрессор «A»)", "утечки во впуске и интеркулере, патрубки, управление турбиной, саму турбину, датчик давления наддува", "turbo", False),
    ]),
    ("emissions", "EGR, катализатор и пары топлива", [
        ("P0400", "Неисправность потока рециркуляции отработавших газов (EGR «A»)", _EGR, "engine", False),
        ("P0401", "Недостаточный поток рециркуляции отработавших газов (EGR «A»)", _EGR, "engine", False),
        ("P0402", "Избыточный поток рециркуляции отработавших газов (EGR «A»)", "не остался ли клапан EGR открытым, его привод и датчик положения", "engine", False),
        ("P0403", "Неисправность в цепи управления клапаном EGR «A»", "разъём и проводку клапана, сам клапан", "engine", False),
        ("P0404", "Клапан EGR «A» работает вне допустимых пределов", "нагар в клапане, его привод и датчик положения, проводку", "engine", False),
        ("P0420", "Катализатор очищает выхлоп хуже допустимого (банк 1)", _CAT, "exhaust", False),
        ("P0422", "Основной катализатор очищает выхлоп хуже допустимого (банк 1)", _CAT, "exhaust", False),
        ("P0430", "Катализатор очищает выхлоп хуже допустимого (банк 2)", _CAT, "exhaust", False),
        ("P0443", "Неисправность в цепи клапана продувки адсорбера — системы улавливания паров топлива", "разъём и проводку клапана, сам клапан", "electric", False),
        ("P0455", "Большая утечка в системе улавливания паров топлива", "крышку топливного бака — закрыта ли она до щелчка, — шланги и клапаны системы, адсорбер", None, False),
        ("P0456", "Очень маленькая утечка в системе улавливания паров топлива", "уплотнение крышки бака, шланги и соединения системы, клапаны вентиляции", None, False),
    ]),
    ("idle", "Холостой ход, скорость и питание", [
        ("P0500", "Неисправность датчика скорости автомобиля «A»", "датчик скорости и его проводку; на многих машинах скорость берут от датчиков колёс ABS — проверяют и их", "electric", False),
        ("P0505", "Неисправность системы управления холостым ходом", "регулятор холостого хода или электронный дроссель — не загрязнены ли, — подсос воздуха", "inj", False),
        ("P0506", "Обороты холостого хода ниже заданных", "загрязнение дроссельного узла или регулятора холостого хода, воздушный фильтр, подсос воздуха", "inj", False),
        ("P0507", "Обороты холостого хода выше заданных", "подсос воздуха во впуске, загрязнение или износ дроссельного узла и регулятора холостого хода", "inj", False),
        ("P0562", "Низкое напряжение бортовой сети", "заряд и состояние аккумулятора, клеммы, генератор и его ремень", "generator", False),
        ("P0563", "Высокое напряжение бортовой сети", "регулятор напряжения генератора, клеммы и провода массы", "generator", False),
        ("P0606", "Неисправность процессора блока управления", "питание и массу блока управления, его разъёмы, затем сам блок", "electric", False),
    ]),
    ("gearbox", "Коробка передач", [
        ("P0700", "Блок управления коробкой записал неисправность и попросил зажечь Check Engine", "коды в памяти самого блока коробки — P0700 только сообщает, что они там есть", "akpp_diag", False),
        ("P0705", "Неисправность в цепи датчика «A» положения селектора коробки (PRNDL)", "датчик положения селектора, его регулировку и проводку, трос селектора", "akpp_diag", False),
        ("P0715", "Неисправность в цепи датчика «A» скорости входного вала или турбины", "датчик и его проводку, уровень и состояние масла в коробке", "akpp_diag", False),
        ("P0720", "Неисправность в цепи датчика скорости выходного вала", "датчик, его разъём и проводку", "akpp_diag", False),
        ("P0730", "Неверное передаточное отношение: обороты валов коробки не соответствуют включённой передаче", _RATIO, "akpp", False),
        ("P0731", "Неверное передаточное отношение на 1-й передаче", _RATIO, "akpp", False),
        ("P0732", "Неверное передаточное отношение на 2-й передаче", _RATIO, "akpp", False),
        ("P0733", "Неверное передаточное отношение на 3-й передаче", _RATIO, "akpp", False),
        ("P0734", "Неверное передаточное отношение на 4-й передаче", _RATIO, "akpp", False),
        ("P0740", "Неисправность в цепи клапана блокировки гидротрансформатора", "проводку и разъём клапана, сам клапан, уровень и состояние масла", "akpp", False),
        ("P0750", "Неисправность клапана переключения передач «A»", "проводку и разъём клапана (соленоида), сам клапан, масло в коробке", "akpp", False),
    ]),
]
# «банк 1», «датчик 2», «цилиндре 3», «детонации 1»: the number never starts a line on its own
_NUMBERED = re.compile(r"\b(банк|датчик|цилиндре|детонации) (\d)")
GROUPS = [(key, title, [(c, _NUMBERED.sub("\\1\u00a0\\2", n), k, p, u) for c, n, k, p, u in rows]) for key, title, rows in GROUPS]
CODES = {c: {"name": n, "check": k, "page": p, "urge": u} for _, _, rows in GROUPS for c, n, k, p, u in rows}


# ---------- checks ----------
def _page(key: str | None) -> tuple[str | None, str | None]:
    """(href, label) of a service page, or (None, None). A missing, forbidden or self page is a build error."""
    if key is None:
        return None, None
    path = PAGES[key]
    svc = D.BY_PATH.get(path)
    if svc is None:
        raise ValueError(f"kod: нет страницы услуги {path} ({key})")
    if any(bad in path for bad in FORBIDDEN):
        raise ValueError(f"kod: расшифровка не должна вести на {path}")
    if path == PAGE:
        raise ValueError(f"kod: ссылка на саму страницу диагностики ({key})")
    return path, svc.get("nav_name") or svc["h1"]


def check() -> None:
    """Every rule of the table; raises ValueError. Runs on every build (block() and lamp_link() call it)."""
    rows = [r for _, _, group in GROUPS for r in group]
    codes = [r[0] for r in rows]
    if not 70 <= len(codes) <= 100:
        raise ValueError(f"kod: в справочнике должно быть 70–100 кодов, а не {len(codes)}")
    bad = [c for c in codes if not CODE_RE.match(c)]
    if bad:
        raise ValueError(f"kod: неверный код {bad}")
    if len(set(codes)) != len(codes):
        raise ValueError(f"kod: код повторяется {sorted({c for c in codes if codes.count(c) > 1})}")
    if len({g for g, _, _ in GROUPS}) != len(GROUPS):
        raise ValueError("kod: у групп справочника должны быть разные ключи")
    for code, name, what, page, _ in rows:
        if kind(code) != "generic":
            raise ValueError(f"kod: {code} — в справочнике только общие коды SAE")
        if not name.strip() or not what.strip() or name.rstrip()[-1] in ".;" or what.rstrip()[-1] in ".;":
            raise ValueError(f"kod: {code}: пустой текст или точка в конце")
        _page(page)
    for key in PAGES:
        _page(key)
    if EXAMPLE not in CODES or any(e not in CODES for e in EXAMPLES):
        raise ValueError("kod: пример и подсказки должны быть в справочнике")
    if D.BY_PATH.get(PAGE) is None:
        raise ValueError(f"kod: нет страницы {PAGE}")


# ---------- the decoder (the same rules as kind() and explain() in src/assets/js/kod.js) ----------
def kind(code: str) -> str:
    """generic | maker | reserved, by the second character (P3: by the third as well)."""
    letter, second = code[0], code[1]
    if letter == "P":
        if second in "02":
            return "generic"
        if second == "1":
            return "maker"
        return "maker" if int(code[2], 16) <= 3 else "generic"        # P3000–P33FF maker, P3400–P3FFF generic
    if second == "0":
        return "generic"
    return "reserved" if second == "3" else "maker"


def entry(code: str) -> dict | None:
    """The row of the table as kod.js reads it from the page (href without the base path)."""
    e = CODES.get(code)
    if not e:
        return None
    href, label = _page(e["page"])
    return {"name": e["name"], "check": e["check"], "urge": e["urge"], "href": href, "label": label}


def explain(code: str) -> dict:
    k = kind(code)
    type_text = TYPE[f"p3-{k}"] if code.startswith("P3") else TYPE[k]
    sub = SUB.get(code[:2], {}).get(code[2], "")
    parts = [["sys", code[0], LETTERS[code[0]]], ["type", code[1], type_text]]
    if sub:
        parts += [["sub", code[2], sub], ["num", code[3:], NUM["sub"]]]
    else:
        parts.append(["num", code[2:], NUM["all"]])
    e = entry(code)
    note = NOTE["known"] if e else NOTE["unknown" if k == "generic" else k]
    return {"code": code, "kind": k, "parts": parts, "entry": e, "note": note}


def model() -> dict:
    """What kod.js works with: the phrases and the table as it reads it from the page (tests feed it to node)."""
    check()
    return {"texts": TEXTS, "codes": {c: entry(c) for c in CODES}}


def cta_message(codes: list) -> str:
    return TEXTS["msg"]["codes"].format(codes=", ".join(codes)) if codes else TEXTS["msg"]["none"]


# ---------- markup ----------
def _plural(n: int, one: str, few: str, many: str) -> str:
    n = abs(n) % 100
    if 11 <= n <= 19:
        return many
    n %= 10
    return one if n == 1 else few if 2 <= n <= 4 else many


def card(code: str, label: str = "") -> str:
    """One decoded code; kod.js builds the same markup (render → card()) for the visitor's codes."""
    x = explain(code)
    cells = []
    for role, chars, _ in x["parts"]:
        cells += [f'<span class="kod-lcd__cell" data-role="{role}">{esc(ch)}</span>' for ch in chars]
    keys = "".join(f'<span class="kod-lcd__key" data-role="{role}" style="--n:{len(chars)}">{esc(KEYS[role])}</span>'
                   for role, chars, _ in x["parts"])
    parts = "".join(f'<div class="kod-part" data-role="{role}"><dt>{esc(ROLES[role])}</dt>'
                    f'<dd><b class="kod-part__ch">{esc(chars)}</b><span>{esc(text)}</span></dd></div>'
                    for role, chars, text in x["parts"])
    e = x["entry"]
    labels = TEXTS["labels"]
    if e:
        link = (f'<a class="link-arrow link-arrow--inline kod-card__link" href="{e["href"]}">{esc(e["label"])} {icon("arrow")}</a>'
                if e["href"] else "")
        urge = f'<p class="kod-card__urge">{icon("hazard", "ic--sm")}<span>{esc(URGE)}</span></p>' if e["urge"] else ""
        text = (f'<p class="kod-card__label">{esc(labels["mean"])}</p><p class="kod-card__name">{esc(e["name"])}</p>'
                f'<p class="kod-card__label">{esc(labels["check"])}</p><p class="kod-card__check">{esc(e["check"])}</p>'
                f'{urge}{link}<p class="kod-card__note">{icon("info", "ic--sm")}<span>{esc(x["note"])}</span></p>')
    else:
        text = f'<p class="kod-card__label">{esc(labels["mean"])}</p><p class="kod-card__none">{esc(x["note"])}</p>'
    head = f'<p class="kod-card__tag">{esc(label)}</p>' if label else ""
    return f"""<div class="kod-card" data-kind="{x['kind']}" data-known="{'1' if e else '0'}">
          <div class="kod-card__id">{head}
            <div class="kod-lcd" role="img" aria-label="{esc(labels['code'].format(code=code))}"><div class="kod-lcd__cells">{"".join(cells)}</div><div class="kod-lcd__keys" aria-hidden="true">{keys}</div></div>
            <dl class="kod-parts">{parts}</dl>
          </div>
          <div class="kod-card__text">{text}</div>
        </div>"""


def _row(code: str) -> str:
    e = entry(code)
    link = (f'<a class="link-arrow link-arrow--inline kod-row__link" href="{e["href"]}" data-f="link">{esc(e["label"])} {icon("arrow", "ic--sm")}</a>'
            if e["href"] else "")
    urge = f'<p class="kod-row__urge" data-f="urge">{esc(URGE)}</p>' if e["urge"] else ""
    return (f'<div class="kod-row" id="kod-{code.lower()}" data-code="{code}"><dt class="kod-row__code">{code}</dt>'
            f'<dd class="kod-row__body"><p class="kod-row__name" data-f="name">{esc(e["name"])}</p>'
            f'<p class="kod-row__check"><span class="kod-row__lbl">{esc(CHECK_LABEL)}</span> <span data-f="check">{esc(e["check"])}</span></p>'
            f'{urge}{link}</dd></div>')


def _reference() -> str:
    groups = []
    for key, title, rows in GROUPS:
        n = len(rows)
        groups.append(f"""<details class="kod-group" id="kod-g-{key}">
          <summary class="kod-group__sum"><span class="kod-group__title">{esc(title)}</span><span class="kod-group__n">{n} {_plural(n, "код", "кода", "кодов")}</span>{icon("plus", "kod-group__ic")}</summary>
          <dl class="kod-rows">{"".join(_row(r[0]) for r in rows)}</dl>
        </details>""")
    legend = "".join(f"<li><b>{esc(term)}</b> — {esc(text)}</li>" for term, text in LEGEND)
    return f"""<div class="kod-ref">
      <h3 class="kod-ref__title">{esc(REF_TITLE)}</h3>
      <p class="kod-ref__intro">{esc(REF_INTRO)} <span class="kod__js">{esc(REF_INTRO_JS)}</span></p>
      <ul class="kod-ref__legend">{legend}</ul>
      <div class="kod-ref__groups">{"".join(groups)}</div>
    </div>"""


def _texts_json() -> str:
    # inert data for kod.js; «</» never appears in the phrases, but a </script> inside JSON would end the element
    return json.dumps(TEXTS, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def lamp_link() -> str:
    """The line in the Check Engine card of «Что горит на панели?» (build/pribory.py) that leads here."""
    check()
    return (f'<p class="lamp-card__kod"><a class="link-arrow link-arrow--inline" href="{PAGE}#{ANCHOR}">'
            f'{esc(LAMP_LINK)} {icon("arrow")}</a></p>')


def block(svc: dict) -> str:
    """The decoder on the computer diagnostics page; empty for every other service page."""
    if svc["path"] != PAGE:
        return ""
    check()
    preset = esc(json.dumps({"message": cta_message([])}, ensure_ascii=False))
    examples = "".join(f'<button class="kod-chip" type="button" data-kod-example="{c}">{c}</button>' for c in EXAMPLES)
    # the section itself never moves (no .reveal on it): a link to #kod lands exactly on the title
    return f"""<section class="kod" id="{ANCHOR}" aria-labelledby="kod-title" data-kod>
      <div class="block-title"><span class="tag-num">{esc(TAG)}</span><h2 class="h3" id="kod-title">{esc(TITLE)}</h2></div>
      <p class="kod__intro">{esc(INTRO)} <span class="kod__js">{esc(INTRO_JS)}</span></p>
      <div class="kod-scan reveal">
        <div class="kod-scan__bar" aria-hidden="true"><span class="kod-scan__led"></span><span>{esc(SCREEN[0])}</span><span class="kod-scan__std">{esc(SCREEN[1])}</span></div>
        <form class="kod-form" data-kod-form novalidate>
          <label class="kod-form__label" for="kod-input">{esc(FIELD)}</label>
          <div class="kod-form__row">
            <input class="kod-form__input" id="kod-input" name="kod" type="text" inputmode="text" autocomplete="off" autocorrect="off" autocapitalize="characters" spellcheck="false" enterkeyhint="go" maxlength="160" placeholder="{EXAMPLE}" aria-describedby="kod-hint kod-errors" data-kod-input>
            <button class="btn kod-form__go" type="submit">{icon("search")} {esc(GO)}</button>
          </div>
          <p class="kod-form__hint" id="kod-hint">{esc(HINT)}</p>
          <ul class="kod-form__errors" id="kod-errors" data-kod-errors hidden></ul>
          <div class="kod-examples"><span class="kod-examples__label">{esc(EXAMPLES_LABEL)}</span>{examples}</div>
        </form>
        <div class="kod-out" data-kod-out tabindex="-1">
          {card(EXAMPLE, TEXTS["labels"]["example"])}
        </div>
        <div class="kod-cta">
          <button class="btn btn--primary" type="button" data-modal="call" data-preset="{preset}" data-kod-cta>{icon("phone")} {esc(CTA)}</button>
          <p class="kod-cta__note" data-kod-cta-note hidden></p>
        </div>
        <p class="sr-only" aria-live="polite" data-kod-live></p>
      </div>
      {_reference()}
      <script type="application/json" data-kod-texts>{_texts_json()}</script>
    </section>"""
