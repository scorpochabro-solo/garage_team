# -*- coding: utf-8 -*-
"""«Что горит на приборной панели»: a warning-light cluster on the home page (section #pribory).

Every explanation is rendered here, on the server: without JavaScript the section is a readable list of cards and
search engines see all of the text; src/assets/js/pribory.js turns it into the panel (one card at a time, the
ignition bulb check). The texts are general knowledge written cautiously — «обычно», «точнее скажет диагностика» —
and nothing in them is about the business itself. Links go only to existing service pages (checked below, at build
time) and never to the «удаление» pages of the chip-tuning section: the particulate filter card leads to diagnostics
and diesel repair.

The symbols are drawn after the standard dashboard pictograms (ISO 2575) on a 32×32 grid, as line icons: stroke
«currentColor», so the same <symbol> is dim on the unlit panel, coloured when lit and coloured in the card.
"""
import json
import math

from . import data as D
from . import kod
from .icons import icon

esc = D.esc

# ---------- symbols (32×32, stroke-based; filled details use currentColor) ----------
_S = 'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
_F = 'fill="currentColor" stroke="none"'
# brake-style brackets around a 16,16 circle: the pads of a drum brake in the standard pictogram
_BRACKETS = '<path d="M7.6 6.6A12.6 12.6 0 0 0 7.6 25.4M24.4 6.6A12.6 12.6 0 0 1 24.4 25.4"/>'


def _coil(left=5, right=27, top=7, mid=20, loops=3, size=3.4, steps=20):
    """The glow-plug pictogram: a wire comes down at the left, runs along the bottom in loops (a prolate trochoid)
    and goes up at the right. Returned as path data."""
    r = 2                                                   # radius of the two bottom corners
    bottom = mid + size
    a = (right - left - 2 * r) / (2 * math.pi * loops)      # advance per radian; size > a is what makes the loops
    x0 = left + r - a * math.pi
    pts = []
    for i in range(1, steps * loops + 1):
        t = math.pi + 2 * math.pi * i / steps
        pts.append(f"L{x0 + a * t - size * math.sin(t):.2f} {mid - size * math.cos(t):.2f}")
    return (f"M{left} {top}V{bottom - r}Q{left} {bottom} {left + r} {bottom}" + "".join(pts)
            + f"Q{right} {bottom} {right} {bottom - r}V{top}")


