# NeuroSomno-HDL: Sleep Apnea Detection on FPGA using Hybrid CNN

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="License: MIT">
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
*   [System Architecture Overview](docs/architecture_overview.md) — Register maps, latency calculations, and layer dataflow logic.
*   [EEG Dataset Configuration](dataset/README.md) — Channel configurations and manual download instructions.
*   [MATLAB Preprocessing Pipeline Guide](matlab_preprocessing/README.md) — In-depth details on filtering, segmentation, and model training.
*   [Hardware RTL & Simulation Reference](hardware/README.md) — Verilog module breakdowns and state machine definitions.
*   [Memory Initialization Guide](hardware/mif/README.md) — Specifications for `.mif`, `.mem`, and `.txt` simulator files.
*   [Validation Results & Synthesis Reports](results/README.md) — Detailed accuracy metrics, power budgets, and FPGA resource footprints.
*   [Vivado Synthesis & Accuracy Validation Report](docs/synthesis_and_accuracy_validation.md) — Detailed resource analysis, LUT/DSP definitions, and simulation accuracy verification.

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

Before starting, ensure that your system meets the following specifications:
*   **Operating System:** Windows 10/11 or Ubuntu 20.04/22.04 LTS.
*   **MATLAB Version:** R2023b or newer.
    *   *Verification:* Type `ver` in the MATLAB Command Window and verify that **Deep Learning Toolbox**, **Fixed-Point Designer**, and **Signal Processing Toolbox** are listed.
*   **Vivado Version:** Xilinx Vivado 2023.1 or newer.
    *   *Verification:* Ensure `vivado` is added to your system PATH or launch via the desktop icon.

---

## Key Results

### Software Model Performance (MATLAB)

| Metric | Random Oversampling | SMOTE |
| :--- | :---: | :---: |
| **Accuracy** | 99.53% | **99.62%** |
| **Balanced Accuracy** | 91.23% | **91.58%** |
| **Sensitivity (Recall)** | 82.61% | **83.33%** |
| **Specificity** | **99.85%** | 99.84% |
| **Precision** | **91.57%** | 86.96% |
| **F1 Score** | **0.8686** | 0.8511 |

### Hardware Accelerator Performance (Vivado Simulation)

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

### Automated Execution (Windows & Linux)

You can execute the entire pipeline (MATLAB preprocessing + weight quantization + Vivado/Icarus simulation) automatically using the cross-platform launcher scripts:

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

> [!NOTE]
> The automated scripts detect whether `matlab` and `vivado` (or `iverilog`) are installed in your PATH. If MATLAB is not installed, the script automatically utilizes the pre-quantized parameter files in `hardware/mif/` to execute the hardware RTL simulation.

---

### Manual Execution Guide

