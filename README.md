# NeuroSomno-HDL

An experimental edge-intelligent EEG sleep apnea classifier featuring PyTorch training, fixed-point Q3.13 weight quantization, and an RTL hardware accelerator implemented in synthesizable Verilog HDL.

The active inference hardware implements a **784-30-30-10-2 fully connected neural network (FCN)** with signed 16-bit Q3.13 fixed-point arithmetic. Class output `0` corresponds to normal respiration, and class output `1` corresponds to an apnea event.

The software regression suite, integer/RTL comparisons and synthesis mapping pass. MATLAB execution, physical board integration, vendor place-and-route timing/power analysis and annotated real-patient evaluation remain unverified.

---

## Contents

- [Results and Metrics](#results-and-metrics)
  - [Hardware and Verification Parity](#hardware-and-verification-parity)
  - [Classification Performance](#classification-performance)
  - [Synthesis Cell Mapping](#synthesis-cell-mapping)
- [Quick Start](#quick-start)
- [Pipeline Architecture](#pipeline-architecture)
  - [Network Topology](#network-topology)
  - [Fixed-Point Arithmetic](#fixed-point-arithmetic)
  - [Data Contract and Biosignal Preprocessing](#data-contract-and-biosignal-preprocessing)
- [Python ML Workflow](#python-ml-workflow)
  - [Preprocessing, Training, and Export](#preprocessing-training-and-export)
  - [Memory and Weight Validation](#memory-and-weight-validation)
  - [Bit-True Software Emulation](#bit-true-software-emulation)
- [Hardware Simulation and Verification](#hardware-simulation-and-verification)
  - [Behavioral Simulation with Icarus Verilog](#behavioral-simulation-with-icarus-verilog)
  - [RTL Golden Reference Parity](#rtl-golden-reference-parity)
  - [AXI-Lite Control and AXI-Stream Data Contract](#axi-lite-control-and-axi-stream-data-contract)
- [Embedded Driver APIs](#embedded-driver-apis)
  - [PYNQ-Z2 Python Overlay Driver](#pynq-z2-python-overlay-driver)
  - [C Driver Interface](#c-driver-interface)
- [MATLAB Workflow](#matlab-workflow)
- [Project Layout](#project-layout)
- [Deployment Constraints](#deployment-constraints)
- [License](#license)

---

## Results and Metrics

All validation figures reflect evaluation against synthetic biosignal datasets generated using realistic cortical EEG characteristics (10 Hz alpha rhythm, 2 Hz slow delta activity, and 30-second apnea attenuation intervals). The software evaluation cohort comprises 590 test windows from a subject completely separated from training and validation. The 30 RTL testbench frames represent a sampled evaluation subset.

### Hardware and Verification Parity

| Check | Metric / Condition | Status |
|---|---|:---:|
| Unit and regression test suite | 30 regression tests (`tests/audit_project.py`) | Pass |
| Results dashboard checks | 5 functional verifications | Pass |
| RTL vs. bit-true integer emulator | 2,160 individual neuron comparisons across 30 frames | 0 mismatches |
| Hardware RTL inference accuracy | 30 / 30 frames correctly identified | 100.00% |
| C driver mock-transport test | Strict C11 build with boundary checks (`tests/test_c_driver.c`) | Pass |
| Memory parameter integrity | 144 MIF files validated against model checkpoint | 0 errors |
| Parameter clipping | 24,812 signed weights and biases mapped to Q3.13 | 0 clipped |
| Maximum quantization rounding error | 0.0000610314; half an LSB is 0.0000610352 | Pass |

### Classification Performance

The software CNN and floating-point FCN were evaluated over 590 held-out synthetic windows. A separate Q3.13 integer-reference evaluation covers the same 590 windows. The 30-frame RTL run is a smaller, distinct evaluation.

| Metric | Software 1D-CNN | FCN (floating point) |
|---|---:|---:|
| Accuracy | 97.63% | 98.98% |
| Balanced Accuracy | 95.33% | 98.00% |
| Sensitivity (Recall) | 90.67% | 96.00% |
| Specificity | 100.00% | 100.00% |
| Precision | 100.00% | 100.00% |
| F1 Score | 0.9510 | 0.9796 |

The Q3.13 integer reference scores **98.98% accuracy, 98.00% balanced accuracy,
96.00% sensitivity, 100.00% specificity, 100.00% precision and 0.9796 F1** on the
same 590 windows. It makes the same class decisions as the floating-point FCN.
This is integer software evaluation, not a claim that all 590 frames ran in RTL.
Reproduce it with `python python_pipeline/evaluate_quantized.py`. See
[the integer results](results/verification/quantized_metrics.json).

#### Confusion Matrix Counts (Cohort N = 590)

| Category | Software 1D-CNN | FCN (floating point) |
|---|---:|---:|
| True Negatives (Normal) | 440 | 440 |
| False Positives (Spurious Alarms) | 0 | 0 |
| False Negatives (Missed Apneas) | 14 | 6 |
| True Positives (Correct Apneas) | 136 | 144 |

### Synthesis Cell Mapping

Mapped using Yosys 0.66 targeting Xilinx 7-series FPGA architectural primitives:

| Primitive Element | Cell Count | Description / Role |
|---|---:|---|
| `DSP48E1` | 88 | Pipelined 16-bit signed multipliers in neuron PEs |
| `RAMB18E1` | 40 | Synchronous Block RAM parameter memory tiles |
| `FDCE` / `FDPE` / `FDRE` (Flip-Flops) | 13,837 | Pipeline registers, accumulators, and serializers |
| `LUT` (Logic Cells) | 15,776 | Interconnect multiplexers, activation ROM, control FSM |
| Estimated Logic Cells | 11,102 | Structural logic equivalent |
| Total Active Parameters | 24,812 | 16-bit fixed-point weight and bias words |

---

## Quick Start

### Prerequisites

- **Python 3.10+** with `numpy`, `torch`, `scipy` (install via `python_pipeline/requirements.txt`)
- **Icarus Verilog** (`iverilog`, `vvp`) for RTL compilation and simulation
- **GCC / Clang** for compiling C driver tests
- **Node.js** for frontend checks (Python can serve the static website)
- **Yosys** (optional) for open-source logic synthesis and FPGA cell mapping

### Installation and One-Command Verification

```sh
# Clone repository
git clone https://github.com/AishikTokdar/NeuroSomno-HDL.git
cd NeuroSomno-HDL

# Install Python dependencies
pip install -r python_pipeline/requirements.txt

# Run complete regression suite
python scripts/verify_project.py

# Run memory and parameter validation
python python_pipeline/validate_memory.py

# Run bit-true integer emulator
python python_pipeline/bit_true_emulator.py
```

Automated launcher scripts are provided for cross-platform execution:
- **Linux / macOS:** `./run_all.sh`
- **Windows Command Prompt:** `run_all.bat`
- **Windows PowerShell:** `.\run_all.ps1`

---

## Pipeline Architecture

```
Raw EEG Channels (C3, C4 @ 128 Hz)
          │
          ▼
┌──────────────────────────────┐
│ Preprocessing & Segmentation │ ◄── 11-second sliding windows (1s stride)
└──────────────┬───────────────┘
               │ 2,816 samples interpolated to 784 inputs
               ▼
┌──────────────────────────────┐
│  AXI4-Stream Master (DMA)    │ ◄── 784 transfers of 16-bit Q3.13 words (TLAST on final beat)
└──────────────┬───────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│               NeuroSomno FPGA Accelerator Core                  │
│                                                                 │
│  Layer 1: 30 Neurons  (784 inputs each, ReLU activation)        │
│  Layer 2: 30 Neurons  (30 inputs each,  ReLU activation)        │
│  Layer 3: 10 Neurons  (30 inputs each,  Sigmoid ROM activation) │
│  Layer 4:  2 Neurons  (10 inputs each,  Linear output)          │
│                                                                 │
│  Argmax Module: Compares logits -> Output 0 (Normal) / 1 (Apnea)│
│  AHI Tracker:   Hourly event accumulator & hypoxia duration     │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────┐
│ AXI-Lite Status & Telemetry  │ ◄── Polled by ARM host CPU / PYNQ driver
└──────────────────────────────┘
```

### Network Topology

The accelerator implements a pipelined feed-forward network with 4 layers:

| Layer | Type | Inputs | Neurons | Activation | Weight MIF Files | Bias MIF Files | Total Parameters |
|:---:|:---:|---:|---:|:---:|:---:|:---:|---:|
| 1 | Dense | 784 | 30 | ReLU | `w_1_0.mif` .. `w_1_29.mif` | `b_1_0.mif` .. `b_1_29.mif` | 23,550 |
| 2 | Dense | 30 | 30 | ReLU | `w_2_0.mif` .. `w_2_29.mif` | `b_2_0.mif` .. `b_2_29.mif` | 930 |
| 3 | Dense | 30 | 10 | Sigmoid (ROM) | `w_3_0.mif` .. `w_3_9.mif` | `b_3_0.mif` .. `b_3_9.mif` | 310 |
| 4 | Dense | 10 | 2 | Linear | `w_4_0.mif` .. `w_4_1.mif` | `b_4_0.mif` .. `b_4_1.mif` | 22 |
| **Total** | | | **72** | | **72 files** | **72 files** | **24,812 words** |

### Fixed-Point Arithmetic

All internal weights, biases, and activation values use **signed 16-bit Q3.13 fixed-point format**:
- **Format:** 1 sign bit, 2 integer bits, 13 fractional bits (`1.2.13`)
- **Dynamic range:** $[-4.0, +3.9998779]$
- **Resolution (LSB):** $2^{-13} \approx 0.00012207$
- **Multiplication:** Two 16-bit signed operands produce a 32-bit product with 26 fractional bits, shifted right by 13 bits (`>>> 13`) before accumulation.
- **Sigmoid Activation:** Implemented via a precomputed 1,024-word lookup table (`hardware/mif/sig_rom.mem`). The address index is derived using `((saturated_input >>> 6) + 512) & 1023`.

### Data Contract and Biosignal Preprocessing

1. **Input Sampling:** Raw EEG signals are resampled to 128 Hz.
2. **Filtering:** Bandpass filtering (0.5–45 Hz) isolates clinical cortical brain wave frequencies (delta, theta, alpha, beta), and a 50 Hz digital notch filter eliminates powerline noise.
3. **Segmentation:** Processed into 11-second sliding windows with a 1-second step stride (1,408 samples across 2 differential channels = 2,816 total points per frame).
4. **Rescaling:** Each window is interpolated down to 784 values and quantized to signed 16-bit Q3.13 format.
5. **Patient Separation:** To guarantee statistical independence, patient IDs are partitioned disjointly across train, validation, and test splits prior to window generation.

---

## Python ML Workflow

### Preprocessing, Training, and Export

```sh
# Step 1: Preprocess signals and generate synthetic train/val/test splits
python python_pipeline/preprocess_eeg.py

# Step 2: Train PyTorch 1D-CNN baseline and the 784-input Quantized FCN
python python_pipeline/train_model.py

# Step 3: Quantize floating-point parameters to Q3.13 and export MIF memory files
python python_pipeline/export_weights.py
```

### Memory and Weight Validation

The memory verification script performs structural and numerical checks on all 144 `.mif` files, the sigmoid ROM, and test vectors:

```sh
python python_pipeline/validate_memory.py

# Optional: verify bit-exact correspondence against saved PyTorch checkpoint
python python_pipeline/validate_memory.py --checkpoint models/fcn_model.pt
```

### Bit-True Software Emulation

Before simulating in hardware, execute the integer-exact Python reference model:

```sh
python python_pipeline/bit_true_emulator.py
```

---

## Hardware Simulation and Verification

### Behavioral Simulation with Icarus Verilog

Run simulation from the `hardware/mif/` directory so relative memory paths resolve:

```sh
cd hardware/mif
iverilog -g2012 -s tb_top_sim -o sim_top ../rtl/*.v ../tb/tb_top_sim.v
vvp sim_top
cd ../..
```

View generated waveform traces with GTKWave:

```sh
gtkwave hardware/mif/zynet_top.vcd
```

### RTL Golden Reference Parity

Verify cycle-exact hardware behavior and neuron activation matching:

```sh
python python_pipeline/verify_rtl.py
```

This harness streams 30 test frames into the RTL simulation via standard I/O, captures every intermediate neuron activation across all four layers (2,160 values), and confirms zero deviation from the golden integer reference model.

### AXI-Lite Control and AXI-Stream Data Contract

The accelerator top module (`hardware/rtl/axi_lite_wrapper.v`) interfaces with host processors via two buses:
- **AXI4-Stream Slave:** Consumes 784 consecutive 16-bit Q3.13 samples per frame. Strobe `TLAST` must be asserted strictly on the 784th handshake beat.
- **AXI-Lite Slave (32-bit aligned):** Provides memory-mapped configuration, weight reprogramming, execution start triggers, status polling, and telemetry readings.

For full register definitions, address offsets, and transaction state diagrams, consult [docs/architecture_overview.md](docs/architecture_overview.md).

---

## Embedded Driver APIs

### PYNQ-Z2 Python Overlay Driver

Located at `embedded/pynq/neurosomno_overlay.py`, supporting software-in-the-loop emulation and physical FPGA deployment:

```python
import numpy as np
from embedded.pynq.neurosomno_overlay import NeuroSomnoOverlay

# Initialize driver in emulation mode (or "hardware" with bitstream)
accel = NeuroSomnoOverlay(mode="emulator")

# Create a sample frame (784 signed Q3.13 integers)
test_frame = np.zeros(784, dtype=np.int16)

# Execute inference
predicted_class = accel.predict_sample(test_frame)
print(f"Prediction: {'Apnea (1)' if predicted_class == 1 else 'Normal (0)'}")

# Query cumulative clinical AHI event telemetry
print(f"Cumulative Apneas: {accel.get_ahi_count()}")
print(f"Severity Grade:    {accel.get_severity_grade()}")
```

### C Driver Interface

For bare-metal or FreeRTOS deployments on ARM Cortex-A9 (`embedded/c_driver/neurosomno_api.c`, `neurosomno_hw.h`):

```c
#include "neurosomno_hw.h"

// Initialize accelerator base address and perform soft reset
NeuroSomno_Init(NEUROSOMNO_BASE_ADDR);

// Trigger inference
NeuroSomno_StartInference();

// Poll for completion
while (!NeuroSomno_IsDone());

// Read diagnostic predictions
uint32_t prediction = NeuroSomno_GetPredictedClass(); // 0 = Normal, 1 = Apnea
uint16_t ahi_count   = NeuroSomno_GetAHICount();
AHI_Severity_t sev   = NeuroSomno_GetSeverity();
```

---

## MATLAB Workflow

The `matlab_preprocessing/` directory provides an alternative training and feature extraction pipeline:

```matlab
addpath('matlab_preprocessing');
run('matlab_preprocessing/preprocess_eeg.m');
run('matlab_preprocessing/segment_eeg.m');
run('matlab_preprocessing/handle_imbalance.m');
run('matlab_preprocessing/train_1dcnn.m');
run('matlab_preprocessing/extract_weights.m');
```

*Note: Requires MATLAB R2023b or later with Deep Learning Toolbox, Signal Processing Toolbox, and Fixed-Point Designer.*

---

## Project Layout

```text
NeuroSomno-HDL/
├── .github/workflows/         CI/CD automated regression and deployment workflows
├── docs/
│   └── architecture_overview.md   Detailed AXI register map and hardware interface spec
├── embedded/
│   ├── c_driver/              Standalone C library (neurosomno_api.c, neurosomno_hw.h)
│   └── pynq/                  Python overlay driver and interactive Jupyter demo notebook
├── hardware/
│   ├── constraints/           XDC physical pin and timing constraints for ZedBoard
│   ├── mif/                   144 Q3.13 memory initialization files, ROM, and manifest
│   ├── rtl/                   Synthesizable Verilog HDL modules (FCN core, IIR, PEs)
│   └── tb/                    Verilog testbenches (neuron, conv1d, top simulation)
├── matlab_preprocessing/      MATLAB preprocessing and alternative training scripts
├── python_pipeline/           Python preprocessing, PyTorch training, and verification
├── results/                   Compact test summaries and log archives
├── scripts/                   Automated cross-tool verification runners
├── tests/                     Unit test suite and C driver mock-transport tests
├── app.js                     Interactive signal, architecture and results controls
├── index.html                 Informative project website and Q3.13 explorer
├── run_all.bat                Windows CMD verification launcher
├── run_all.ps1                Windows PowerShell verification launcher
├── run_all.sh                 Linux / macOS Bash verification launcher
└── style.css                  Responsive project website styles
```

---

## Deployment Constraints

1. **Clinical Disclaimers:** All reported performance numbers are generated on synthetic datasets and integer RTL simulation models. They do not constitute certified clinical diagnostics or FDA-approved medical telemetry.
2. **Timing Closure:** Yosys cell mappings demonstrate logic feasibility (DSP/RAM/LUT mapping). Full physical board deployment requires place-and-route timing closure in Vivado.
3. **Telemetry Semantics:** Event counting assumes 1 new second of continuous EEG per inference window. AHI rates report experimental occurrences per observed hour, not full clinical polysomnography measurements.

---

## License

This project is licensed under the [MIT License](LICENSE).

## Website development and deployment

The public page explains the signal pipeline, model architecture, classification
metrics, fixed-point arithmetic and FPGA resource tradeoffs. Developer diagnostics
stay in the repository reports and are not shown in the public page.

```sh
python -m http.server 8765
```

The Pages workflow copies the public assets into a temporary directory, uploads a named
`github-pages` artifact, checks that an artifact ID was produced, and deploys only
after that build completes. The public package excludes RTL sources, model
parameters, test reports and raw logs. A remote deployment must still run after
these workflow changes are pushed.