SYMBOLS = {
    # engine outline: filler cap, block, the pulley stub on the left and the flared housing on the right
    "engine": f'<g {_S}><path d="M10.5 6.5h7M14 6.5V10"/><path d="M8 13l3-3h10v4h2.5l4-3.5v13l-4-3.5H21v4.5H8z"/><path d="M8 17H4.5M4.5 13.5v7"/></g>',
    # oil can with the drop from its spout
    "oil": f'<g {_S}><path d="M9 14h10l4 3.5 6.5-3.5"/><path d="M23 17.5 21.5 24H9V14"/><path d="M9 15H5v4.5L9 21"/><path d="M13.5 14v-3.5M11 10.5h5"/></g>'
           f'<path {_F} d="M28.4 17.6c1 1.4 1.6 2.3 1.6 3.1a1.6 1.6 0 0 1-3.2 0c0-.8.6-1.7 1.6-3.1z"/>',
    # battery with its terminals, minus and plus
    "battery": f'<g {_S}><rect x="4" y="10" width="24" height="15" rx="1.5"/><path d="M8.5 10V7.5h3.5V10M20 10V7.5h3.5V10"/><path d="M8 17.5h5M19 17.5h5M21.5 15v5"/></g>',
    # thermometer standing in the coolant: the top wave is broken by the bulb
    "coolant": f'<g {_S}><path d="M16 4.5v13"/><path d="M16 6.5h3.5M16 10h3.5M16 13.5h2.5"/><path d="M3.5 22.5c1.4-1.2 2.8-1.2 4.2 0s2.8 1.2 4.2 0M20.1 22.5c1.4 1.2 2.8 1.2 4.2 0s2.8-1.2 4.2 0"/>'
               f'<path d="M3.5 27.5c1.4-1.2 2.8-1.2 4.2 0s2.8 1.2 4.2 0 2.8-1.2 4.2 0 2.8 1.2 4.2 0 2.8-1.2 4.2 0 2.8 1.2 4.2 0"/></g>'
               f'<circle {_F} cx="16" cy="20.4" r="2.8"/>',
    # brake system: «(!)»
    "brake": f'<g {_S}><circle cx="16" cy="16" r="8.2"/>{_BRACKETS}<path d="M16 11.5v5.5"/></g><circle {_F} cx="16" cy="20.3" r="1.25"/>',
    # parking brake: «(P)»
    "park": f'<g {_S}><circle cx="16" cy="16" r="8.2"/>{_BRACKETS}<path d="M13.8 20.5v-9h3.1a2.6 2.6 0 0 1 0 5.2h-3.1"/></g>',
    # ABS: the letters in the brake circle
    "abs": f'<g {_S}><circle cx="16" cy="16" r="9.2"/><path d="M6.8 5.6A13.8 13.8 0 0 0 6.8 26.4M25.2 5.6A13.8 13.8 0 0 1 25.2 26.4"/></g>'
           f'<text x="16" y="18.6" text-anchor="middle" font-family="Manrope, system-ui, sans-serif" font-weight="800" font-size="7.4" letter-spacing="-.1" fill="currentColor">ABS</text>',
    # airbag: a seated passenger and the inflated bag in front of him
    "airbag": f'<g {_S}><circle cx="9.3" cy="11.6" r="5.6"/><path d="M24.4 9 22.7 22.8H14"/></g>'
              f'<path fill="none" stroke="currentColor" stroke-width="3.3" stroke-linecap="round" stroke-linejoin="round" d="M19.6 11.2 18.6 18.9H12.2L11 25.6"/>'
              f'<circle {_F} cx="20.6" cy="6.6" r="2.7"/>',
    # stability control: the car from behind and its skid marks
    "esp": f'<g {_S}><path d="M7 19.5v-4.3c0-.9.5-1.6 1.3-2L10.4 9c.3-.6.9-1 1.6-1h8c.7 0 1.3.4 1.6 1l2.1 4.2c.8.4 1.3 1.1 1.3 2v4.3z"/><path d="M11 13.2h10"/>'
           f'<path d="M8.5 19.5V22M23.5 19.5V22"/><path d="M12 23.2c-2.4 1.4 2.4 3.3 0 5.3M20 23.2c-2.4 1.4 2.4 3.3 0 5.3"/></g>',
    # tyre pressure: the tyre in section with the tread below, «!» inside
    "tpms": f'<g {_S}><path d="M10 6.5 8.2 8.2c-3 4-3 11.5.3 15.8h15c3.3-4.3 3.3-11.8.3-15.8L22 6.5"/><path d="M10.5 24v2.5M14 24v2.5M18 24v2.5M21.5 24v2.5"/><path d="M16 10.5v6.5"/></g>'
            f'<circle {_F} cx="16" cy="20.2" r="1.25"/>',
    # electric power steering: the wheel and «!»
    "eps": f'<g {_S}><circle cx="13" cy="16" r="9"/><circle cx="13" cy="16" r="2.6"/><path d="M4 16h6.4M15.6 16H22M13 18.6V25"/><path d="M28 9.5v8"/></g>'
           f'<circle {_F} cx="28" cy="21.6" r="1.25"/>',
    # diesel glow plugs: the heating coil between two leads
    "glow": f'<path {_S} d="{_coil()}"/>',
    # diesel particulate filter: the housing with soot inside
    "dpf": f'<g {_S}><path d="M7.5 10.5l3-3h11l3 3v11l-3 3h-11l-3-3z"/><path d="M2.5 16h5M24.5 16h5"/></g>'
           + "".join(f'<circle {_F} cx="{x}" cy="{y}" r="1.2"/>' for y in (12, 16, 20) for x in (12, 16, 20)),
    # service due: an open-end spanner
    "service": f'<g {_S} transform="rotate(-45 16 16)"><path d="M7 14h11.4a5.5 5.5 0 0 1 10.2 0h-5.6v4h5.6a5.5 5.5 0 0 1-10.2 0H7a2 2 0 0 1 0-4z"/></g>',
    # exterior bulb failure: a bulb with «!» and its light
    "bulb": f'<g {_S}><path d="M12.2 21.5c-2.3-1.6-3.7-4-3.7-6.8a7.5 7.5 0 0 1 15 0c0 2.8-1.4 5.2-3.7 6.8v1.8h-7.6z"/><path d="M12.8 26.2h6.4"/><path d="M16 11v5"/>'
            f'<path d="M4 14.7h1.6M26.4 14.7H28M6.8 6.2l1.2 1.1M25.2 6.2 24 7.3M16 2.5v1.6"/></g><circle {_F} cx="16" cy="19" r="1.15"/>',
    # high beam: the lamp and straight beams
    "beam": f'<g {_S}><path d="M17.5 7.5c6 0 10 3.6 10 8.5s-4 8.5-10 8.5z"/><path d="M4 9.5h9.5M4 14h9.5M4 18h9.5M4 22.5h9.5"/></g>',
}

