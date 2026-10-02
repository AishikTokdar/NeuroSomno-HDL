// Display recorded results and convert Q3.13 values. No simulated model outputs.
document.addEventListener('DOMContentLoaded', () => {
    const setText = (id, value) => { document.getElementById(id).textContent = value; };
    const number = value => Number(value).toLocaleString('en-US');

    window.recalcQ313 = function () {
        const original = Number.parseFloat(document.getElementById('q-input').value);
        if (!Number.isFinite(original)) {
            setText('q-status', 'Enter a finite number.');
            for (const id of ['q-hex', 'q-decoded', 'q-error']) setText(id, '');
            return;
        }
        const bounded = Math.max(-4, Math.min(32767 / 8192, original));
        const raw = bounded * 8192;
        const lower = Math.floor(raw);
        const fraction = raw - lower;
        const integer = fraction < 0.5 ? lower : fraction > 0.5 ? lower + 1 :
            (lower % 2 === 0 ? lower : lower + 1);
        const decoded = integer / 8192;
        setText('q-status', bounded !== original ? 'Input saturated to the signed Q3.13 range.' : '');
        setText('q-hex', '0x' + (integer & 0xffff).toString(16).toUpperCase().padStart(4, '0'));
        setText('q-decoded', String(decoded));
        setText('q-error', String(Math.abs(original - decoded)));
    };
    document.getElementById('q-input').addEventListener('input', window.recalcQ313);
    window.recalcQ313();

    window.loadResults = async function () {
        try {
            const files = ['summary', 'model_metrics', 'synthesis_summary', 'mif_validation'];
            const [summary, metrics, synthesis, memory] = await Promise.all(files.map(async name => {
                const response = await fetch('results/verification/' + name + '.json');
                if (!response.ok) throw new Error('Unable to load ' + name);
                return response.json();
            }));
            const checks = summary.regressions;
            const passed = checks.tests - checks.failures - checks.errors - checks.skipped;
            setText('regression-result', `${passed} / ${checks.tests} passed`);
            const rtl = summary.rtl_parity;
            setText('parity-result', `${number(rtl.neuron_outputs_compared)}; ${rtl.mismatches} mismatches`);
            setText('classification-result', `${rtl.correct_labels} / ${rtl.frames} correct`);
            for (const model of ['cnn', 'fcn']) {
                for (const key of ['accuracy', 'balanced_acc', 'sensitivity', 'specificity', 'precision', 'f1']) {
                    const value = metrics.models[model][key];
                    setText(model + '-' + key, key === 'f1' ? value.toFixed(4) : value.toFixed(2) + '%');
                }
                const c = metrics.models[model].confusion;
                setText(model + '-confusion', [c.tn, c.fp, c.fn, c.tp].join(' / '));
            }
            for (const key of ['dsp48e1', 'ramb18e1', 'flip_flops', 'lut_cells', 'estimated_logic_cells']) {
                setText('synthesis-' + key, number(synthesis[key]));
            }
            setText('memory-result', `${memory.mif_files_checked} MIF files checked: ${memory.active_files} active, ${memory.obsolete_files.length} obsolete. Active parameters: ${number(memory.active_parameters)}.`);
            setText('memory-status', memory.valid ? 'Memory validation passed. Check the report for checkpoint coverage and obsolete files.' : 'Memory validation failed. See the full memory report.');
            setText('load-status', 'Latest recorded results loaded. Accuracy uses synthetic data only.');
            return true;
        } catch (error) {
            setText('load-status', 'Showing the saved snapshot. Serve this folder with python -m http.server to load the reports.');
            return false;
        }
    };
    window.resultsReady = window.loadResults();
});
