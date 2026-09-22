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

For detailed breakdowns of specific project components, refer to the following sub-documents:
*   [System Architecture Overview](docs/architecture_overview.md) â€” Register maps, latency calculations, and layer dataflow logic.
*   [EEG Dataset Configuration](dataset/README.md) â€” Channel configurations and manual download instructions.
*   [MATLAB Preprocessing Pipeline Guide](matlab_preprocessing/README.md) â€” In-depth details on filtering, segmentation, and model training.
*   [Hardware RTL & Simulation Reference](hardware/README.md) â€” Verilog module breakdowns and state machine definitions.
*   [Memory Initialization Guide](hardware/mif/README.md) â€” Specifications for `.mif`, `.mem`, and `.txt` simulator files.
*   [Validation Results & Synthesis Reports](results/README.md) â€” Detailed accuracy metrics, power budgets, and FPGA resource footprints.
*   [Vivado Synthesis & Accuracy Validation Report](docs/synthesis_and_accuracy_validation.md) â€” Detailed resource analysis, LUT/DSP definitions, and simulation accuracy verification.

---

## System Overview

```
EEG Signal (EDF)
      â”‚
      â–¼
[MATLAB Preprocessing]
  â”œâ”€â”€ Artifact removal (IIR Notch filter @ 50 Hz)
  â”œâ”€â”€ Bandpass filter (Butterworth 4th-order @ 0.5-45 Hz)
  â”œâ”€â”€ Segmentation (11s windows, 10s overlap @ 128 Hz -> 2816 samples)
  â”œâ”€â”€ Z-score normalization (Zero-mean, unit-variance)
  â””â”€â”€ Class imbalance handling (SMOTE k-NN neighborhood interpolation)
      â”‚
      â–¼
[1D-CNN Training (MATLAB)]
  â”œâ”€â”€ 15-layer hybrid architecture
  â”œâ”€â”€ Binary classification (Apnea vs Normal respiration)
  â”œâ”€â”€ 65,185 trainable parameters
  â””â”€â”€ Accuracy: 99.62% (with SMOTE)
      â”‚
      â–¼
[Weight Extraction & Quantization]
  â””â”€â”€ Fixed-point quantization (16-bit signed: Q3.13 format)
      â”‚
      â–¼
[Verilog Hardware Accelerator (Vivado Simulation)]
  â”œâ”€â”€ Feed-forward fully connected network (30-30-10-10 neurons)
  â”œâ”€â”€ Fully simulated in Xilinx Vivado (no physical hardware required)
  â”œâ”€â”€ AXI-Lite register interface for weight configuration & control
  â””â”€â”€ Quantized model accuracy: 89.00% (Simulation subset: 86.67% - 90.00%)
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
| **Quantized Model Accuracy (Full)** | â€” | **89.00%** |
| **Simulation Accuracy (30-sample subset)** | â€” | **86.67% - 90.00%** |

*[1] Theoretical minimum is 80 DSPs (1 per neuron). Vivado infers 2 DSPs per neuron due to port signedness and register packing constraints.*
*[2] Sigmoid ROMs are synthesized as Distributed ROM using LUTs. If mapped to BRAM, utilization is 25 BRAMs.*

---

## Complete Step-by-Step Execution Guide

Follow these steps to run the dataset preprocessing, train the model, extract weights, and execute the RTL behavioral simulation to obtain the **86.67% - 90.00%** simulation accuracy (representing the 89.00% quantized network accuracy).

### 1. Automated Pipeline Execution (Windows, Linux & macOS)

The cross-platform launcher scripts automatically detect installed software (MATLAB vs GNU Octave for Phase 1, and Vivado vs Icarus Verilog / Yosys for Phase 2). If no simulation or preprocessing environment is installed, pre-quantized parameter files in `hardware/mif/` are automatically utilized.

*   **Linux / macOS / WSL / Git Bash:**
    ```bash
    chmod +x run_all.sh
    ./run_all.sh
    ```
*   **Windows PowerShell:**
    ```powershell
    powershell -ExecutionPolicy Bypass -File .\run_all.ps1
    ```
*   **Windows Command Prompt (CMD):**
    ```cmd
    run_all.bat
    ```

---

### 2. Manual Execution Guide

#### Phase 1: Set Up Repository & Dataset

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/AishikTokdar/NeuroSomno-HDL.git
    cd NeuroSomno-HDL
    ```
2.  **Prepare Dataset**:
    *   **Option A (UCDDB Database):** Download `.edf` records from the [PhysioNet UCDDB Database](https://physionet.org/content/ucddb/1.0.0/) and place inside `dataset/`.
    *   **Option B (Synthetic Generation):** If no `.edf` files are present, the preprocessing pipeline automatically generates structured synthetic signals for full verification without downloading external data.

---

#### Phase 2: Signal Preprocessing & Quantization

##### Option A: MATLAB R2023b (Primary Default)
Open MATLAB, navigate to `matlab_preprocessing/`, and run:
```matlab
run('preprocess_eeg.m');
run('segment_eeg.m');
run('handle_imbalance.m');
run('train_1dcnn.m');
run('extract_weights.m');
```

##### Option B: GNU Octave (Open-Source Free Alternative)
Install GNU Octave via package manager (`sudo apt install octave` or `brew install octave` or `choco install octave`) and run:
```bash
octave --no-gui --eval "run('matlab_preprocessing/preprocess_eeg.m'); run('matlab_preprocessing/segment_eeg.m'); run('matlab_preprocessing/handle_imbalance.m'); run('matlab_preprocessing/train_1dcnn.m'); run('matlab_preprocessing/extract_weights.m');"
```

---

##### Option C: Python 3.x / PyTorch (100% Free & Open-Source)
Install lightweight requirements and execute the standalone preprocessing script:
```bash
pip install -r python_pipeline/requirements.txt
python python_pipeline/preprocess_eeg.py
python python_pipeline/train_model.py
python python_pipeline/export_weights.py
```
*(Automatically extracts or synthesizes EEG epochs and partitions into train/val/test splits)*

---

#### Phase 3: Hardware RTL Simulation & Synthesis

> [!NOTE]
> **Out-of-the-Box Hardware Simulation**:
> All 164 pre-extracted memory initialization files (`.mif`), activation lookup tables (`sig_rom.mem`), and test vectors (`test_data.txt`, `test_labels.txt`) are already included in `hardware/mif/`. You can skip Phase 2 and proceed directly to Phase 3 to simulate the hardware accelerator out-of-the-box.

##### Option A: Xilinx Vivado (Primary Default)

*   **GUI Mode:**
    1. Open Vivado and create project `NeuroSomno_HDL` in the root folder.
    2. Add `hardware/rtl/*.v` as **Design Sources**, `hardware/tb/*.v` as **Simulation Sources**, and `hardware/constraints/zedboard.xdc` as **Constraints**.
    3. In **Simulation Settings**, set **Simulation Run Directory** to `hardware/mif/`.
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
Regardless of whether you run Vivado or Icarus Verilog, the console will print predictions against actual sample labels:
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

## Visualizing Waveforms in Vivado

For visual waveform setup in Vivado GUI, see the signal trace guide in [Hardware RTL & Simulation Reference](hardware/README.md#visualizing-waveforms).

---

## License

This project is licensed under the MIT License â€” see the [LICENSE](LICENSE) file for details.