# ---------- what a colour means ----------
# tone: (colour in the card, legend line). Green and blue are the same kind of lamp, so the legend names them together.
TONES = {
    "red": ("Красный", "остановитесь, когда это безопасно, и выясните причину"),
    "amber": ("Жёлтый", "проверьте в ближайшее время"),
    "blue": ("Синий", "информация: система включена, это не неисправность"),
}
LEGEND = [("red", "Красный", TONES["red"][1]), ("amber", "Жёлтый", TONES["amber"][1]),
          ("blue", "Зелёный или синий", "информация: система включена")]

# ---------- the lamps, in panel order (four rows of four) ----------
# name: card title; short: the cluster screen and the call-back message; look: the symbol in words (for the no-JS list,
# screen readers and search); off: ms the lamp stays lit after the others at the end of the bulb check (the airbag lamp
# finishes its self-test last, as in a real car); check=False: not lit in the bulb check (a real car does not light
# the high-beam indicator at ignition). cta / message replace the default «Записаться на диагностику».
LAMPS = [
    {"key": "engine", "tone": "amber", "name": "Check Engine", "short": "Check Engine",
     "look": "контур двигателя", "off": 0,
     "means": "Блок управления двигателем записал ошибку. Причины бывают разные — от датчика до пропусков зажигания, "
              "и по самой лампе их не отличить.",
     "todo": "Если лампа горит ровно, а машина едет как обычно, до сервиса можно доехать, но с диагностикой не тяните. "
             "Если лампа мигает — это серьёзнее: обычно так двигатель сообщает о пропусках зажигания, от которых страдает "
             "катализатор. Снизьте нагрузку и скорость и не откладывайте диагностику, а если мотор заметно троит, "
             "дальше лучше не ехать.",
     "links": ["/services/diagnostika/komputernaa-diagnostika.html",
               "/services/remont-promyvka-inzektorov-i-monovpryskov/zamena-svecej.html"],
     "kod": True},                                # «Есть код ошибки? Расшифруйте» → the decoder (build/kod.py)
    {"key": "oil", "tone": "red", "name": "Давление масла", "short": "Давление масла", "look": "маслёнка с каплей", "off": 60,
     "means": "Давление масла в двигателе упало ниже нормы: масла мало, неисправен масляный насос или датчик. "
              "Без смазки детали двигателя можно повредить за считанные минуты.",
     "todo": "Остановитесь в безопасном месте и заглушите двигатель. Через несколько минут проверьте уровень масла щупом. "
             "Если масла мало — долейте; если уровень в норме, а лампа горит, ехать дальше не стоит: лучше вызвать эвакуатор.",
     "links": ["/services/remont-promyvka-inzektorov-i-monovpryskov/zamer-davlenia-masla.html",
               "/services/remont-dvigatela/zamena-masla-v-dvigatele.html",
               "/services/remont-dvigatela/ustranenie-teci-masla.html"]},
    {"key": "battery", "tone": "red", "name": "Зарядка аккумулятора", "short": "Зарядка аккумулятора",
     "look": "аккумулятор с плюсом и минусом", "off": 60,
     "means": "Генератор перестал заряжать аккумулятор. Обычно причина в ремне генератора, самом генераторе или проводке. "
              "Машина едет на запасе батареи, и его хватит ненадолго.",
     "todo": "Выключите всё лишнее — обогрев, кондиционер, мультимедиа — и ближайшим путём поезжайте в сервис, не глуша "
             "двигатель: он может больше не завестись. Если одновременно растёт температура двигателя — остановитесь: "
             "на многих моторах тот же ремень вращает помпу.",
     "links": ["/services/remont-elektrooborudovania-avtomobila/remont-generatora.html",
               "/services/remont-dvigatela/zamena-remna-generatora.html"]},
    {"key": "coolant", "tone": "red", "name": "Перегрев двигателя", "short": "Перегрев двигателя",
     "look": "термометр в волнах", "off": 0,
     "means": "Двигатель перегревается: охлаждающей жидкости мало или она плохо циркулирует — например, из-за термостата, "
              "помпы или вентилятора радиатора.",
     "todo": "Остановитесь, когда это безопасно, и заглушите двигатель. Не открывайте крышку расширительного бачка на горячем "
             "моторе: жидкость под давлением может обжечь. Уровень антифриза проверьте, когда двигатель остынет, и не "
             "ездите с перегревом — от него страдают головка блока и её прокладка.",
     "note": "На некоторых машинах этот значок бывает синим: двигатель ещё не прогрелся. Это не неисправность.",
     "links": ["/services/remont-i-promyvka-sistem-ohlazdenia.html",
               "/services/remont-i-promyvka-sistem-ohlazdenia/zamena-termostata.html",
               "/services/remont-i-promyvka-sistem-ohlazdenia/zamena-motora-radiatora.html"]},
    {"key": "brake", "tone": "red", "name": "Тормозная система", "short": "Тормозная система",
     "look": "восклицательный знак в круге и скобках", "off": 120,
     "means": "Возможные причины: затянут стояночный тормоз, в бачке мало тормозной жидкости, на некоторых машинах — "
              "износ колодок.",
     "todo": "Проверьте, полностью ли отпущен стояночный тормоз. Если значок не гаснет, остановитесь и посмотрите уровень "
             "тормозной жидкости. Если педаль стала мягкой или проваливается, ехать дальше нельзя.",
     "links": ["/services/diagnostika/diagnostika-tormoznoj-sistemy.html",
               "/services/remont-zamena-regulirovka-prokacka-tormozov.html",
               "/services/remont-zamena-regulirovka-prokacka-tormozov/zamena-kolodok.html"]},
    {"key": "abs", "tone": "amber", "name": "ABS", "short": "ABS",
     "look": "буквы ABS в круге и скобках", "off": 180,
     "means": "Антиблокировочная система отключилась из-за неисправности — часто это датчик скорости колеса или его "
              "проводка. Обычные тормоза работают, но при резком торможении колёса могут заблокироваться.",
     "todo": "Тормозите заранее и плавно, особенно на мокрой и скользкой дороге, и запишитесь на диагностику. Если вместе "
             "с ABS горит красный «(!)» — остановитесь: тормоза могут работать хуже.",
     "links": ["/services/diagnostika/diagnostika-tormoznoj-sistemy.html",
               "/services/diagnostika/komputernaa-diagnostika.html"]},
    {"key": "park", "tone": "red", "name": "Стояночный тормоз", "short": "Стояночный тормоз",
     "look": "буква P в круге и скобках", "off": 120,
     "means": "Стояночный тормоз затянут. Если значок горит, когда тормоз отпущен, он мог отойти не до конца, а на "
              "машинах с кнопкой вместо рычага может быть неисправен электропривод.",
     "todo": "Отпустите стояночный тормоз и убедитесь, что значок погас. Если он горит в движении, остановитесь: езда "
             "с подтянутым тормозом перегревает колодки и диски.",
     "links": ["/services/remont-zamena-regulirovka-prokacka-tormozov/zamena-trosa-rucnika.html",
               "/services/remont-zamena-regulirovka-prokacka-tormozov/zamena-kolodok-rucnika.html"]},
    {"key": "airbag", "tone": "red", "name": "Подушки безопасности", "short": "Подушки безопасности",
     "look": "сидящий человек и круг перед ним", "off": 520,
     "means": "Система подушек безопасности нашла у себя неисправность. При аварии подушки и преднатяжители ремней "
              "могут не сработать.",
     "todo": "Машина едет как обычно, но защищает хуже — не откладывайте диагностику. Часто причина в разъёме под "
             "сиденьем или в шлейфе под рулём, но точнее скажет считывание ошибок.",
     "links": ["/services/diagnostika/komputernaa-diagnostika.html",
               "/services/remont-elektrooborudovania-avtomobila/remont-elektroprovodki.html"]},
    {"key": "esp", "tone": "amber", "name": "Система стабилизации (ESP)", "short": "Стабилизация ESP",
     "look": "машина с извилистыми следами", "off": 180,
     "means": "Если значок коротко мигает в движении, система работает: машину начало заносить или колёса буксуют. "
              "Если горит постоянно — система выключена кнопкой или неисправна.",
     "todo": "Мигает — сбросьте скорость и двигайтесь плавнее. Горит постоянно — проверьте, не выключили ли систему "
             "кнопкой; если нет, запишитесь на диагностику и пока ведите машину аккуратнее.",
     "links": ["/services/diagnostika/komputernaa-diagnostika.html",
               "/services/diagnostika/diagnostika-tormoznoj-sistemy.html"]},
    {"key": "tpms", "tone": "amber", "name": "Давление в шинах", "short": "Давление в шинах",
     "look": "шина в разрезе с восклицательным знаком", "off": 240,
     "means": "Давление в одной или нескольких шинах ниже нормы — из-за прокола, похолодания или естественной утечки. "
              "Если значок сначала мигает около минуты, а потом горит, обычно это неисправность самой системы контроля.",
     "todo": "Осмотрите колёса и проверьте давление манометром; нужные значения указаны на табличке в проёме двери или "
             "на лючке бензобака. После подкачки на некоторых машинах систему нужно сбросить — как, написано в инструкции.",
     "links": ["/services/sinomontaz.html"]},
    {"key": "eps", "tone": "amber", "name": "Электроусилитель руля", "short": "Усилитель руля",
     "look": "руль с восклицательным знаком", "off": 90,
     "means": "Неисправность электроусилителя: руль может стать заметно тяжелее, особенно на малой скорости и при парковке.",
     "todo": "Двигайтесь аккуратно и будьте готовы к тяжёлому рулю. Иногда значок загорается после просадки напряжения — "
             "например, после запуска «от прикуривателя» — и гаснет после перезапуска двигателя. Если не гаснет, нужна "
             "диагностика.",
     "links": ["/services/diagnostika/komputernaa-diagnostika.html",
               "/services/remont-elektrooborudovania-avtomobila.html"]},
    {"key": "bulb", "tone": "amber", "name": "Неисправность внешних ламп", "short": "Перегорела лампа",
     "look": "лампочка с восклицательным знаком", "off": 30,
     "means": "Не горит одна из внешних ламп: стоп-сигнал, поворотник, габарит или ближний свет. Иногда значок "
              "загорается после установки светодиодных ламп: блок управления считает их перегоревшими.",
     "todo": "Включите свет и обойдите машину; стоп-сигналы удобно проверить с помощником. Если новая лампа тоже не "
             "горит, причина может быть в предохранителе, разъёме или проводке.",
     "links": ["/services/remont-elektrooborudovania-avtomobila/zamena-lampocek-osvesenia.html",
               "/services/remont-elektrooborudovania-avtomobila/remont-elektroprovodki.html"]},
    {"key": "glow", "tone": "amber", "name": "Свечи накаливания (дизель)", "short": "Свечи накаливания",
     "look": "спираль между двумя выводами", "off": 380,
     "means": "На дизеле значок загорается при включении зажигания: свечи прогревают камеры сгорания перед пуском. Если он "
              "мигает в движении или горит после запуска, на многих машинах так блок управления сообщает о неисправности "
              "двигателя.",
     "todo": "Перед пуском дождитесь, пока значок погаснет, особенно в мороз. Если он мигает или не гаснет после запуска, "
             "запишитесь на диагностику: причина может быть в свечах, их реле или системе управления двигателем.",
     "links": ["/services/remont-dizela/remont-dizelnogo-dvigatela.html",
               "/services/diagnostika/komputernaa-diagnostika.html"]},
    {"key": "dpf", "tone": "amber", "name": "Сажевый фильтр (дизель)", "short": "Сажевый фильтр",
     "look": "фильтр с точками внутри", "off": 0,
     "means": "Сажевый фильтр дизеля забился и не успевает очищаться сам — так бывает, если машина ездит в основном "
              "короткими поездками по городу.",
     "todo": "Если позволяет дорога, проедьте 15–20 минут за городом с ровной скоростью: на многих машинах этого хватает, "
             "чтобы фильтр очистился. Если значок не гаснет или загорелся вместе с Check Engine, нужна диагностика.",
     # diagnostics and diesel repair only: never the «удаление» pages (see _links)
     "links": ["/services/diagnostika/komputernaa-diagnostika.html", "/services/remont-dizela.html"]},
    {"key": "service", "tone": "amber", "name": "Пора на плановое ТО", "short": "Пора на ТО", "look": "гаечный ключ", "off": 300,
     "means": "Напоминание о плановом обслуживании: подошёл срок по пробегу или по времени. Это не неисправность.",
     "todo": "Запишитесь на ТО в ближайшее время. После обслуживания напоминание сбрасывают — на многих машинах через "
             "меню или сканером.",
     "links": ["/services/planovoe-to.html", "/services/remont-dvigatela/zamena-masla-v-dvigatele.html"],
     "cta": "Записаться на ТО", "message": "Горит индикатор «Пора на ТО». Хочу записаться на плановое ТО."},
    {"key": "beam", "tone": "blue", "name": "Дальний свет", "short": "Дальний свет", "look": "фара с прямыми лучами",
     "off": 0, "check": False,
     "means": "Включён дальний свет — значок просто напоминает об этом.",
     "todo": "Переключайтесь на ближний, когда навстречу едут машины или вы догоняете попутную. Если встречные моргают "
             "вам и при ближнем свете, возможно, фары светят слишком высоко — их стоит отрегулировать.",
     "links": ["/services/remont-elektrooborudovania-avtomobila/regulirovka-far.html"],
     "cta": "Записаться на регулировку фар", "message": "Хочу проверить и отрегулировать фары."},
]

