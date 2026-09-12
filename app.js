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
});
