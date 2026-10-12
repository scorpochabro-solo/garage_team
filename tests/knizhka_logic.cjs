// The pure part of src/assets/js/knizhka.js («Моя машина»: G.knizhka) for tests/test_knizhka.py:
//   node tests/knizhka_logic.cjs '[["addMonths", "2026-01-31", 1], ["checkVin", "xw8 zzz61z eg061733"], …]'
// prints one JSON row per call: {"ok": true, "value": …} or {"ok": false, "error": "…"}.
// The file runs in a sandbox with an empty page and no storage, so only the model starts; dates are counted in UTC
// days, and the test runs it in a time zone with daylight saving to show that the machine's zone plays no part.
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const CODE = fs.readFileSync(path.join(__dirname, '..', 'src', 'assets', 'js', 'knizhka.js'), 'utf8');
const page = { querySelector: () => null, querySelectorAll: () => [], getElementById: () => null, addEventListener() {} };
const sandbox = { window: {}, document: page, navigator: {}, addEventListener() {}, setTimeout, clearTimeout };
vm.createContext(sandbox);
vm.runInContext(CODE, sandbox);
const K = sandbox.window.G.knizhka;

const calls = JSON.parse(process.argv[2] || '[]');
const rows = calls.map(([fn, ...args]) => {
  try {
    if (typeof K[fn] !== 'function') throw new Error(`no function ${fn}`);
    // results cross from the sandbox as JSON, like everything the page would store; NaN («not a number typed») is
    // kept apart from null («nothing typed»)
    const json = JSON.stringify(K[fn](...args), (k, v) => (typeof v === 'number' && Number.isNaN(v) ? 'NaN' : v));
    return { ok: true, value: json === undefined ? null : JSON.parse(json) };
  } catch (e) {
    return { ok: false, error: String(e && e.message ? e.message : e) };
  }
});
console.log(JSON.stringify(rows));
