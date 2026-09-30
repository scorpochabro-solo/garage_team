// parse(), explain(), message() and errorText() of src/assets/js/kod.js in node, for tests/test_kod.py.
//   echo '{"model": <build/kod.py model()>, "parse": ["p0 301, P0171"], "explain": ["P0301"], "message": [["P0301"]],
//          "errors": [{"key": "second", "token": "P4301"}]}' | node tests/kod_decode.cjs
// prints the same keys with the results. The file runs in a sandbox with an empty page, so only the pure part of
// kod.js is used; the model is what the script would read from the page (the reference rows and the JSON phrases).
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const CODE = fs.readFileSync(path.join(__dirname, '..', 'src', 'assets', 'js', 'kod.js'), 'utf8');
const page = { querySelector: () => null, querySelectorAll: () => [] };
const sandbox = { window: {}, document: page, addEventListener() {}, matchMedia: () => ({ matches: false }) };
vm.createContext(sandbox);
vm.runInContext(CODE, sandbox);
const K = sandbox.window.G.kod;

const job = JSON.parse(fs.readFileSync(0, 'utf8'));
const { model } = job;
const max = model.texts.max;
const out = {
  parse: (job.parse || []).map((raw) => K.parse(raw, max)),
  explain: (job.explain || []).map((code) => K.explain(code, model)),
  message: (job.message || []).map((codes) => K.message(codes, model.texts)),
  errors: (job.errors || []).map((e) => K.errorText(e, model.texts)),
};
process.stdout.write(JSON.stringify(out));
