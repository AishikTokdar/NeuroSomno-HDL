// Frontend behavior checks. Developer diagnostics are not part of the public page.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const source = fs.readFileSync(path.join(root, 'app.js'), 'utf8');
function boot(offline = false, options = {}) {
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
  const document = { documentElement: element({}), getElementById: id => ids.get(id),
    addEventListener: (name, callback) => { if (name === 'DOMContentLoaded') callback(); },
    querySelectorAll: selector => selector.startsWith('[') ? nodes.filter(n => Object.hasOwn(n.attrs, selector.slice(1, -1))) : [] };
  const window = {};
  const storage = new Map(options.theme ? [['neurosomno-theme', options.theme]] : []);
  const localStorage = { getItem: key => { if (options.blockStorage) throw new Error('Storage disabled'); return storage.get(key); },
    setItem: (key,value) => { if (options.blockStorage) throw new Error('Storage disabled'); storage.set(key,value); } };
  const media = { matches: Boolean(options.dark), addEventListener: (_, callback) => { media.change = callback; } };
  const fetch = async url => {
    if (offline) throw new Error('Offline');
    return { ok: true, json: async () => JSON.parse(fs.readFileSync(path.join(root, url), 'utf8')) };
  };
  const context = { document, window, fetch, console, setTimeout, localStorage, matchMedia: () => media, navigator: { clipboard: { writeText: async () => {} } } };
  vm.runInNewContext(html.match(/<script>([\s\S]*?)<\/script>/)[1], context);
  vm.runInNewContext(source, context);
  return { window, ids, nodes, document, storage, media, value: id => ids.get(id).textContent };
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
  await check('theme choice persists, follows the system and tolerates blocked storage', async () => {
    app.window.NeuroSomno.setTheme('dark');
    assert.equal(app.document.documentElement.attrs['data-theme'], 'dark');
    assert.equal(app.storage.get('neurosomno-theme'), 'dark');
    assert.equal(app.ids.get('theme-color').attrs.content, '#1c1e1b');
    const saved = boot(false, {theme:'light',dark:true}); await saved.window.siteReady;
    assert.equal(saved.document.documentElement.attrs['data-theme'], 'light');
    saved.window.NeuroSomno.setTheme('system'); assert.equal(saved.document.documentElement.attrs['data-theme'], 'dark');
    saved.media.matches = false; saved.media.change(); assert.equal(saved.document.documentElement.attrs['data-theme'], 'light');
    const blocked = boot(false, {blockStorage:true}); assert.equal(await blocked.window.siteReady, true);
    blocked.window.NeuroSomno.setTheme('dark'); assert.equal(blocked.document.documentElement.attrs['data-theme'], 'dark');
  });
  await check('spectrum identifies frequencies and shows actual notch attenuation', () => {
    const wave = Array.from({length:256},(_,i) => Math.sin(2*Math.PI*10*i/128));
    const bins = app.window.NeuroSomno.spectrum(wave);
    assert(Math.abs(bins[20]-1)<1e-12); assert(bins[100]<1e-12);
    const signal = JSON.parse(fs.readFileSync(path.join(root,'assets/signal_example.json'),'utf8'));
    const raw = app.window.NeuroSomno.spectrum(signal.raw), filtered = app.window.NeuroSomno.spectrum(signal.filtered);
    assert(filtered[100]<raw[100]/10);
    app.window.NeuroSomno.selectSignal('filtered'); assert.match(app.value('spectrum-caption'), /50 Hz amplitude/);
  });
  await check('parameter shares and activation curves describe the actual network', () => {
    app.window.NeuroSomno.selectLayer(4); assert.match(app.value('parameter-note'), /0.09%/);
    assert.match(app.ids.get('parameter-bars').innerHTML, /23,550/);
    assert.equal(app.window.NeuroSomno.activationValue('relu',-3),0);
    assert.equal(app.window.NeuroSomno.activationValue('sigmoid',0),.5);
    app.ids.get('activation-input').value = '0'; app.window.NeuroSomno.renderActivation('sigmoid');
    assert.match(app.value('activation-output'), /0.5000/);
    assert.equal((app.ids.get('activation-path').attrs.d.match(/[ML]/g)||[]).length,161);
  });
  await check('transaction gaps preserve counts and comparison metrics use the correct scale', () => {
    app.window.NeuroSomno.selectTransaction(1); assert.equal(app.value('stream-accepted'),'1 / 784');
    app.window.NeuroSomno.selectTransaction(2); assert.equal(app.value('stream-accepted'),'1 / 784'); assert.equal(app.value('stream-valid'),'0');
    app.window.NeuroSomno.selectTransaction(3); assert.equal(app.value('stream-last'),'1'); assert.equal(app.value('stream-accepted'),'784 / 784');
    app.window.NeuroSomno.selectTransaction(99); assert.equal(app.ids.get('stream-next').disabled,true);
    app.window.NeuroSomno.renderComparison('sensitivity'); assert.match(app.ids.get('comparison-bars').innerHTML,/90.67%/);
    app.window.NeuroSomno.renderComparison('f1'); assert.match(app.ids.get('comparison-bars').innerHTML,/97.96%/);
    assert.match(app.value('comparison-caption'),/zero-to-one/);
  });
  console.log(`Frontend: ${9 - failed}/9 checks passed.`);
  process.exitCode = failed ? 1 : 0;
})();