EYEBROW = "// Приборы — {n} значков"
TITLE = "Что горит на приборной панели?"
LEAD = ("Нажмите на значок, который видите у себя, — расскажем, что он обычно означает, насколько это срочно "
        "и что делать дальше.")
NOTE = ("При включении зажигания почти все значки на пару секунд загораются — так машина проверяет лампы и системы. "
        "Важно то, что продолжает гореть после запуска двигателя.")
HINT_TITLE = "Цвет значка — это срочность"
HINT_TEXT = "Нажмите на значок, который горит у вас, — здесь появится, что он значит и что делать."
ASK = "Не нашли свой значок? Опишите, как он выглядит, — перезвоним и подскажем."
ASK_CTA = "Описать значок"
ASK_MESSAGE = "На панели горит значок: "
SCREEN_IDLE = "Выберите значок"
SCREEN_CHECK = "Проверка ламп"
CTA = "Записаться на диагностику"
MESSAGE = "Горит индикатор «{short}». Хочу записаться на диагностику."


def _links(paths):
    """(href, label) of existing service pages. A missing page or a removal page is a build error, not a dead link."""
    out = []
    for path in paths:
        svc = D.BY_PATH.get(path)
        if svc is None:
            raise ValueError(f"pribory: нет страницы услуги {path}")
        if "udalenie" in path or "otklucenie" in path:
            raise ValueError(f"pribory: плюшка не ведёт на страницы удаления и отключения систем ({path})")
        out.append((path, svc.get("nav_name") or svc["h1"]))
    return out


