# Python Biosignal & Machine Learning Pipeline

This directory provides an end-to-end Python alternative to the MATLAB pipeline for preprocessing raw EEG signals, training deep learning classifiers, exporting Q3.13 fixed-point parameters, and validating RTL behavior using a bit-true emulator.

---

## Pipeline Overview

```
Raw EDF / Synthetic Signals
          │
          ▼
   [preprocess_eeg.py] ──> 50 Hz Notch, 0.5-45 Hz Bandpass, 11s Windowing
          │
          ▼
    [train_model.py]   ──> SMOTE Balancing, Hybrid 1D-CNN, Quantized FCN
          │
          ▼
   [export_weights.py] ──> Q3.13 Conversion, MIF files, sig_rom.mem, test vectors
          │
          ▼
 [bit_true_emulator.py]──> Parity check against Verilog RTL simulation
```

---

## Script Specifications

| Script | Inputs | Outputs | Description |
| :--- | :--- | :--- | :--- |
| **[`preprocess_eeg.py`](preprocess_eeg.py)** | Raw `.edf` in [`../dataset/`](../dataset/README.md) or synthetic generator | Preprocessed `.npy` feature windows and label arrays | Applies 50 Hz IIR notch filter, 4th-order Butterworth bandpass (0.5–45 Hz), and 11-second sliding window segmentation (1408 samples/channel, 2816 concatenated). |
| **[`train_model.py`](train_model.py)** | Preprocessed feature partitions | `hybrid_1dcnn.pt` and `fcn_quantized.pt` PyTorch checkpoints | Trains 15-layer Hybrid 1D-CNN on full 2816-sample signals and 784-input FCN (30-30-10-10) with SMOTE minority-class oversampling. |
| **[`export_weights.py`](export_weights.py)** | Trained PyTorch model checkpoints | `.mif` files, `sig_rom.mem`, `test_data.txt`, `test_labels.txt` | Quantizes floating-point weights and biases to 16-bit signed Q3.13 fixed-point format and writes to [`../hardware/mif/`](../hardware/mif/README.md). |
| **[`verify_quantization.py`](verify_quantization.py)** | Exported `.mif` files in `../hardware/mif/` | Console precision verification report | Verifies numerical bounds, detects saturation clipping, and validates Q3.13 quantization error margin ($< 2^{-13}$). |
| **[`bit_true_emulator.py`](bit_true_emulator.py)** | Exported `.mif` files and test vectors | Classification predictions and accuracy score | Python cycle- and bit-accurate emulator modeling [`../hardware/rtl/zynet_top.v`](../hardware/rtl/zynet_top.v) with exact integer MAC logic. |

---

## Quickstart Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Complete Pipeline
```bash
python preprocess_eeg.py
python train_model.py
python export_weights.py
python verify_quantization.py
python bit_true_emulator.py
```

All generated memory initialization files and test vectors are saved directly to [`../hardware/mif/`](../hardware/mif/README.md) for direct RTL simulation with Vivado or Icarus Verilog.