### Phase 1: Set Up the Dataset & Environment

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/AishikTokdar/NeuroSomno-HDL.git
    cd NeuroSomno-HDL
    ```
2.  **Ensure Prerequisites are Installed**:
    *   MATLAB R2023b or later (with *Signal Processing*, *Deep Learning*, and *Fixed-Point Designer* toolboxes).
    *   Xilinx Vivado 2023.1 (or later).
3.  **Prepare the Dataset**:
    *   **Option A (UCDDB Database):** Download `.edf` records from the [PhysioNet UCDDB Database](https://physionet.org/content/ucddb/1.0.0/) and place them inside the `dataset/` directory.
    *   **Option B (Synthetic Generation):** If no `.edf` files are found, the preprocessing script will automatically generate synthetic structured EEG-like signals. This allows you to run and verify the entire project without any manual downloads.

### Phase 2: Execute the MATLAB Pipeline

1.  Open MATLAB.
2.  Change your working directory to the cloned repository's `matlab_preprocessing/` folder.
3.  Run the main preprocessing script:
    ```matlab
    run('preprocess_eeg.m')
    ```
    > [!NOTE]
    > This filters the signals and saves them as mat variables (`c3_filt`, `c4_filt`).
4.  Run the segmentation script:
    ```matlab
    run('segment_eeg.m')
    ```
    > [!NOTE]
    > This creates the overlapping 11-second segments (2816 elements) and partitions the dataset.
5.  Balance the training data classes using SMOTE:
    ```matlab
    run('handle_imbalance.m')
    ```
6.  Train the neural network models:
    ```matlab
    run('train_1dcnn.m')
    ```
    > [!NOTE]
    > This trains the 1D-CNN (`global_model.mat`) and the target FCN hardware model (`fcn_model.mat`).
7.  Extract, quantize, and export the network parameters:
    ```matlab
    run('extract_weights.m')
    ```
    > [!IMPORTANT]
    > This generates all `.mif` weight files, `sig_rom.mem`, `test_data.txt`, and `test_labels.txt` inside the `hardware/mif/` folder.

### Phase 3: Run RTL Behavioral Simulation

You can execute the RTL behavioral simulation manually using Xilinx Vivado (GUI or Batch) or Icarus Verilog (CLI):

#### Option A: Xilinx Vivado GUI Mode
1.  Launch Xilinx Vivado.
2.  Create a new RTL Project named `NeuroSomno_HDL` in the root repository directory.
3.  Import the source files:
    *   Add all `.v` files located in `hardware/rtl/` as **Design Sources**.
    *   Add all `.v` files located in `hardware/tb/` as **Simulation Sources**.
    *   Add `hardware/constraints/zedboard.xdc` as a **Constraints** file.
4.  Configure the Simulator Working Directory:
    *   In the Flow Navigator, click **Simulation Settings**.
    *   Under **Simulation**, set the **Simulation Run Directory** to point to the `hardware/mif/` folder containing the weights and test data.
    *   *Alternative:* Copy all `.mif`, `.mem`, and `.txt` files from `hardware/mif/` into the default Vivado simulation output folder: `<project_name>.sim/sim_1/behav/xsim/`.
5.  Launch the simulation:
    *   Click **Run Simulation** -> **Run Behavioral Simulation**.
    *   In the Tcl console, run the command: `run -all`.

#### Option B: Xilinx Vivado Command Line (Batch Mode)
Execute Vivado batch simulation directly from your terminal:
```bash
vivado -mode batch -source -eval "create_project -force NeuroSomno_HDL ./vivado_proj -part xc7z020clg484-1; add_files [glob ./hardware/rtl/*.v]; add_files -fileset sim_1 [glob ./hardware/tb/*.v]; set_property top tb_top_sim [get_filesets sim_1]; launch_simulation; run -all; exit"
```

#### Option C: Icarus Verilog (Open-Source CLI Simulation)
If you do not have Vivado installed, you can use the open-source **Icarus Verilog** toolchain:
1.  Navigate to the MIF directory:
    ```bash
    cd hardware/mif
    ```
2.  Compile the RTL and Testbench:
    ```bash
    iverilog -g2012 -I ../rtl -o sim_top ../rtl/*.v ../tb/tb_top_sim.v
    ```
3.  Run the simulation executable with VVP:
    ```bash
    vvp sim_top
    ```

#### Verification of Simulation Results
Check the terminal / Tcl console output. It will stream the prediction vs actual label comparison for each test sample:
```text
Sample 0: Pred = 0, Act = 0
Sample 1: Pred = 1, Act = 1
...
Sample 29: Pred = 0, Act = 0
Overall Accuracy: 90.000000 (or 86.666667)
```
> [!TIP]
> The simulation prints an overall accuracy of **90.00%** (27/30 correct) or **86.67%** (26/30 correct), which represents the 89.00% full-dataset quantized accuracy evaluated over this 30-sample subset.

---

## Visualizing Waveforms in Vivado

To inspect signals visually in Vivado's Waveform Viewer:
1.  Locate the simulation signal tree inside the **Scope** window.
2.  Navigate to `tb_top_sim` -> `uut` -> `l1` (Layer 1).
3.  Drag the `o_data` and `o_valid` signals into the **Wave** window.
4.  Right-click on `o_data`, select **Radix** -> **Real Settings...** -> Choose **Fixed Point** -> Select **Signed** -> Set **Fraction Length** to **13**.
5.  Select **Waveform Style** -> **Analog** to display the signal values as continuous waveforms.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
