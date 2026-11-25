/* Project explanations, measured results and lightweight interactive diagrams. */
document.addEventListener('DOMContentLoaded', () => {
    const byId = id => document.getElementById(id);
    const text = (id, value) => { byId(id).textContent = String(value); };
    const format = value => Number(value).toLocaleString('en-US');
    const systemTheme = matchMedia('(prefers-color-scheme: dark)');
    let themePreference = 'system';
    try { themePreference = localStorage.getItem('neurosomno-theme') || 'system'; } catch {}
    function setTheme(preference) {
        themePreference = ['light', 'dark', 'system'].includes(preference) ? preference : 'system';
        const dark = themePreference === 'dark' || (themePreference === 'system' && systemTheme.matches);
        document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
        byId('theme-select').value = themePreference;
        byId('theme-color').setAttribute('content', dark ? '#1c1e1b' : '#f6f4ef');
        try { localStorage.setItem('neurosomno-theme', themePreference); } catch {}
    }
    byId('theme-select').addEventListener('change', event => setTheme(event.target.value));
    systemTheme.addEventListener('change', () => { if (themePreference === 'system') setTheme('system'); });
    setTheme(themePreference);
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
        renderParameters(Number(index));
    }
    function renderParameters(selected) {
        const total = Object.values(layers).reduce((sum, layer) => sum + layer.parameters, 0);
        byId('parameter-bars').innerHTML = Object.entries(layers).map(([index, layer]) =>
            `<div class="parameter-row ${Number(index) === selected ? 'selected' : ''}"><div><span>Layer ${index} · ${layer.inputs} × ${layer.outputs}</span><span>${format(layer.parameters)}</span></div><div class="parameter-track"><span style="width:${layer.parameters / total * 100}%"></span></div></div>`).join('');
        text('parameter-note', `Layer ${selected} holds ${(layers[selected].parameters / total * 100).toFixed(2)}% of all ${format(total)} parameters, including biases. Linear scale; very small shares retain a two-pixel marker.`);
    }
    renderParameters(1);
    document.querySelectorAll('[data-layer]').forEach(button => button.addEventListener('click', () => selectLayer(button.getAttribute('data-layer'))));
    function selectResults(view) {
        if (!['metrics', 'confusion'].includes(view)) return;
        markButtons('[data-results-view]', 'data-results-view', view);
        byId('metrics-view').hidden = view !== 'metrics';
        byId('confusion-view').hidden = view !== 'confusion';
    }
    document.querySelectorAll('[data-results-view]').forEach(button => button.addEventListener('click', () => selectResults(button.getAttribute('data-results-view'))));

    let signalData, spectra, spectrumMaximum;
    function spectrum(values) {
        const count = values.length;
        return Array.from({ length: Math.floor(count / 2) + 1 }, (_, bin) => {
            let real = 0, imaginary = 0;
            values.forEach((value, index) => {
                const angle = 2 * Math.PI * bin * index / count;
                real += value * Math.cos(angle); imaginary -= value * Math.sin(angle);
            });
            return Math.hypot(real, imaginary) / count * (bin === 0 || bin === count / 2 ? 1 : 2);
        });
    }
    function selectSignal(stage) {
        if (!['raw', 'filtered', 'normalized'].includes(stage)) return;
        markButtons('[data-signal]', 'data-signal', stage);
        text('signal-title', { raw: 'Raw signal / includes a 50 Hz component', filtered: 'Filtered / notch + bandpass', normalized: 'Normalized / zero mean, unit variance' }[stage]);
        if (!signalData) return;
        const values = signalData[stage];
        const path = values.map((value, index) => `${index ? 'L' : 'M'}${(index * 700 / (values.length - 1)).toFixed(2)} ${(110 - value * 43).toFixed(2)}`).join(' ');
        byId('signal-path').setAttribute('d', path);
        byId('signal-plot').setAttribute('aria-label', `${stage} synthetic EEG across two seconds. Educational illustration, not patient data.`);
        if (spectra) {
            const magnitudes = spectra[stage];
            byId('spectrum-path').setAttribute('d', magnitudes.map((value, index) => `${index ? 'L' : 'M'}${(48 + index * 652 / (magnitudes.length - 1)).toFixed(2)} ${(190 - value / spectrumMaximum * 170).toFixed(2)}`).join(' '));
            byId('spectrum-plot').setAttribute('aria-label', `Linear amplitude spectrum of the ${stage} synthetic example, zero to 64 Hz.`);
            text('spectrum-caption', `${stage[0].toUpperCase() + stage.slice(1)} signal · 256 samples · 0.5 Hz frequency bins · 50 Hz amplitude: ${magnitudes[100].toFixed(4)}. One-sided discrete Fourier transform, no window taper; shared amplitude scale.`);
        }
    }
    document.querySelectorAll('[data-signal]').forEach(button => button.addEventListener('click', () => selectSignal(button.getAttribute('data-signal'))));

    let activation = 'relu';
    function activationValue(kind, value) {
        return kind === 'relu' ? Math.max(0, value) : kind === 'sigmoid' ? 1 / (1 + Math.exp(-value)) : value;
    }
    function renderActivation(kind = activation) {
        if (!['relu', 'sigmoid', 'linear'].includes(kind)) return;
        activation = kind;
        markButtons('[data-activation]', 'data-activation', kind);
        const parsed = Number(byId('activation-input').value);
        const value = Number.isFinite(parsed) ? Math.max(-4, Math.min(4, parsed)) : 0;
        const output = activationValue(kind, value);
        const point = (x, y) => `${(35 + (x + 4) / 8 * 365).toFixed(2)} ${(110 - y * 22.5).toFixed(2)}`;
        byId('activation-path').setAttribute('d', Array.from({ length: 161 }, (_, index) => {
            const x = -4 + index / 20;
            return `${index ? 'L' : 'M'}${point(x, activationValue(kind, x))}`;
        }).join(' '));
        const [cx, cy] = point(value, output).split(' ');
        byId('activation-dot').setAttribute('cx', cx); byId('activation-dot').setAttribute('cy', cy);
        byId('activation-plot').setAttribute('aria-label', `Mathematical ${kind} curve, input ${value.toFixed(2)}, output ${output.toFixed(4)}.`);
        text('activation-value', value.toFixed(2));
        text('activation-output', `${{ relu: 'ReLU', sigmoid: 'Sigmoid', linear: 'Linear' }[kind]}(${value.toFixed(2)}) = ${output.toFixed(4)}`);
    }
    document.querySelectorAll('[data-activation]').forEach(button => button.addEventListener('click', () => renderActivation(button.getAttribute('data-activation'))));
    byId('activation-input').addEventListener('input', () => renderActivation());
    renderActivation();

    const transaction = [
        [0, 1, 0, 0, 'The host pulses START. The core is ready to receive the input vector.'],
        [1, 1, 0, 1, 'VALID and READY are high. The first input word is accepted on the clock edge.'],
        [0, 1, 0, 1, 'The sender inserts an input gap. VALID is low, so no word is accepted and the count stays at one.'],
        [1, 1, 1, 784, 'Intermediate transfers are omitted in this illustration. Word 784 is accepted with TLAST high, ending the frame.'],
        [0, 0, 0, 784, 'The core finishes its remaining layer computations and serialization. READY stays low. This stage has no measured duration in the illustration.'],
        [0, 0, 0, 784, 'DONE is set. The host reads NNOUT for the class. Another START is required before the next vector. No prediction is invented by this illustration.']
    ];
    let transactionIndex = 0;
    function selectTransaction(index) {
        transactionIndex = Math.max(0, Math.min(transaction.length - 1, Number(index) || 0));
        const [valid, ready, last, accepted, description] = transaction[transactionIndex];
        document.querySelectorAll('[data-transaction]').forEach(node => {
            const current = Number(node.getAttribute('data-transaction')) === transactionIndex;
            node.classList.toggle('current', current); node.setAttribute('aria-current', current ? 'step' : 'false');
        });
        text('stream-valid', valid); text('stream-ready', ready); text('stream-last', last);
        text('stream-accepted', `${accepted} / 784`); text('stream-description', description);
        byId('stream-back').disabled = transactionIndex === 0;
        byId('stream-next').disabled = transactionIndex === transaction.length - 1;
    }
    byId('stream-back').addEventListener('click', () => selectTransaction(transactionIndex - 1));
    byId('stream-next').addEventListener('click', () => selectTransaction(transactionIndex + 1));
    byId('stream-reset').addEventListener('click', () => selectTransaction(0));
    selectTransaction(0);

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
    let comparisonGroups;
    function renderComparison(metric = byId('comparison-metric').value || 'accuracy') {
        if (!comparisonGroups || !metricNames.some(([key]) => key === metric)) return;
        const label = metricNames.find(([key]) => key === metric)[1];
        const names = ['CNN / float', 'FCN / float', 'FCN / Q3.13'];
        const values = comparisonGroups.map(group => Number(group[metric]) * (metric === 'f1' ? 100 : 1));
        byId('comparison-bars').innerHTML = values.map((value, index) => `<div class="comparison-row"><span>${names[index]}</span><div class="comparison-track"><span style="width:${Math.max(0, Math.min(100, value))}%"></span></div><strong>${value.toFixed(2)}%</strong></div>`).join('');
        byId('comparison-bars').setAttribute('aria-label', `${label}: ${names.map((name, index) => `${name} ${values[index].toFixed(2)} percent`).join(', ')}.`);
        text('comparison-caption', `${label} on the same 590 synthetic held-out windows. Full scale from 0 to 100%.${metric === 'f1' ? ' F1 is shown as a percentage here; the table uses its usual zero-to-one scale.' : ''}`);
    }
    byId('comparison-metric').addEventListener('change', () => renderComparison());
    function renderResults(models, quantized, synthesis) {
        const groups = [models.models.cnn, models.models.fcn, quantized.metrics];
        if (models.models.fcn.checkpoint_sha256 !== quantized.checkpoint_sha256 || models.test_windows !== quantized.test_windows) {
            throw new Error('Evaluation snapshots do not describe the same model and split');
        }
        comparisonGroups = groups; renderComparison();
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
            renderResults(models, quantized, synthesis); signalData = signal;
            spectra = Object.fromEntries(['raw', 'filtered', 'normalized'].map(stage => [stage, spectrum(signal[stage])]));
            spectrumMaximum = Math.max(...Object.values(spectra).flat()) * 1.05 || 1;
            selectSignal('raw');
            return true;
        } catch {
            text('results-source', 'Showing the recorded result snapshot included with this page. Use a local HTTP server to load the interactive signal data.');
            return false;
        }
    })();
    window.NeuroSomno = Object.freeze({ selectLayer, selectResults, selectSignal, setTheme, spectrum, renderActivation, activationValue, selectTransaction, renderComparison });
});
