// Functional checks using a minimal DOM; this does not test browser rendering.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const elements = new Map();
for (const match of html.matchAll(/\bid="([^"\s]+)"/g)) {
  assert(!elements.has(match[1]), `Duplicate id: ${match[1]}`);
  elements.set(match[1], { value: '', textContent: '', addEventListener() {} });
}
elements.get('q-input').value = '1';
const document = { getElementById: id => elements.get(id), addEventListener: (_, fn) => fn() };
const window = {};
let failFetch = false;
const fetch = async url => {
  if (failFetch) throw new Error('Offline');
  return { ok: true, json: async () => JSON.parse(fs.readFileSync(path.join(root, url), 'utf8')) };
};
vm.runInNewContext(fs.readFileSync(path.join(root, 'app.js'), 'utf8'), { document, window, fetch, console });
const value = id => elements.get(id).textContent;
const convert = input => { elements.get('q-input').value = String(input); window.recalcQ313(); };
let failed = 0;
async function check(name, fn) {
  try { await fn(); console.log('PASS ' + name); }
  catch (error) { failed++; console.log('FAIL ' + name + ': ' + error.message); }
}
(async () => {
  await window.resultsReady;
  await check('Q3.13 words and convergent rounding', () => {
    for (const [input, word] of [[1, '0x2000'], [-4, '0x8000'], [-0.5 / 8192, '0x0000'], [1.5 / 8192, '0x0002']]) {
      convert(input); assert.equal(value('q-hex'), word);
    }
  });
  await check('saturation includes full precision loss', () => {
    convert(6); assert.equal(value('q-hex'), '0x7FFF');
    assert.equal(Number(value('q-error')), 6 - 32767 / 8192);
  });
  await check('invalid input clears stale values', () => {
    for (const input of ['', 'Infinity', 'not-a-number']) {
      convert(input); assert.equal(value('q-hex'), ''); assert.match(value('q-status'), /finite/);
    }
  });
  await check('visible results come from recorded evidence', () => {
    assert.match(value('load-status'), /Latest recorded/);
    const metrics = JSON.parse(fs.readFileSync(path.join(root,'results/verification/model_metrics.json'),'utf8'));
    assert.equal(value('cnn-accuracy'), metrics.models.cnn.accuracy.toFixed(2)+'%');
    assert.equal(value('fcn-accuracy'), metrics.models.fcn.accuracy.toFixed(2)+'%');
    assert.equal(value('cnn-confusion'), '440 / 0 / 14 / 136');
    assert.equal(value('synthesis-dsp48e1'), '88');
    const memory = JSON.parse(fs.readFileSync(path.join(root,'results/verification/mif_validation.json'),'utf8'));
    assert.match(value('memory-result'), new RegExp(memory.mif_files_checked+' MIF files checked: 144 active, '+memory.obsolete_files.length+' obsolete'));
    assert(!/https?:|requestAnimationFrame|Math.random/.test(fs.readFileSync(path.join(root, 'app.js'), 'utf8')));
  });
  await check('offline loading reports a saved snapshot', async () => {
    failFetch = true; assert.equal(await window.loadResults(), false);
    assert.match(value('load-status'), /saved snapshot/);
  });
  console.log(`Results page: ${5 - failed}/5 checks passed (mock DOM).`);
  process.exitCode = failed ? 1 : 0;
})();
