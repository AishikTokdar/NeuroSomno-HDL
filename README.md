# 🌙 NeuroSomno-HDL : Sleep Apnea Detection on FPGA using Hybrid CNN

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="License: MIT">
  <img src="https://img.shields.io/badge/Platform-MATLAB%20R2026b-orange.svg?style=for-the-badge" alt="Platform: MATLAB">
  <img src="https://img.shields.io/badge/Simulation-Xilinx%20Vivado%202026.1-blue.svg?style=for-the-badge" alt="Simulation: Vivado">
  <img src="https://img.shields.io/badge/Target-Zynq--7000%20ZedBoard-red.svg?style=for-the-badge" alt="Target: Zynq">
</p>

NeuroSomno-HDL is an edge-intelligent, software-only FPGA simulation framework designed for real-time sleep apnea detection using EEG signals. The system processes raw biosignals, trains a hybrid 1D Convolutional Neural Network (1D-CNN) classifier in MATLAB, and implements a quantized, pipelined feed-forward neural network accelerator in Verilog HDL.

This repository provides a complete, hardware-independent simulation pipeline that can be executed entirely in software using MATLAB and Xilinx Vivado.

---

## 👥 Author & Repository Info

*   **Author:** Aishik Tokdar
*   **Repository URL:** [https://github.com/AishikTokdar/NeuroSomno-HDL](https://github.com/AishikTokdar/NeuroSomno-HDL)

---

## 📂 Document Navigation

For detailed breakdowns of specific project components, refer to the following sub-documents:
*   [📖 System Architecture Overview](docs/architecture_overview.md) — Register maps, latency calculations, and layer dataflow logic.
*   [📊 EEG Dataset Configuration](dataset/README.md) — Channel configurations and manual download instructions.
*   [⚙️ MATLAB Preprocessing Pipeline Guide](matlab_preprocessing/README.md) — In-depth details on filtering, segmentation, and model training.
*   [💾 Hardware RTL & Simulation Reference](hardware/README.md) — Verilog module breakdowns and state machine definitions.
*   [📁 Memory Initialization Guide](hardware/mif/README.md) — Specifications for `.mif`, `.mem`, and `.txt` simulator files.
*   [📈 Validation Results & Synthesis Reports](results/README.md) — Detailed accuracy metrics, power budgets, and FPGA resource footprints.

---

## ⚡ System Overview

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
  └── Overall simulation accuracy: 89.00%
```

---

## 💻 System Requirements & Toolchain Verification

Before starting, ensure that your system meets the following specifications:
*   **Operating System:** Windows 10/11 or Ubuntu 20.04/22.04 LTS.
*   **MATLAB Version:** R2023b or newer.
    *   *Verification:* Type `ver` in the MATLAB Command Window and verify that **Deep Learning Toolbox**, **Fixed-Point Designer**, and **Signal Processing Toolbox** are listed.
*   **Vivado Version:** Xilinx Vivado 2023.1 or newer.
    *   *Verification:* Ensure `vivado` is added to your system PATH or launch via the desktop icon.

---

## 🏆 Key Results

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
| **DSP Utilization** | 2 / 220 (0.91%) | 160 / 220 (72.73%) |
| **BRAM Utilization** | 0.50 / 140 (0.36%) | 15 / 140 (10.71%) |
| **Overall Simulation Accuracy** | — | **89.00%** |

---

## 🛠️ Complete Step-by-Step Execution Guide

Follow these exact steps to run the dataset preprocessing, train the model, extract weights, and execute the RTL behavioral simulation to obtain the **89.00%** classification accuracy.

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

### Phase 3: Run RTL Behavioral Simulation (Xilinx Vivado)

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
6.  Verify the Results:
    *   Check the Tcl Console. It will stream the prediction vs actual label comparison for each test sample:
        ```text
        Sample 0: Pred = 0, Act = 0
        Sample 1: Pred = 1, Act = 1
        ...
        Sample 29: Pred = 0, Act = 0
        Overall Accuracy: 89.000000
        ```
    > [!TIP]
    > The simulation prints an overall accuracy of **89.00%**, matching the synthesized model benchmarks.

---

## 📈 Visualizing Waveforms in Vivado

To inspect signals visually in Vivado's Waveform Viewer:
1.  Locate the simulation signal tree inside the **Scope** window.
2.  Navigate to `tb_top_sim` -> `uut` -> `l1` (Layer 1).
3.  Drag the `o_data` and `o_valid` signals into the **Wave** window.
4.  Right-click on `o_data`, select **Radix** -> **Real Settings...** -> Choose **Fixed Point** -> Select **Signed** -> Set **Fraction Length** to **13**.
5.  Select **Waveform Style** -> **Analog** to display the signal values as continuous waveforms.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
