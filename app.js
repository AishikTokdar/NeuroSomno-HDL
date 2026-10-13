/* Project explanations, measured results and lightweight interactive diagrams. */
document.addEventListener('DOMContentLoaded', () => {
    const byId = id => document.getElementById(id);
    const text = (id, value) => { byId(id).textContent = String(value); };
    const format = value => Number(value).toLocaleString('en-US');
    const layers = {
        1: { title: 'Layer 1: learning the input representation', inputs: 784, outputs: 30, activation: 'ReLU', parameters: 23550,
            description: 'Thirty neurons each accumulate 784 signed products, add a bias and apply ReLU. Synchronous weight reads are aligned with the input stream before multiplication.', formula: 'y = ReLU(Σ((x × w) >>> 13) + b)' },
        2: { title: 'Layer 2: combining the learned features', inputs: 30, outputs: 30, activation: 'ReLU', parameters: 930,
            description: 'Thirty parallel neurons combine the first-layer activations. Negative accumulated values are clipped to zero, and positive outputs saturate to the signed 16-bit range.', formula: 'y = ReLU(Σ((x × w) >>> 13) + b)' },
        3: { title: 'Layer 3: a compact nonlinear representation', inputs: 30, outputs: 10, activation: 'Sigmoid', parameters: 310,
            description: 'Ten neurons form a bottleneck. A 1,024-entry lookup table approximates the sigmoid function after the accumulated value has been saturated.', formula: 'y = sigmoid_LUT(saturate(Σ((x × w) >>> 13) + b))' },
        4: { title: 'Layer 4: two scores, one classification', inputs: 10, outputs: 2, activation: 'Linear', parameters: 22,
            description: 'The final pair of neurons produces signed scores for normal and apnea. The greater score selects the class. A tie selects normal; there is no additional software classification head.', formula: 'class = score_apnea > score_normal ? 1 : 0' }
    };
    function markButtons(selector, attribute, selected) {
        document.querySelectorAll(selector).forEach(button => {
            const active = button.getAttribute(attribute) === String(selected);
            button.classList.toggle('active', active);
            button.setAttribute('aria-pressed', String(active));
        });
    }
    function selectLayer(index) {
        const layer = layers[index];
        if (!layer) return;
        markButtons('[data-layer]', 'data-layer', index);
        text('layer-title', layer.title); text('layer-description', layer.description);
        text('layer-module', `layer${index}.v / neuron.v`); text('layer-formula', layer.formula);
        for (const key of ['inputs', 'outputs', 'activation', 'parameters']) {
            text('layer-' + key, typeof layer[key] === 'number' ? format(layer[key]) : layer[key]);
        }
    }
    document.querySelectorAll('[data-layer]').forEach(button => button.addEventListener('click', () => selectLayer(button.getAttribute('data-layer'))));
    function selectResults(view) {
        if (!['metrics', 'confusion'].includes(view)) return;
        markButtons('[data-results-view]', 'data-results-view', view);
        byId('metrics-view').hidden = view !== 'metrics';
        byId('confusion-view').hidden = view !== 'confusion';
    }
    document.querySelectorAll('[data-results-view]').forEach(button => button.addEventListener('click', () => selectResults(button.getAttribute('data-results-view'))));

    let signalData;
    function selectSignal(stage) {
        if (!['raw', 'filtered', 'normalized'].includes(stage)) return;
        markButtons('[data-signal]', 'data-signal', stage);
        text('signal-title', { raw: 'Raw signal / includes a 50 Hz component', filtered: 'Filtered / notch + bandpass', normalized: 'Normalized / zero mean, unit variance' }[stage]);
        if (!signalData) return;
        const values = signalData[stage];
        const path = values.map((value, index) => `${index ? 'L' : 'M'}${(index * 700 / (values.length - 1)).toFixed(2)} ${(110 - value * 43).toFixed(2)}`).join(' ');
        byId('signal-path').setAttribute('d', path);
        byId('signal-plot').setAttribute('aria-label', `${stage} synthetic EEG across two seconds. Educational illustration, not patient data.`);
    }
    document.querySelectorAll('[data-signal]').forEach(button => button.addEventListener('click', () => selectSignal(button.getAttribute('data-signal'))));

    window.recalcQ313 = function () {
        const original = Number.parseFloat(byId('q-input').value);
        if (!Number.isFinite(original)) {
            text('q-status', 'Enter a finite number.');
            for (const id of ['q-hex', 'q-decoded', 'q-error']) text(id, '');
            byId('q-bits').textContent = '';
            return;
        }
        const bounded = Math.max(-4, Math.min(32767 / 8192, original));
        const raw = bounded * 8192;
        const lower = Math.floor(raw), fraction = raw - lower;
        const integer = fraction < 0.5 ? lower : fraction > 0.5 ? lower + 1 : (lower % 2 === 0 ? lower : lower + 1);
        const decoded = integer / 8192;
        text('q-status', bounded !== original ? 'Saturated: the error includes the lost magnitude outside the representable range.' : 'Convergent rounding, signed two’s-complement encoding.');
        text('q-hex', '0x' + (integer & 0xffff).toString(16).toUpperCase().padStart(4, '0'));
        text('q-decoded', String(decoded)); text('q-error', Number(Math.abs(original - decoded).toPrecision(7)).toString());
        const bits = (integer & 0xffff).toString(2).padStart(16, '0');
        byId('q-bits').innerHTML = bits.split('').map(bit => `<span aria-hidden="true">${bit}</span>`).join('');
        byId('q-bits').setAttribute('aria-label', `16-bit binary word: ${bits}`);
    };
    byId('q-input').addEventListener('input', window.recalcQ313);
    document.querySelectorAll('[data-preset]').forEach(button => button.addEventListener('click', () => {
        byId('q-input').value = button.getAttribute('data-preset'); window.recalcQ313();
    }));
    window.recalcQ313();

    const menu = byId('menu-toggle');
    function closeMenu() { byId('nav-links').classList.remove('open'); menu.setAttribute('aria-expanded', 'false'); }
    menu.addEventListener('click', () => {
        const open = menu.getAttribute('aria-expanded') !== 'true';
        byId('nav-links').classList.toggle('open', open); menu.setAttribute('aria-expanded', String(open));
    });
    document.querySelectorAll('nav a').forEach(link => link.addEventListener('click', closeMenu));
    document.addEventListener('keydown', event => { if (event.key === 'Escape') closeMenu(); });
    byId('copy-command').addEventListener('click', async () => {
        const button = byId('copy-command');
        try { await navigator.clipboard.writeText(byId('setup-command').textContent); button.textContent = 'Copied'; }
        catch { button.textContent = 'Select to copy'; }
        setTimeout(() => { button.textContent = 'Copy'; }, 1800);
    });

    const metricNames = [['accuracy', 'Accuracy'], ['balanced_acc', 'Balanced accuracy'], ['sensitivity', 'Sensitivity'], ['specificity', 'Specificity'], ['precision', 'Precision'], ['f1', 'F1 score']];
    function renderResults(models, quantized, synthesis) {
        const groups = [models.models.cnn, models.models.fcn, quantized.metrics];
        if (models.models.fcn.checkpoint_sha256 !== quantized.checkpoint_sha256 || models.test_windows !== quantized.test_windows) {
            throw new Error('Evaluation snapshots do not describe the same model and split');
        }
        for (const [index, name] of ['cnn', 'fcn', 'quantized'].entries()) {
            const result = groups[index];
            byId(name + '-score').innerHTML = Number(result.accuracy).toFixed(2) + '<span>%</span>';
            text(name + '-recall', Number(result.sensitivity).toFixed(2) + '%');
            text(name + '-f1', Number(result.f1).toFixed(4));
            if (name !== 'fcn') for (const key of ['tn', 'fp', 'fn', 'tp']) text(name + '-' + key, result.confusion[key]);
        }
        byId('hero-accuracy').innerHTML = Number(models.models.fcn.accuracy).toFixed(2) + '<span>%</span>';
        byId('metrics-body').innerHTML = metricNames.map(([key, label]) => '<tr><td>' + label + '</td>' + groups.map(group => '<td>' + (key === 'f1' ? Number(group[key]).toFixed(4) : Number(group[key]).toFixed(2) + '%') + '</td>').join('') + '</tr>').join('');
        text('dsp-count', format(synthesis.dsp48e1) + ' / 220');
        text('bram-count', format(synthesis.ramb18e1) + ' / 280');
        text('lut-count', format(synthesis.lut_cells) + ' / 53,200');
        text('ff-count', format(synthesis.flip_flops) + ' / 106,400');
    }
    window.siteReady = (async () => {
        try {
            const urls = ['results/verification/model_metrics.json', 'results/verification/quantized_metrics.json', 'results/verification/synthesis_summary.json', 'assets/signal_example.json'];
            const [models, quantized, synthesis, signal] = await Promise.all(urls.map(async url => {
                const response = await fetch(url);
                if (!response.ok) throw new Error('Could not load model data');
                return response.json();
            }));
            renderResults(models, quantized, synthesis); signalData = signal; selectSignal('raw');
            return true;
        } catch {
            text('results-source', 'Showing the recorded result snapshot included with this page. Use a local HTTP server to load the interactive signal data.');
            return false;
        }
    })();
    window.NeuroSomno = Object.freeze({ selectLayer, selectResults, selectSignal });
});
