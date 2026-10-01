# NeuroSomno-HDL: Sleep Apnea Detection on FPGA using Hybrid CNN

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="License: MIT">
  <img src="https://img.shields.io/badge/CI-RTL%20Simulation-success.svg?style=for-the-badge" alt="CI: RTL Simulation">
  <img src="https://img.shields.io/badge/Platform-MATLAB%20R2023b-orange.svg?style=for-the-badge" alt="Platform: MATLAB">
  <img src="https://img.shields.io/badge/Simulation-Xilinx%20Vivado%202023.1-blue.svg?style=for-the-badge" alt="Simulation: Vivado">
  <img src="https://img.shields.io/badge/Target-Zynq--7000%20ZedBoard-red.svg?style=for-the-badge" alt="Target: Zynq">
  <img src="https://img.shields.io/badge/GitHub%20Pages-Live%20Dashboard-brightgreen.svg?style=for-the-badge" alt="GitHub Pages: Live Dashboard">
</p>

NeuroSomno-HDL is an edge-intelligent, software-only FPGA simulation framework designed for real-time sleep apnea detection using EEG signals. The system processes raw biosignals, trains a hybrid 1D Convolutional Neural Network (1D-CNN) classifier in MATLAB, and implements a quantized, pipelined feed-forward neural network accelerator in Verilog HDL.

This repository provides a complete, hardware-independent simulation pipeline that can be executed entirely in software using MATLAB and Xilinx Vivado.

---

## Author & Repository Info

