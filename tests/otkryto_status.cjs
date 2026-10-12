// The status of src/assets/js/otkryto.js at fixed moments (a fake clock), for tests/test_otkryto.py.
//   node tests/otkryto_status.cjs '<{"week": …} as in data-oc>' 2026-10-05T08:59:00+03:00 …   -> JSON rows
//   add --md for a Markdown table
// The file runs in a sandbox with an empty page. Each moment is converted twice, by Intl (Europe/Moscow) and by the
// UTC+3 fallback (Intl without time zones), and the two must agree; the machine's own time zone plays no part.
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const CODE = fs.readFileSync(path.join(__dirname, '..', 'src', 'assets', 'js', 'otkryto.js'), 'utf8');
const DAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

function load(intl) {
  const page = { querySelectorAll: () => [], addEventListener() {}, visibilityState: 'visible' };
  const sandbox = { window: {}, document: page, navigator: {}, addEventListener() {}, setTimeout, clearTimeout, Intl: intl };
  vm.createContext(sandbox);
  vm.runInContext(CODE, sandbox);
  return sandbox.window.G.otkryto;
}

const args = process.argv.slice(2);
const md = args.includes('--md');
const [data, ...moments] = args.filter((a) => a !== '--md');
const week = JSON.parse(data).week;
const withIntl = load(Intl);
const noTz = load({ DateTimeFormat: function DateTimeFormat() { throw new RangeError('no time zone data'); } });

const rows = moments.map((iso) => {
  const date = new Date(iso);
  const a = withIntl.moscow(date);
  const b = noTz.moscow(date);
  if (a.day !== b.day || a.min !== b.min) throw new Error(`Intl and UTC+3 disagree for ${iso}: ${JSON.stringify([a, b])}`);
  const s = withIntl.status(week, a);
  const join = (rest) => (rest ? `${s.word} · ${rest}` : s.word).replace(/\u00a0/g, ' ');
  return { iso, moscow: `${DAYS[a.day]} ${withIntl.hm(a.min)}`, state: s.state, text: join(s.rest), brief: join(s.brief) };
});

if (md) {
  console.log('| Москва | Состояние | Контакты, меню | Верхняя строка шапки |');
  console.log('|---|---|---|---|');
  rows.forEach((r) => console.log(`| ${r.moscow} | ${r.state} | ${r.text} | ${r.brief} |`));
} else {
  console.log(JSON.stringify(rows));
}