def _sym(key, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f'<svg{c} viewBox="0 0 32 32" aria-hidden="true" focusable="false"><use href="#pl-{key}"/></svg>'


def _sprite():
    body = "".join(f'<symbol id="pl-{k}" viewBox="0 0 32 32">{v}</symbol>' for k, v in SYMBOLS.items())
    return f'<svg class="sprite" aria-hidden="true" focusable="false" style="position:absolute;width:0;height:0;overflow:hidden">{body}</svg>'


def _dial(redline=False):
    """A dim gauge face (speedometer / tachometer) beside the lamps: a 270° scale of ticks, no numbers, no needle.
    It only says «this is an instrument cluster»; the tachometer gets its red zone."""
    cx = cy = 100
    r_arc, n = 92, 40
    minor, major, red = [], [], []
    for i in range(n + 1):
        a = math.radians(135 + 270 * i / n)
        long = i % 5 == 0
        r1, r2 = r_arc - 5, r_arc - (17 if long else 10)
        seg = f"M{cx + r1 * math.cos(a):.1f} {cy + r1 * math.sin(a):.1f}L{cx + r2 * math.cos(a):.1f} {cy + r2 * math.sin(a):.1f}"
        (red if redline and i >= n - 6 else major if long else minor).append(seg)
    a0, a1 = math.radians(135), math.radians(45)
    arc = f"M{cx + r_arc * math.cos(a0):.1f} {cy + r_arc * math.sin(a0):.1f}A{r_arc} {r_arc} 0 1 1 {cx + r_arc * math.cos(a1):.1f} {cy + r_arc * math.sin(a1):.1f}"
    red_path = f'<path class="dial__red" d="{"".join(red)}"/>' if red else ""
    return (f'<svg class="cluster__dial" viewBox="0 0 200 200" aria-hidden="true" focusable="false">'
            f'<path class="dial__arc" d="{arc}"/><circle class="dial__ring" cx="100" cy="100" r="60"/>'
            f'<path class="dial__minor" d="{"".join(minor)}"/><path class="dial__major" d="{"".join(major)}"/>{red_path}</svg>')


def _lamp(l):
    colour = TONES[l["tone"]][0].lower()
    check = "" if l.get("check", True) else ' data-no-check'
    return (f'<button class="lamp" type="button" data-lamp="{l["key"]}" data-tone="{l["tone"]}"{check} aria-pressed="false" '
            f'aria-controls="pribory-{l["key"]}" aria-label="{esc(l["short"])}, {colour}" style="--off:{l["off"]}ms">'
            f'{_sym(l["key"], "lamp__sym")}{_sym(l["key"], "lamp__sym lamp__sym--lit")}</button>')


def _card(l):
    tone, meaning = TONES[l["tone"]]
    links = "".join(f'<li><a class="link-arrow" href="{href}">{esc(label)} {icon("arrow-up-right")}</a></li>'
                    for href, label in _links(l["links"]))
    preset = json.dumps({"message": l.get("message") or MESSAGE.format(short=l["short"])}, ensure_ascii=False)
    note = f'<p class="lamp-card__note">{esc(l["note"])}</p>' if l.get("note") else ""
    note += kod.lamp_link() if l.get("kod") else ""   # the link to the decoder goes under «Что это значит» too
    k = l["key"]
    return f"""<article class="lamp-card" id="pribory-{k}" data-lamp-card="{k}" data-tone="{l['tone']}" data-short="{esc(l['short'])}" aria-labelledby="pribory-{k}-title">
      <div class="lamp-card__in">
        <div class="lamp-card__id">
          <div class="lamp-card__head"><span class="lamp-card__icon">{_sym(k)}</span><div><h3 class="lamp-card__title" id="pribory-{k}-title">{esc(l['name'])}</h3><p class="lamp-card__look">Значок: {esc(l['look'])}</p></div></div>
          <p class="lamp-card__urgency"><b>{tone}</b> — {esc(meaning)}.</p>
        </div>
        <div class="lamp-card__text"><h4 class="lamp-card__label">Что это значит</h4><p>{esc(l['means'])}</p>{note}</div>
        <div class="lamp-card__text"><h4 class="lamp-card__label">Что делать</h4><p>{esc(l['todo'])}</p></div>
        <div class="lamp-card__foot">
          <ul class="lamp-card__links" aria-label="Услуги по теме">{links}</ul>
          <button class="btn btn--primary" type="button" data-modal="call" data-preset="{esc(preset)}">{icon('phone')} {esc(l.get('cta') or CTA)}</button>
        </div>
      </div>
    </article>"""


def _hint():
    preset = json.dumps({"message": ASK_MESSAGE}, ensure_ascii=False)
    rows = "".join(f'<li data-tone="{t}"><span><b>{name}</b> — {esc(text)}.</span></li>' for t, name, text in LEGEND)
    return f"""<div class="lamp-card lamp-card--hint is-active" data-lamp-card="">
      <div class="lamp-card__in">
        <div class="lamp-card__id"><p class="lamp-card__label">Как пользоваться</p><h3 class="lamp-card__title">{esc(HINT_TITLE)}</h3></div>
        <ul class="lamp-legend">{rows}</ul>
        <div class="lamp-card__text"><p>{esc(NOTE)}</p><p class="lamp-card__hint">{esc(HINT_TEXT)}</p></div>
        <div class="lamp-card__foot">
          <p class="lamp-card__ask">{esc(ASK)}</p>
          <button class="btn btn--ghost is-on-dark" type="button" data-modal="call" data-preset="{esc(preset)}">{icon('phone')} {esc(ASK_CTA)}</button>
        </div>
      </div>
    </div>"""


def pribory_section():
    if not 12 <= len(LAMPS) <= 20 or len({l["key"] for l in LAMPS}) != len(LAMPS) or any(l["key"] not in SYMBOLS for l in LAMPS):
        raise ValueError("pribory: 12–20 значков, у каждого свой ключ и свой символ")
    lamps = "".join(_lamp(l) for l in LAMPS)
    cards = "".join(_card(l) for l in LAMPS)
    # the inline line marks the section as interactive before it is painted: no flash of the no-JS list on a #pribory link
    return f"""<section class="section pribory" id="pribory" aria-labelledby="pribory-title" data-pribory>
  <script>document.currentScript.parentNode.classList.add('is-live')</script>
  {_sprite()}
  <div class="wrap">
    <div class="sec-head reveal">
      <div><p class="eyebrow">{esc(EYEBROW.format(n=len(LAMPS)))}</p><h2 class="h2 sec-head__title" id="pribory-title">{esc(TITLE)}</h2></div>
      <p class="sec-head__aside">{esc(LEAD)}</p>
    </div>
    <div class="pribory__stage reveal">
      <div class="pribory__panel">
        <div class="cluster corner" data-cluster>
          {_dial()}
          <div class="cluster__center">
            <p class="cluster__screen" aria-hidden="true" data-idle="{esc(SCREEN_IDLE)}" data-check="{esc(SCREEN_CHECK)}"><i></i><span data-cluster-screen>{esc(SCREEN_IDLE)}</span></p>
            <div class="cluster__grid" role="group" aria-label="Значки приборной панели">{lamps}</div>
          </div>
          {_dial(redline=True)}
        </div>
      </div>
      <div class="pribory__cards">
    {_hint()}{cards}
      </div>
    </div>
    <p class="sr-only" aria-live="polite" data-pribory-live></p>
  </div>
</section>"""
