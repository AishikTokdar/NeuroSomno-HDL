// Frontend behavior checks. Developer diagnostics are not part of the public page.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const source = fs.readFileSync(path.join(root, 'app.js'), 'utf8');
function boot(offline = false) {
  const ids = new Map(), nodes = [];
  function element(attrs) {
    const classes = new Set((attrs.class || '').split(/\s+/));
    return { attrs, value: attrs.value || '', textContent: '', innerHTML: '', hidden: false,
      listeners: {}, addEventListener(name, handler) { this.listeners[name] = handler; },
      getAttribute(name) { return this.attrs[name] ?? null; },
      setAttribute(name, value) { this.attrs[name] = String(value); },
      classList: { toggle(name, on) { if (on) classes.add(name); else classes.delete(name); },
        remove(name) { classes.delete(name); }, contains(name) { return classes.has(name); } } };
  }
  for (const tag of html.matchAll(/<[a-z][^>]*>/gi)) {
    const attrs = Object.fromEntries([...tag[0].matchAll(/([\w-]+)="([^"]*)"/g)].map(m => [m[1], m[2]]));
    const node = element(attrs); nodes.push(node);
    if (attrs.id) { assert(!ids.has(attrs.id), 'Duplicate id ' + attrs.id); ids.set(attrs.id, node); }
  }
  const document = { getElementById: id => ids.get(id),
    addEventListener: (name, callback) => { if (name === 'DOMContentLoaded') callback(); },
    querySelectorAll: selector => selector.startsWith('[') ? nodes.filter(n => Object.hasOwn(n.attrs, selector.slice(1, -1))) : [] };
  const window = {};
  const fetch = async url => {
    if (offline) throw new Error('Offline');
    return { ok: true, json: async () => JSON.parse(fs.readFileSync(path.join(root, url), 'utf8')) };
  };
  vm.runInNewContext(source, { document, window, fetch, console, setTimeout, navigator: { clipboard: { writeText: async () => {} } } });
  return { window, ids, nodes, value: id => ids.get(id).textContent };
}
let failed = 0;
async function check(name, fn) {
  try { await fn(); console.log('PASS ' + name); }
  catch (error) { failed++; console.log('FAIL ' + name + ': ' + error.message); }
}
(async () => {
  const app = boot(); assert.equal(await app.window.siteReady, true);
  await check('Q3.13 conversion, ties and saturation', () => {
    for (const [input, expected] of [[1,'0x2000'],[-4,'0x8000'],[-.5/8192,'0x0000'],[1.5/8192,'0x0002'],[6,'0x7FFF']]) {
      app.ids.get('q-input').value = String(input); app.window.recalcQ313();
      assert.equal(app.value('q-hex'), expected);
    }
    assert(Math.abs(Number(app.value('q-error'))-(6-32767/8192)) < 1e-6);
    assert.equal((app.ids.get('q-bits').innerHTML.match(/<span/g) || []).length, 16);
  });
  await check('architecture picker explains actual layer sizes', () => {
    app.window.NeuroSomno.selectLayer(4);
    assert.equal(app.value('layer-inputs'), '10'); assert.equal(app.value('layer-outputs'), '2');
    assert.equal(app.value('layer-activation'), 'Linear'); assert.equal(app.value('layer-parameters'), '22');
    assert.match(app.value('layer-description'), /no additional software classification head/);
    app.window.NeuroSomno.selectLayer(1); assert.equal(app.value('layer-parameters'), '23,550');
  });
  await check('model results and confusion views use measured data', () => {
    const q = JSON.parse(fs.readFileSync(path.join(root,'results/verification/quantized_metrics.json'),'utf8'));
    assert(app.ids.get('quantized-score').innerHTML.startsWith(q.metrics.accuracy.toFixed(2)));
    assert.equal(app.value('quantized-fn'), String(q.metrics.confusion.fn));
    assert.equal(app.value('cnn-fn'), '14'); assert.equal(app.value('dsp-count'), '88 / 220');
    app.window.NeuroSomno.selectResults('confusion');
    assert.equal(app.ids.get('confusion-view').hidden, false); assert.equal(app.ids.get('metrics-view').hidden, true);
    app.window.NeuroSomno.selectResults('metrics'); assert.equal(app.ids.get('metrics-view').hidden, false);
    assert(!/pytest|regression suite|MIF files|memory validation|neuron outputs compared/i.test(html));
  });
  await check('signal controls show different processing stages', () => {
    const raw = app.ids.get('signal-path').attrs.d;
    assert(raw.startsWith('M0.00 ')); assert.equal((raw.match(/[ML]/g) || []).length, 256);
    app.window.NeuroSomno.selectSignal('filtered');
    assert.notEqual(app.ids.get('signal-path').attrs.d, raw); assert.match(app.value('signal-title'), /notch/);
    app.window.NeuroSomno.selectSignal('normalized'); assert.match(app.value('signal-title'), /unit variance/);
  });
  await check('invalid input and offline fallback remain honest', async () => {
    app.ids.get('q-input').value = 'Infinity'; app.window.recalcQ313();
    assert.equal(app.value('q-hex'), ''); assert.match(app.value('q-status'), /finite/);
    const offline = boot(true); assert.equal(await offline.window.siteReady, false);
    assert.match(offline.value('results-source'), /recorded result snapshot/);
    assert(html.includes('98.98') && html.includes('590'));
  });
  console.log(`Frontend: ${5 - failed}/5 checks passed.`);
  process.exitCode = failed ? 1 : 0;
})();