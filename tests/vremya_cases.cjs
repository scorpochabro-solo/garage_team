// «Когда удобно приехать?» of src/assets/js/vremya.js at fixed moments (a fake clock), for tests/test_vremya.py.
//   node tests/vremya_cases.cjs '<job>'   -> JSON: one result per case
// job: {"conf": <data-vremya of build/vremya.py>, "cases": [...]}, a case is one of
//   {"op": "days", "at": ISO}                                  the window: [{date, state, wd, num, tag, sr, parts: [[key, hours, sr]]}]
//   {"op": "line", "at": ISO, "date": "YYYY-MM-DD", "part": key | "any" | null}   the line for the message
//   {"op": "with", "text": "…", "line": "…"}                   the text with the line put in / replaced / taken out ("" = out)
//   {"op": "parse", "at": ISO, "text": "…"}                    the choice a line in the text stands for
// The file runs in a sandbox with an empty page. Each moment is converted twice, by Intl (Europe/Moscow) and by the
// UTC+3 fallback (Intl without time zones), and the two must agree; the machine's own time zone plays no part.
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const CODE = fs.readFileSync(path.join(__dirname, '..', 'src', 'assets', 'js', 'vremya.js'), 'utf8');

function load(intl) {
  const page = { querySelectorAll: () => [], getElementById: () => null, addEventListener() {}, visibilityState: 'visible' };
  const sandbox = { window: {}, document: page, addEventListener() {}, setTimeout, clearTimeout, Intl: intl };
  vm.createContext(sandbox);
  vm.runInContext(CODE, sandbox);
  return sandbox.window.G.vremya;
}

const job = JSON.parse(process.argv[2]);
const withIntl = load(Intl);
const noTz = load({ DateTimeFormat: function DateTimeFormat() { throw new RangeError('no time zone data'); } });
const api = withIntl.create(job.conf);

const at = (iso) => {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) throw new Error(`bad moment ${iso}`);
  const a = withIntl.moscow(date);
  const b = noTz.moscow(date);
  if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(`Intl and UTC+3 disagree for ${iso}: ${JSON.stringify([a, b])}`);
  return api.days(a);
};
const plain = (x) => JSON.parse(JSON.stringify(x));   // objects of the sandbox's realm -> plain JSON

const out = job.cases.map((c) => {
  if (c.op === 'days') {
    return at(c.at).map((d) => {
      const l = api.dayLabel(d);
      return { date: d.key, state: d.state, wd: l.wd, num: l.num, tag: l.tag, sr: l.sr,
        parts: d.slots.map((s) => { const p = api.partLabel(s); return [s.key, p.hours, p.sr]; }) };
    });
  }
  if (c.op === 'line') {
    const day = at(c.at).find((d) => d.key === c.date);
    if (!day) throw new Error(`${c.date} is not in the window of ${c.at}`);
    return api.lineFor(day, c.part);
  }
  if (c.op === 'with') return api.withLine(c.text, c.line);
  if (c.op === 'parse') return plain(api.parse(c.text, at(c.at)));
  throw new Error(`unknown op ${c.op}`);
});
console.log(JSON.stringify(out));
