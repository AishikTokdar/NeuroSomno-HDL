// NeuroSomno-HDL Interactive Web Application Script

document.addEventListener('DOMContentLoaded', () => {
    // 1. Tab Switching Handler
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetId = button.getAttribute('data-tab');

            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            button.classList.add('active');
            const targetContent = document.getElementById(targetId);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });

    // 2. Interactive Architecture Diagram Modal Data
    const archData = {
        'ps-cpu': {
            title: 'Processing System (PS) — ARM Cortex-A9',
            module: 'Host Software Subsystem',
            primitives: 'Dual-core ARM Cortex-A9 MPCore @ 667 MHz',
            datawidth: '32-bit AXI4-Lite & AXI4-Stream',
            cycles: 'Software Controlled Host Execution',
            description: 'The Processing System runs the host application, configures network weight parameters during initialization via AXI-Lite registers, streams raw test data into the accelerator via AXI-Stream, and services completion interrupts.'
        },
        'axi-wrapper': {
            title: 'AXI-Lite Interface Wrapper',
            module: 'hardware/rtl/axi_lite_wrapper.v',
            primitives: '120 LUTs, 142 Flip-Flops (FDRE)',
            datawidth: '32-bit Register Map (10 Address Offsets)',
            cycles: '2 Clock Cycles per AXI Read/Write Transaction',
            description: 'Interfacing control registers (`REG_CTRL`, `REG_STATUS`, `REG_NNOUT`) and memory loading registers (`REG_WVAL`, `REG_BVAL`, `REG_WEN`) to allow host CPU control over the hardware accelerator.'
        },
        'layer-1': {
            title: 'Layer 1 Accelerator Block (30 Neurons)',
            module: 'hardware/rtl/layer1.v & neuron.v',
            primitives: '1,530 LUTs, 1,770 FFs, 60 DSP48E1, 15 RAMB18E1 (BRAM)',
            datawidth: '784 Inputs x 16-bit Q3.13 -> 30 Outputs',
            cycles: '787 Clock Cycles per Sample (~7.87 µs)',
            description: 'Computes parallel 784-input MAC operations across 30 neurons. Weights are loaded from 15 Block RAMs (0.5 BRAM18 per neuron). Uses ReLU zero-clipping activation logic.'
        },
        'layer-2': {
            title: 'Layer 2 Accelerator Block (30 Neurons)',
            module: 'hardware/rtl/layer2.v & neuron.v',
            primitives: '1,530 LUTs, 1,770 FFs, 60 DSP48E1, Distributed LUTRAM',
            datawidth: '30 Inputs x 16-bit Q3.13 -> 30 Outputs',
            cycles: '33 Clock Cycles per Sample (~0.33 µs)',
            description: 'Receives serialized Layer 1 stream. Computes 30x30 matrix multiplication using parallel PEs. Weights are stored in small Distributed RAM (LUTRAM) with ReLU activation.'
        },
        'layer-3': {
            title: 'Layer 3 Accelerator Block (10 Neurons)',
            module: 'hardware/rtl/layer3.v & sig_rom.v',
            primitives: '3,070 LUTs (includes 2,560 LUTs for Sigmoid ROMs), 440 FFs, 20 DSP48E1',
            datawidth: '30 Inputs x 16-bit Q3.13 -> 10 Outputs',
            cycles: '34 Clock Cycles per Sample (~0.34 µs)',
            description: 'Processes Layer 2 outputs through 10 parallel neuron units. Activations are computed via 1024-word precomputed Sigmoid lookup tables (`sig_rom.v`) synthesized using Distributed ROM.'
        },
        'layer-4': {
            title: 'Layer 4 Accelerator Block (10 Neurons)',
            module: 'hardware/rtl/layer4.v & sig_rom.v',
            primitives: '3,070 LUTs (includes 2,560 LUTs for Sigmoid ROMs), 440 FFs, 20 DSP48E1',
            datawidth: '10 Inputs x 16-bit Q3.13 -> 10 Outputs',
            cycles: '14 Clock Cycles per Sample (~0.14 µs)',
            description: 'Final hidden layer producing raw class logit score estimates. Features Sigmoid activation lookup tables and serialized output streaming to the Argmax unit.'
        },
        'argmax': {
            title: 'Output Argmax Class Comparator',
            module: 'hardware/rtl/find_max_out.v',
            primitives: '45 LUTs, 32 Flip-Flops',
            datawidth: '10 x 16-bit Logit Inputs -> 4-bit Binary Class',
            cycles: '12 Clock Cycles per Sample (~0.12 µs)',
            description: 'Sequentially tracks maximum logit value across Layer 4 outputs, identifies predicted class index (0: Normal Respiration / 1: Apnea Event), and asserts completion interrupt `intr`.'
        }
    };

    // Modal Control Functions
    const modalOverlay = document.getElementById('archModal');
    const modalCloseBtn = document.getElementById('modalClose');

    window.openArchModal = function(blockId) {
        const data = archData[blockId];
        if (!data || !modalOverlay) return;

        document.getElementById('modalTitle').innerText = data.title;
        document.getElementById('modalModule').innerText = data.module;
        document.getElementById('modalPrimitives').innerText = data.primitives;
        document.getElementById('modalDatawidth').innerText = data.datawidth;
        document.getElementById('modalCycles').innerText = data.cycles;
        document.getElementById('modalDesc').innerText = data.description;

        modalOverlay.classList.add('active');

        // Highlight active block
        document.querySelectorAll('.arch-block').forEach(b => b.classList.remove('active'));
        const activeBlock = document.querySelector(`[onclick="openArchModal('${blockId}')"]`);
        if (activeBlock) activeBlock.classList.add('active');
    };

    if (modalCloseBtn && modalOverlay) {
        modalCloseBtn.addEventListener('click', () => {
            modalOverlay.classList.remove('active');
        });

        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) {
                modalOverlay.classList.remove('active');
            }
        });
    }

    // 3. Code Copy to Clipboard
    window.copyCode = function(button, codeId) {
        const codeElement = document.getElementById(codeId);
        if (!codeElement) return;

        const textToCopy = codeElement.innerText;
        navigator.clipboard.writeText(textToCopy).then(() => {
            const originalText = button.innerText;
            button.innerText = 'Copied!';
            button.style.background = 'var(--accent-emerald)';
            button.style.color = '#000';
            setTimeout(() => {
                button.innerText = originalText;
                button.style.background = '';
                button.style.color = '';
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy text: ', err);
        });
    };

    // 4. Register Map Search Filter
    const searchInput = document.getElementById('regSearch');
    if (searchInput) {
        searchInput.addEventListener('keyup', (e) => {
            const term = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#regTable tbody tr');

            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                if (text.includes(term)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // 5. Animate Resource Progress Bars on Scroll
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const fills = entry.target.querySelectorAll('.progress-bar-fill');
                fills.forEach(fill => {
                    const width = fill.getAttribute('data-width');
                    fill.style.width = width;
                });
            }
        });
    }, { threshold: 0.2 });

    const resourceGrid = document.querySelector('.resource-grid');
    if (resourceGrid) {
        observer.observe(resourceGrid);
    }

    // 6. Interactive Fixed-Point Q3.13 Quantization Calculator
    window.setQPreset = function(val) {
        const input = document.getElementById('qInputVal');
        if (input) {
            input.value = val;
            window.recalcQ313();
        }
    };

    window.recalcQ313 = function() {
        const input = document.getElementById('qInputVal');
        if (!input) return;
        let val = parseFloat(input.value);
        if (isNaN(val)) val = 0.0;

        // Dynamic range bounds for signed Q3.13: [-4.0, +3.9998779]
        if (val > 3.9998779) val = 3.9998779;
        if (val < -4.0) val = -4.0;

        const scaled = Math.round(val * 8192);
        const int16 = scaled < 0 ? (scaled & 0xFFFF) : scaled;
        const binStr = (int16 >>> 0).toString(2).padStart(16, '0');

        const signBit = binStr[0];
        const intBits = binStr.substring(1, 3);
        const fracBits = binStr.substring(3);

        const hexVal = '0x' + int16.toString(16).toUpperCase().padStart(4, '0');
        const reconVal = scaled / 8192.0;
        const absErr = Math.abs(val - reconVal);

        const elSign = document.getElementById('bitSign');
        const elInt = document.getElementById('bitInt');
        const elFrac = document.getElementById('bitFrac');
        const elHex = document.getElementById('qHexVal');
        const elIntVal = document.getElementById('qIntVal');
        const elRecon = document.getElementById('qReconVal');
        const elErr = document.getElementById('qErrVal');

        if (elSign) elSign.innerText = signBit;
        if (elInt) elInt.innerText = intBits;
        if (elFrac) elFrac.innerText = fracBits;
        if (elHex) elHex.innerText = hexVal;
        if (elIntVal) elIntVal.innerText = scaled.toString();
        if (elRecon) elRecon.innerText = reconVal.toFixed(6);
        if (elErr) elErr.innerText = absErr.toFixed(6);
    };

    const qInput = document.getElementById('qInputVal');
    if (qInput) {
        qInput.addEventListener('input', window.recalcQ313);
        window.recalcQ313();
    }

    // 7. Real-Time In-Browser EEG Simulation & Apnea Detector Controller
    let simRunning = true;
    let simSpeed = 1;
    let simTimeSec = 0.0;
    let simSubject = 'severe';
    let ahiCount = 0;
    let currentApneaDuration = 0.0;
    let inApneaEvent = false;

    const canvas = document.getElementById('eegCanvas');
    const ctx = canvas ? canvas.getContext('2d') : null;
    let bufferPoints = new Array(300).fill(100);

    window.toggleSimPlay = function() {
        simRunning = !simRunning;
        const btn = document.getElementById('simPlayBtn');
        if (btn) {
            btn.innerText = simRunning ? 'Pause Stream' : 'Resume Stream';
        }
    };

    window.resetSimStream = function() {
        simTimeSec = 0.0;
        ahiCount = 0;
        currentApneaDuration = 0.0;
        inApneaEvent = false;
        bufferPoints.fill(100);
        updateSimUI(false);
    };

    window.changeSimSubject = function() {
        const sel = document.getElementById('simSubject');
        if (sel) {
            simSubject = sel.value;
            window.resetSimStream();
        }
    };

    window.setSimSpeed = function(spd) {
        simSpeed = spd;
        document.querySelectorAll('.sim-speed-group .preset-btn').forEach(b => b.classList.remove('active'));
        const activeBtn = document.getElementById(`spd${spd}`);
        if (activeBtn) activeBtn.classList.add('active');
    };

    function updateSimUI(isApnea) {
        const badge = document.getElementById('simClassBadge');
        const text = document.getElementById('simClassText');
        const ahiTxt = document.getElementById('simAhiCount');
        const sevTxt = document.getElementById('simAhiSev');
        const durTxt = document.getElementById('simConsecutiveText');
        const timeTxt = document.getElementById('simTimeElapsed');

        if (badge && text) {
            if (isApnea) {
                badge.className = 'sim-class-badge apnea';
                text.innerText = 'APNEA DETECTED';
            } else {
                badge.className = 'sim-class-badge normal';
                text.innerText = 'NORMAL RESPIRATION';
            }
        }

        if (ahiTxt) ahiTxt.innerText = ahiCount.toString();
        if (durTxt) durTxt.innerText = `Current Apnea Duration: ${currentApneaDuration.toFixed(1)}s`;

        if (sevTxt) {
            if (ahiCount < 5) {
                sevTxt.className = 'ahi-sev-tag normal';
                sevTxt.innerText = 'NORMAL';
            } else if (ahiCount < 15) {
                sevTxt.className = 'ahi-sev-tag mild';
                sevTxt.innerText = 'MILD';
            } else if (ahiCount < 30) {
                sevTxt.className = 'ahi-sev-tag moderate';
                sevTxt.innerText = 'MODERATE';
            } else {
                sevTxt.className = 'ahi-sev-tag severe';
                sevTxt.innerText = 'SEVERE';
            }
        }

        if (timeTxt) {
            const mins = Math.floor(simTimeSec / 60);
            const secs = Math.floor(simTimeSec % 60);
            const frac = Math.floor((simTimeSec % 1) * 10);
            timeTxt.innerText = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${frac}`;
        }

        // Layer Activation Bars
        const l1 = document.getElementById('l1ActBar');
        const l2 = document.getElementById('l2ActBar');
        const l3 = document.getElementById('l3ActBar');
        const l4 = document.getElementById('l4ActBar');
        const v1 = document.getElementById('l1ActVal');
        const v2 = document.getElementById('l2ActVal');
        const v3 = document.getElementById('l3ActVal');
        const v4 = document.getElementById('l4ActVal');

        const p1 = Math.min(100, Math.max(20, Math.round((isApnea ? 35 : 75) + (Math.random() * 15 - 7))));
        const p2 = Math.min(100, Math.max(15, Math.round((isApnea ? 28 : 60) + (Math.random() * 12 - 6))));
        const p3 = Math.min(100, Math.max(10, Math.round((isApnea ? 20 : 48) + (Math.random() * 10 - 5))));
        const p4 = isApnea ? Math.min(100, Math.round(85 + Math.random() * 12)) : Math.min(40, Math.round(15 + Math.random() * 10));

        if (l1) l1.style.width = `${p1}%`;
        if (l2) l2.style.width = `${p2}%`;
        if (l3) l3.style.width = `${p3}%`;
        if (l4) l4.style.width = `${p4}%`;
        if (v1) v1.innerText = `${p1}%`;
        if (v2) v2.innerText = `${p2}%`;
        if (v3) v3.innerText = `${p3}%`;
        if (v4) v4.innerText = `${p4}%`;
    }

    function renderSimulationFrame() {
        if (!canvas || !ctx) return;

        if (simRunning) {
            const dt = (1.0 / 60.0) * simSpeed;
            simTimeSec += dt;

            // Check if patient is currently in an apnea interval
            let isApnea = false;
            if (simSubject === 'mild') {
                const cycle = simTimeSec % 70;
                isApnea = (cycle >= 40 && cycle <= 54);
            } else if (simSubject === 'severe') {
                const cycle = simTimeSec % 50;
                isApnea = (cycle >= 20 && cycle <= 42);
            }

            if (isApnea) {
                currentApneaDuration += dt;
                if (currentApneaDuration >= 10.0 && !inApneaEvent) {
                    inApneaEvent = true;
                    ahiCount += 1;
                }
            } else {
                currentApneaDuration = 0.0;
                inApneaEvent = false;
            }

            // Generate synthetic EEG sample
            const t = simTimeSec;
            let val;
            if (isApnea) {
                // Flatlined/attenuated amplitude during apnea
                val = 0.12 * Math.sin(2 * Math.PI * 8 * t) + (Math.random() - 0.5) * 0.08;
            } else {
                // Normal cortical rhythm: 10 Hz alpha wave + 2 Hz slow delta
                val = Math.sin(2 * Math.PI * 10 * t) + 0.45 * Math.sin(2 * Math.PI * 2 * t + 0.3) + (Math.random() - 0.5) * 0.25;
            }

            // Map val [-2.0, 2.0] to canvas pixel y [10, 190]
            const yPixel = 100 - val * 45;
            bufferPoints.shift();
            bufferPoints.push(yPixel);

            if (Math.floor(simTimeSec * 10) % 3 === 0) {
                updateSimUI(isApnea);
            }
        }

        // Draw Canvas Grid & Oscilloscope Trace
        ctx.fillStyle = '#06090e';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Draw Grid Lines
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
        ctx.lineWidth = 1;
        for (let x = 0; x < canvas.width; x += 40) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, canvas.height);
            ctx.stroke();
        }
        for (let y = 0; y < canvas.height; y += 40) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(canvas.width, y);
            ctx.stroke();
        }

        // Draw Center Baseline
        ctx.strokeStyle = 'rgba(59, 130, 246, 0.2)';
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(0, 100);
        ctx.lineTo(canvas.width, 100);
        ctx.stroke();
        ctx.setLineDash([]);

        // Draw Glowing Waveform
        const dx = canvas.width / (bufferPoints.length - 1);
        ctx.beginPath();
        ctx.moveTo(0, bufferPoints[0]);
        for (let i = 1; i < bufferPoints.length; i++) {
            ctx.lineTo(i * dx, bufferPoints[i]);
        }

        const isApneaNow = (currentApneaDuration > 0.5);
        ctx.strokeStyle = isApneaNow ? '#ef4444' : '#10b981';
        ctx.shadowColor = isApneaNow ? '#ef4444' : '#10b981';
        ctx.shadowBlur = 8;
        ctx.lineWidth = 2.2;
        ctx.stroke();
        ctx.shadowBlur = 0;

        requestAnimationFrame(renderSimulationFrame);
    }

    if (canvas) {
        requestAnimationFrame(renderSimulationFrame);
    }

    // 8. Dynamic Multi-Board FPGA Resource Scalability Estimator
    const boardDB = {
        'zedboard': { name: 'ZedBoard (XC7Z020)', lut: 53200, ff: 106400, dsp: 220, bram: 140 },
        'pynqz2':   { name: 'PYNQ-Z2 (XC7Z020)', lut: 53200, ff: 106400, dsp: 220, bram: 140 },
        'basys3':   { name: 'Basys 3 (XC7A35T)', lut: 20800, ff: 41600,  dsp: 90,  bram: 50 },
        'kria':     { name: 'Kria KV260 (XCK26)', lut: 117120, ff: 234240, dsp: 1248, bram: 144 },
        'ultra96':  { name: 'Ultra96-V2 (ZU3EG)', lut: 70560, ff: 141120, dsp: 360, bram: 216 }
    };

    const archModes = {
        'default': { lut: 6290, ff: 6653, dsp: 160, bram: 15.0 },
        'signed':  { lut: 6290, ff: 6653, dsp: 80,  bram: 15.0 },
        'int8':    { lut: 4180, ff: 3840, dsp: 40,  bram: 7.5 }
    };

    window.recalcBoardResources = function() {
        const bSel = document.getElementById('boardSelect');
        const oSel = document.getElementById('optimSelect');
        if (!bSel || !oSel) return;

        const board = boardDB[bSel.value] || boardDB['zedboard'];
        const mode = archModes[oSel.value] || archModes['signed'];

        const lutPct = ((mode.lut / board.lut) * 100).toFixed(1);
        const ffPct = ((mode.ff / board.ff) * 100).toFixed(1);
        const dspPct = ((mode.dsp / board.dsp) * 100).toFixed(1);
        const bramPct = ((mode.bram / board.bram) * 100).toFixed(1);

        const elLutVal = document.getElementById('boardLutVal');
        const elLutBar = document.getElementById('boardLutBar');
        const elFfVal = document.getElementById('boardFfVal');
        const elFfBar = document.getElementById('boardFfBar');
        const elDspVal = document.getElementById('boardDspVal');
        const elDspBar = document.getElementById('boardDspBar');
        const elBramVal = document.getElementById('boardBramVal');
        const elBramBar = document.getElementById('boardBramBar');

        if (elLutVal) elLutVal.innerText = `${mode.lut.toLocaleString()} / ${board.lut.toLocaleString()} (${lutPct}%)`;
        if (elLutBar) elLutBar.style.width = `${Math.min(100, lutPct)}%`;

        if (elFfVal) elFfVal.innerText = `${mode.ff.toLocaleString()} / ${board.ff.toLocaleString()} (${ffPct}%)`;
        if (elFfBar) elFfBar.style.width = `${Math.min(100, ffPct)}%`;

        if (elDspVal) elDspVal.innerText = `${mode.dsp} / ${board.dsp} (${dspPct}%)`;
        if (elDspBar) {
            elDspBar.style.width = `${Math.min(100, dspPct)}%`;
            elDspBar.style.background = (dspPct > 80) ? '#f87171' : 'var(--accent-emerald)';
        }

        if (elBramVal) elBramVal.innerText = `${mode.bram} / ${board.bram} (${bramPct}%)`;
        if (elBramBar) elBramBar.style.width = `${Math.min(100, bramPct)}%`;
    };

    // 9. Clinical Confusion Matrix & Threshold Tuning Controller
    window.recalcConfusion = function() {
        const slider = document.getElementById('thresholdSlider');
        const disp = document.getElementById('threshDisplay');
        if (!slider) return;

        const tau = parseFloat(slider.value);
        if (disp) disp.innerText = tau.toFixed(2);

        // N = 1200 total (1000 Normal, 200 Apnea)
        // Shifting threshold changes sensitivity vs specificity
        const totalPos = 200;
        const totalNeg = 1000;

        // Model sigmoidal response: higher tau reduces false positives but increases false negatives
        const sens = Math.max(0.60, Math.min(0.96, 0.835 - (tau - 0.50) * 0.45));
        const spec = Math.max(0.95, Math.min(0.999, 0.998 + (tau - 0.50) * 0.02));

        const tp = Math.round(totalPos * sens);
        const fn = totalPos - tp;
        const tn = Math.round(totalNeg * spec);
        const fp = totalNeg - tn;

        const precision = tp / (tp + fp + 1e-12);
        const balAcc = 0.5 * (sens + spec);
        const f1 = 2 * (precision * sens) / (precision + sens + 1e-12);

        const elTN = document.getElementById('cmTN');
        const elFP = document.getElementById('cmFP');
        const elFN = document.getElementById('cmFN');
        const elTP = document.getElementById('cmTP');
        const elRecall = document.getElementById('cmRecall');
        const elSpec = document.getElementById('cmSpec');
        const elBalAcc = document.getElementById('cmBalAcc');
        const elF1 = document.getElementById('cmF1');

        if (elTN) elTN.innerText = `${tn} (TN)`;
        if (elFP) elFP.innerText = `${fp} (FP)`;
        if (elFN) elFN.innerText = `${fn} (FN)`;
        if (elTP) elTP.innerText = `${tp} (TP)`;

        if (elRecall) elRecall.innerText = `${(sens * 100).toFixed(1)}%`;
        if (elSpec) elSpec.innerText = `${(spec * 100).toFixed(1)}%`;
        if (elBalAcc) elBalAcc.innerText = `${(balAcc * 100).toFixed(1)}%`;
        if (elF1) elF1.innerText = f1.toFixed(3);
    };

    // Initial trigger
    window.recalcBoardResources();
    window.recalcConfusion();
});




// Real-time canvas visualizer enabled
