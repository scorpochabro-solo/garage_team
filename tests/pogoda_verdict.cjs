// The verdict of src/assets/js/pogoda.js on test forecasts, for tests/test_pogoda.py.
//   node tests/pogoda_verdict.cjs < input.json   ->   JSON
// input: { "config": <#pogoda-data of the page>,
//          "cases": [{ "name", "api": <an Open-Meteo answer>, "today": index of today (default: config.past) }],
//          "temps": [numbers], "moments": [ISO strings], "plurals": [numbers] }
// Each case runs parse -> verdict -> describe of the real script, or reports the parse error. The script runs in a
// sandbox with an empty page (it stops after exposing G.pogoda). Each moment goes through the Moscow clock twice,
// with Intl and with the UTC+3 fallback (Intl without time zones); both answers are returned.
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const CODE = fs.readFileSync(path.join(__dirname, '..', 'src', 'assets', 'js', 'pogoda.js'), 'utf8');

function load(intl) {
  const page = { querySelector: () => null, getElementById: () => null, addEventListener() {} };
  const sandbox = { window: {}, document: page, addEventListener() {}, setTimeout, clearTimeout, Intl: intl };
  vm.createContext(sandbox);
  vm.runInContext(CODE, sandbox);
  return sandbox.window.G.pogoda;
}

const P = load(Intl);
const noTz = load({ DateTimeFormat: function DateTimeFormat() { throw new RangeError('no time zone data'); } });
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const cfg = input.config;
const date = (days, i) => (i >= 0 ? days[i].date : null);

const cases = (input.cases || []).map((c) => {
  let days;
  try {
    days = P.parse(c.api, cfg);
  } catch (e) {
    return { name: c.name, ok: false, error: e.message };
  }
  const t = c.today === undefined ? cfg.past : c.today;
  const v = P.verdict(days, t, cfg);
  const w = P.describe(v, days, t, cfg);
  return {
    name: c.name, ok: true, days: days.length, today: days[t].date,
    season: v.season, state: v.state, cause: v.cause, from: date(days, v.from), frost: date(days, v.frost),
    run: v.run ? [days[v.run[0]].date, days[v.run[1]].date] : null, rebound: date(days, v.rebound),
    tone: w.tone, title: w.title, kick: w.kick, chip: w.chip, why: w.why, note: w.note, live: w.live, message: w.message,
    scale: (({ lo, hi }) => ({ lo, hi }))(P.scale(days, cfg)),
  };
});
const temps = (input.temps || []).map((x) => P.temp(x));
const moments = (input.moments || []).map((iso) => ({ iso, intl: P.zoned(new Date(iso), cfg.tz), fallback: noTz.zoned(new Date(iso), cfg.tz) }));
const plurals = (input.plurals || []).map((n) => `${n} ${P.plural(n, cfg.dayForms)}`);
process.stdout.write(JSON.stringify({ cases, temps, moments, plurals }));