*   **Author:** Aishik Tokdar
*   **Repository URL:** [https://github.com/AishikTokdar/NeuroSomno-HDL](https://github.com/AishikTokdar/NeuroSomno-HDL)
*   **Live Interactive Dashboard:** [https://aishiktokdar.github.io/NeuroSomno-HDL/](https://aishiktokdar.github.io/NeuroSomno-HDL/)

---

## Document Navigation

*   [System Architecture Overview](docs/architecture_overview.md) — Pipelined dataflow, latency calculations, and AXI register maps.
*   [EEG Dataset Configuration](dataset/README.md) — UCDDB channel configurations and synthetic generator instructions.
*   [MATLAB Preprocessing Pipeline](matlab_preprocessing/README.md) — Filtering mathematics, SMOTE balancing, and model export.
*   [Python & PyTorch Biosignal Pipeline](python_pipeline/README.md) — FOSS pipeline, PyTorch training, and bit-true emulator.
*   [Hardware RTL & Simulation Reference](hardware/README.md) — Verilog module hierarchy, state machines, and waveform viewing.
*   [Memory Initialization Guide](hardware/mif/README.md) — Specifications for `.mif`, `sig_rom.mem`, and test vectors.
*   [Embedded Edge Deployment & Drivers](embedded/README.md) — PYNQ-Z2 overlay Python API and standalone ARM Cortex-A9 C driver.
*   [Interactive PYNQ-Z2 Jupyter Demo](embedded/pynq/demo_inference.ipynb) — Step-by-step edge hardware execution notebook.
*   [Validation Results & Synthesis Reports](results/README.md) — Accuracy benchmarks, power budgets, and FPGA resource utilization.
*   [Vivado Synthesis & Accuracy Validation Report](docs/synthesis_and_accuracy_validation.md) — LUT/FF/DSP/BRAM breakdown and simulation accuracy verification.
*   [Automated RTL CI Workflow](.github/workflows/rtl_ci.yml) — GitHub Actions automated simulation pipeline.

---

## Repository Structure & File Map

*   **Automation & Continuous Integration**
    *   [`.github/workflows/rtl_ci.yml`](.github/workflows/rtl_ci.yml) — Automated RTL simulation CI workflow
    *   [`run_all.sh`](run_all.sh) — Cross-platform Bash launcher (Linux / macOS)
    *   [`run_all.ps1`](run_all.ps1) — Automated PowerShell launcher (Windows)
    *   [`run_all.bat`](run_all.bat) — Automated Command Prompt batch script (Windows)
    *   [`LICENSE`](LICENSE) — MIT open-source license
*   **Web Dashboard & Visualizers**
    *   [`index.html`](index.html) — Live interactive browser dashboard
    *   [`style.css`](style.css) — Dashboard stylesheet and design system
    *   [`app.js`](app.js) — Signal generator, Q3.13 converter, and FPGA resource estimator
*   **Dataset**
    *   [`dataset/README.md`](dataset/README.md) — PhysioNet UCDDB setup and synthetic generator guide
*   **Engineering Documentation**
    *   [`docs/architecture_overview.md`](docs/architecture_overview.md) — Pipelined hardware architecture and register map
    *   [`docs/synthesis_and_accuracy_validation.md`](docs/synthesis_and_accuracy_validation.md) — Synthesis report and DSP optimization report
*   **MATLAB Preprocessing Suite**
    *   [`matlab_preprocessing/README.md`](matlab_preprocessing/README.md) — MATLAB pipeline documentation
    *   [`matlab_preprocessing/extract_channels.m`](matlab_preprocessing/extract_channels.m) — Channel extraction script
    *   [`matlab_preprocessing/preprocess_eeg.m`](matlab_preprocessing/preprocess_eeg.m) — 50 Hz notch & 0.5–45 Hz bandpass filtering
    *   [`matlab_preprocessing/segment_eeg.m`](matlab_preprocessing/segment_eeg.m) — 11-second sliding window segmentation
    *   [`matlab_preprocessing/normalize_zscore.m`](matlab_preprocessing/normalize_zscore.m) — Z-score normalization function
    *   [`matlab_preprocessing/handle_imbalance.m`](matlab_preprocessing/handle_imbalance.m) — SMOTE k-NN minority oversampling
    *   [`matlab_preprocessing/train_1dcnn.m`](matlab_preprocessing/train_1dcnn.m) — 1D-CNN and FCN training
    *   [`matlab_preprocessing/extract_weights.m`](matlab_preprocessing/extract_weights.m) — Fixed-point quantization & MIF exporter
*   **Python / PyTorch Pipeline**
    *   [`python_pipeline/README.md`](python_pipeline/README.md) — Python pipeline documentation
    *   [`python_pipeline/requirements.txt`](python_pipeline/requirements.txt) — Minimal Python dependencies
    *   [`python_pipeline/preprocess_eeg.py`](python_pipeline/preprocess_eeg.py) — Python biosignal filtering & segmentation
    *   [`python_pipeline/train_model.py`](python_pipeline/train_model.py) — PyTorch model training with SMOTE
    *   [`python_pipeline/export_weights.py`](python_pipeline/export_weights.py) — Q3.13 weight quantization & MIF exporter
    *   [`python_pipeline/verify_quantization.py`](python_pipeline/verify_quantization.py) — Quantization precision verification
    *   [`python_pipeline/bit_true_emulator.py`](python_pipeline/bit_true_emulator.py) — Bit-true Python RTL golden emulator
*   **Hardware RTL & Simulation**
    *   [`hardware/README.md`](hardware/README.md) — Hardware architecture and simulation guide
    *   [`hardware/rtl/zynet_top.v`](hardware/rtl/zynet_top.v) — Top-level neural network accelerator
    *   [`hardware/rtl/axi_lite_wrapper.v`](hardware/rtl/axi_lite_wrapper.v) — AXI4-Lite register interface
    *   [`hardware/rtl/neuron.v`](hardware/rtl/neuron.v) — Signed Multiply-Accumulate Processing Element
    *   [`hardware/rtl/weight_memory.v`](hardware/rtl/weight_memory.v) — Parameter BRAM storage block
    *   [`hardware/rtl/layer1.v`](hardware/rtl/layer1.v) to [`hardware/rtl/layer4.v`](hardware/rtl/layer4.v) — Pipelined feed-forward layers
    *   [`hardware/rtl/sig_rom.v`](hardware/rtl/sig_rom.v) — Sigmoid activation lookup table module
    *   [`hardware/rtl/relu.v`](hardware/rtl/relu.v) — ReLU activation module
    *   [`hardware/rtl/find_max_out.v`](hardware/rtl/find_max_out.v) — Sequential argmax comparator
    *   [`hardware/rtl/ahi_tracker.v`](hardware/rtl/ahi_tracker.v) — Real-time Apnea-Hypopnea Index tracker IP
    *   [`hardware/rtl/conv1d_pe.v`](hardware/rtl/conv1d_pe.v) — Streaming 1D Convolution PE
    *   [`hardware/rtl/maxpool1d.v`](hardware/rtl/maxpool1d.v) — Streaming 1D Max Pooling module
    *   [`hardware/rtl/iir_notch_50hz.v`](hardware/rtl/iir_notch_50hz.v) — Hardware 50 Hz notch filter
    *   [`hardware/rtl/iir_bandpass.v`](hardware/rtl/iir_bandpass.v) — Hardware 0.5–45 Hz bandpass filter
    *   [`hardware/tb/tb_top_sim.v`](hardware/tb/tb_top_sim.v) — Self-checking behavioral testbench
    *   [`hardware/constraints/zedboard.xdc`](hardware/constraints/zedboard.xdc) — Physical pin constraints & clock timing
    *   [`hardware/mif/README.md`](hardware/mif/README.md) — Pre-quantized MIF parameter directory
    *   [`hardware/mif/sig_rom.mem`](hardware/mif/sig_rom.mem) — Sigmoid ROM lookup table
    *   [`hardware/mif/test_data.txt`](hardware/mif/test_data.txt) — 30-sample behavioral test vectors
    *   [`hardware/mif/test_labels.txt`](hardware/mif/test_labels.txt) — Ground-truth labels
*   **Embedded Edge Drivers**
    *   [`embedded/README.md`](embedded/README.md) — Embedded deployment guide & memory map
    *   [`embedded/pynq/neurosomno_overlay.py`](embedded/pynq/neurosomno_overlay.py) — PYNQ Python overlay driver
    *   [`embedded/pynq/demo_inference.ipynb`](embedded/pynq/demo_inference.ipynb) — Interactive Jupyter demonstration notebook
    *   [`embedded/c_driver/neurosomno_hw.h`](embedded/c_driver/neurosomno_hw.h) — C driver register header & bitmasks
    *   [`embedded/c_driver/neurosomno_api.c`](embedded/c_driver/neurosomno_api.c) — Bare-metal ARM Cortex-A9 C driver
*   **Results & Reports**
    *   [`results/README.md`](results/README.md) — FPGA device utilization and power analysis

---

## System Overview

```
EEG Signal (EDF)
      │
      ▼
[MATLAB Preprocessing]
  ├── Artifact removal (IIR Notch filter @ 50 Hz)
  ├── Bandpass filter (Butterworth 4th-order @ 0.5-45 Hz)
  ├── Segmentation (11s windows, 10s overlap @ 128 Hz -> 2816 samples)
  ├── Z-score normalization (Zero-mean, unit-variance)
  └── Class imbalance handling (SMOTE k-NN neighborhood interpolation)
      │
      ▼
[1D-CNN Training (MATLAB)]
  ├── 15-layer hybrid architecture
  ├── Binary classification (Apnea vs Normal respiration)
  ├── 65,185 trainable parameters
  └── Accuracy: 99.62% (with SMOTE)
      │
      ▼
[Weight Extraction & Quantization]
  └── Fixed-point quantization (16-bit signed: Q3.13 format)
      │
      ▼
[Verilog Hardware Accelerator (Vivado Simulation)]
  ├── Feed-forward fully connected network (30-30-10-10 neurons)
  ├── Fully simulated in Xilinx Vivado (no physical hardware required)
  ├── AXI-Lite register interface for weight configuration & control
  └── Quantized model accuracy: 89.00% (Simulation subset: 86.67% - 90.00%)
```

---

## System Requirements & Toolchain Verification

NeuroSomno-HDL supports both **Proprietary Vendor Toolchains** (Primary Default) and **100% Free & Open-Source (FOSS) Software** (Alternative Suite).

### Primary Default Toolchain (Vendor Recommended)
*   **Operating System:** Windows 10/11 or Ubuntu 20.04/22.04 LTS.
*   **MATLAB Version:** [MATLAB R2023b or newer](https://www.mathworks.com/products/matlab.html).
    *   *Required Toolboxes:* Deep Learning Toolbox, Fixed-Point Designer, Signal Processing Toolbox.
    *   *Verification:* Type `ver` in the MATLAB Command Window.
*   **Vivado Version:** [Xilinx Vivado 2023.1 or newer](https://www.xilinx.com/products/design-tools/vivado.html).
    *   *Verification:* Ensure `vivado` is added to system `PATH` or launch via Vivado GUI.

### Open-Source Toolchain Suite (100% Free Alternative)

You can run, simulate, synthesize, and verify this entire repository using free open-source tools without any proprietary software licenses:

| Software Tool | Primary Purpose in Project | Web & Download Link |
| :--- | :--- | :--- |
| **Icarus Verilog (`iverilog`)** | Verilog RTL IEEE-1364 behavioral simulator engine | [steveicarus.github.io/iverilog](https://steveicarus.github.io/iverilog/) |
| **GTKWave** | Graphical digital waveform visualizer (`.vcd` output) | [gtkwave.sourceforge.net](http://gtkwave.sourceforge.net/) |
| **Yosys** | Open-source RTL logic synthesis suite & gate analysis | [yosyshq.net/yosys](https://yosyshq.net/yosys/) |
| **GNU Octave** | Free drop-in MATLAB-compatible numerical framework | [gnu.org/software/octave](https://www.gnu.org/software/octave/) |
| **Python 3.x** | Open-source machine learning & biosignal processing | [python.org](https://www.python.org/) |
| **Verilator** *(Optional)* | High-performance C++ cycle-accurate simulator | [veripool.org/verilator](https://www.veripool.org/verilator/) |

---

## Key Results

### Software Model Performance (MATLAB / Octave)

| Metric | Random Oversampling | SMOTE |
| :--- | :---: | :---: |
| **Accuracy** | 99.53% | **99.62%** |
| **Balanced Accuracy** | 91.23% | **91.58%** |
| **Sensitivity (Recall)** | 82.61% | **83.33%** |
| **Specificity** | **99.85%** | 99.84% |
| **Precision** | **91.57%** | 86.96% |
| **F1 Score** | **0.8686** | 0.8511 |

### Hardware Accelerator Performance (Vivado / Icarus Verilog Simulation)

| Metric | Neuron Module | Full FCN Accelerator |
| :--- | :---: | :---: |
| **Worst Negative Slack (WNS)** | 4.571 ns | 4.156 ns |
| **Total Estimated Power** | 0.157 W | 0.368 W |
| **LUT Utilization** | 51 / 53200 (0.10%) | 6290 / 53200 (11.82%) |
| **FF Utilization** | 43 / 106400 (0.04%) | 6653 / 106400 (6.25%) |
| **DSP Utilization** | 2 / 220 (0.91%) | 160 / 220 (72.73%) *[1]* |
| **BRAM Utilization** | 0.50 / 140 (0.36%) | 15 / 140 (10.71%) *[2]* |
| **Quantized Model Accuracy (Full)** | — | **89.00%** |
| **Simulation Accuracy (30-sample subset)** | — | **86.67% - 90.00%** |

*[1] Theoretical minimum is 80 DSPs (1 per neuron). Vivado infers 2 DSPs per neuron due to port signedness and register packing constraints.*
*[2] Sigmoid ROMs are synthesized as Distributed ROM using LUTs. If mapped to BRAM, utilization is 25 BRAMs.*

---

## Complete Step-by-Step Execution Guide

Follow these steps to run the dataset preprocessing, train the model, extract weights, and execute the RTL behavioral simulation to obtain the **86.67% - 90.00%** simulation accuracy (representing the 89.00% quantized network accuracy).

### 1. Automated Pipeline Execution (Windows, Linux & macOS)

The cross-platform launcher scripts automatically detect installed software (MATLAB vs GNU Octave for Phase 1, and Vivado vs Icarus Verilog / Yosys for Phase 2). If no simulation or preprocessing environment is installed, pre-quantized parameter files in [`hardware/mif/`](hardware/mif/README.md) are automatically utilized.

*   **Linux / macOS / WSL / Git Bash:**
    ```bash
    chmod +x run_all.sh
    ./run_all.sh
    ```
    Script source: [`run_all.sh`](run_all.sh)
*   **Windows PowerShell:**
    ```powershell
    powershell -ExecutionPolicy Bypass -File .\run_all.ps1
    ```
    Script source: [`run_all.ps1`](run_all.ps1)
*   **Windows Command Prompt (CMD):**
    ```cmd
    run_all.bat
    ```
    Script source: [`run_all.bat`](run_all.bat)

---

### 2. Manual Execution Guide

#### Phase 1: Set Up Repository & Dataset

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/AishikTokdar/NeuroSomno-HDL.git
    cd NeuroSomno-HDL
    ```
2.  **Prepare Dataset**:
    *   **Option A (UCDDB Database):** Download `.edf` records from the [PhysioNet UCDDB Database](https://physionet.org/content/ucddb/1.0.0/) and place inside [`dataset/`](dataset/README.md).
    *   **Option B (Synthetic Generation):** If no `.edf` files are present, the preprocessing pipeline automatically generates structured synthetic signals for full verification without downloading external data.

---

#### Phase 2: Signal Preprocessing & Quantization

##### Option A: MATLAB R2023b (Primary Default)
Open MATLAB, navigate to [`matlab_preprocessing/`](matlab_preprocessing/README.md), and run:
```matlab
run('preprocess_eeg.m');
run('segment_eeg.m');
run('handle_imbalance.m');
run('train_1dcnn.m');
run('extract_weights.m');
```
Scripts executed:
*   [`matlab_preprocessing/preprocess_eeg.m`](matlab_preprocessing/preprocess_eeg.m) — Filtering and artifact removal
*   [`matlab_preprocessing/segment_eeg.m`](matlab_preprocessing/segment_eeg.m) — 11-second sliding window segmentation
*   [`matlab_preprocessing/handle_imbalance.m`](matlab_preprocessing/handle_imbalance.m) — SMOTE k-NN balancing
*   [`matlab_preprocessing/train_1dcnn.m`](matlab_preprocessing/train_1dcnn.m) — Model training
*   [`matlab_preprocessing/extract_weights.m`](matlab_preprocessing/extract_weights.m) — Fixed-point quantization & MIF exporter

##### Option B: GNU Octave (Open-Source Free Alternative)
Install GNU Octave via package manager (`sudo apt install octave` or `brew install octave` or `choco install octave`) and run:
```bash
octave --no-gui --eval "run('matlab_preprocessing/preprocess_eeg.m'); run('matlab_preprocessing/segment_eeg.m'); run('matlab_preprocessing/handle_imbalance.m'); run('matlab_preprocessing/train_1dcnn.m'); run('matlab_preprocessing/extract_weights.m');"
```

##### Option C: Python 3.x / PyTorch (100% Free & Open-Source)
Run the complete Python biosignal preprocessing, SMOTE balancing, PyTorch model training, Q3.13 MIF export, and bit-true emulation:
```bash
pip install -r python_pipeline/requirements.txt
python python_pipeline/preprocess_eeg.py
python python_pipeline/train_model.py
python python_pipeline/export_weights.py
python python_pipeline/verify_quantization.py
python python_pipeline/bit_true_emulator.py
```
Scripts executed:
*   [`python_pipeline/requirements.txt`](python_pipeline/requirements.txt) — Dependency specifications
*   [`python_pipeline/preprocess_eeg.py`](python_pipeline/preprocess_eeg.py) — 50 Hz notch & 0.5–45 Hz bandpass filtering
*   [`python_pipeline/train_model.py`](python_pipeline/train_model.py) — PyTorch 1D-CNN & FCN training with SMOTE
*   [`python_pipeline/export_weights.py`](python_pipeline/export_weights.py) — Q3.13 weight quantization & MIF generator
*   [`python_pipeline/verify_quantization.py`](python_pipeline/verify_quantization.py) — Numerical bounds & error verification
*   [`python_pipeline/bit_true_emulator.py`](python_pipeline/bit_true_emulator.py) — Golden RTL bit-true verification emulator

---

#### Phase 3: Hardware RTL Simulation & Synthesis

> [!NOTE]
> **Out-of-the-Box Hardware Simulation**:
> All 164 pre-extracted memory initialization files (`.mif`), activation lookup tables ([`sig_rom.mem`](hardware/mif/sig_rom.mem)), and test vectors ([`test_data.txt`](hardware/mif/test_data.txt), [`test_labels.txt`](hardware/mif/test_labels.txt)) are already included in [`hardware/mif/`](hardware/mif/README.md). You can skip Phase 2 and proceed directly to Phase 3 to simulate the hardware accelerator out-of-the-box.

##### Option A: Xilinx Vivado (Primary Default)

*   **GUI Mode:**
    1. Open Vivado and create project `NeuroSomno_HDL` in the root folder.
    2. Add [`hardware/rtl/*.v`](hardware/rtl/) as **Design Sources**, [`hardware/tb/*.v`](hardware/tb/) as **Simulation Sources**, and [`hardware/constraints/zedboard.xdc`](hardware/constraints/zedboard.xdc) as **Constraints**.
    3. In **Simulation Settings**, set **Simulation Run Directory** to [`hardware/mif/`](hardware/mif/README.md).
    4. Click **Run Simulation** -> **Run Behavioral Simulation**, then run `run -all` in the Tcl console.
*   **Batch CLI Mode:**
    ```bash
    vivado -mode batch -source -eval "create_project -force NeuroSomno_HDL ./vivado_proj -part xc7z020clg484-1; add_files [glob ./hardware/rtl/*.v]; add_files -fileset sim_1 [glob ./hardware/tb/*.v]; set_property top tb_top_sim [get_filesets sim_1]; launch_simulation; run -all; exit"
    ```

##### Option B: Icarus Verilog + GTKWave (Open-Source CLI Simulation)

Install Icarus Verilog & GTKWave (`sudo apt install iverilog gtkwave` or `brew install icarus-verilog gtkwave`):

1.  **Compile & Run Simulation**:
    ```bash
    cd hardware/mif
    iverilog -g2012 -I ../rtl -o sim_top ../rtl/*.v ../tb/tb_top_sim.v
    vvp sim_top
    ```
2.  **View Waveform Traces in GTKWave**:
    To inspect signals graphically, dump waveforms during simulation and open in GTKWave:
    ```bash
    gtkwave dump.vcd
    ```

##### Option C: Yosys Open-Source Synthesis Check

Install Yosys (`sudo apt install yosys` or `brew install yosys` or `choco install yosys`) to check logic gate count and synthesizability:
```bash
yosys -p "read_verilog -sv hardware/rtl/*.v; synth_xilinx -top zynet_top; stat"
```

---

#### Verification of Simulation Results
Regardless of whether you run Vivado or Icarus Verilog ([`hardware/tb/tb_top_sim.v`](hardware/tb/tb_top_sim.v)), the console will print predictions against actual sample labels:
```text
Sample 0: Pred = 0, Act = 0
Sample 1: Pred = 1, Act = 1
...
Sample 29: Pred = 0, Act = 0
Overall Accuracy: 90.000000 (or 86.666667)
```
> [!TIP]
> The simulation prints an overall accuracy of **90.00%** (27/30 correct) or **86.67%** (26/30 correct), matching the full 89.00% dataset quantized accuracy evaluated over this 30-sample behavioral testbench.

---

#### Phase 4: Embedded Edge Deployment (PYNQ / ARM Cortex-A9)

For physical hardware deployment on Xilinx Zynq-7000 SoC boards (ZedBoard / PYNQ-Z2), see the [Embedded Edge Deployment Guide](embedded/README.md):

*   **Option A: PYNQ Python Overlay**
    *   Driver API: [`embedded/pynq/neurosomno_overlay.py`](embedded/pynq/neurosomno_overlay.py)
    *   Interactive Walkthrough: [`embedded/pynq/demo_inference.ipynb`](embedded/pynq/demo_inference.ipynb)
*   **Option B: Standalone ARM Cortex-A9 C Driver**
    *   Hardware Header & Offsets: [`embedded/c_driver/neurosomno_hw.h`](embedded/c_driver/neurosomno_hw.h)
    *   C API Implementation: [`embedded/c_driver/neurosomno_api.c`](embedded/c_driver/neurosomno_api.c)

---

## Visualizing Waveforms in Vivado

For visual waveform setup in Vivado GUI, see the signal trace guide in [Hardware RTL & Simulation Reference](hardware/README.md#visualizing-waveforms).

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
