# EEG Dataset Setup Guide

This document describes how to obtain and configure the European Data Format (EDF) signals for training and validating the **NeuroSomno-HDL** model.

---

## Dataset Details
*   **Database:** St. Vincent's University Hospital / UCD Sleep Apnea Database (UCDDB)
*   **Provider:** PhysioNet
*   **Format:** European Data Format (EDF)
*   **EEG Channels:** `C3-A2` (Left central cortex) and `C4-A1` (Right central cortex)
*   **Sampling Rate:** 128 Hz

---

## Step-by-Step Dataset Download Procedure

### 1. Manual Download from PhysioNet
1. Navigate to the official PhysioNet UCDDB page: [https://physionet.org/content/ucddb/1.0.0/](https://physionet.org/content/ucddb/1.0.0/).
2. Scroll down to the **Files** section.
3. Download the individual subject record files (e.g., `ucddb002.edf`, `ucddb003.edf`, etc.) or the complete zip archive.
4. Place all downloaded `.edf` files directly inside this `dataset/` directory.

### 2. Labels Configuration
*   For each subject `.edf` file, there must be a corresponding label file named `<subject>_label.mat` in this directory containing a vector `labels`.
*   `0` = Normal breathing.
*   `1` = Apnea event occurrence.

---

## Fallback: Running with Synthetic Data

> [!TIP]
> If you want to test the complete training, weight extraction, and RTL simulation pipeline immediately without downloading large external databases:
> 1. Keep this `dataset/` directory empty.
> 2. Run `matlab_preprocessing/preprocess_eeg.m`.
> 3. The script will detect the missing files and automatically generate three synthetic subject files (`ucddb001`, `ucddb002`, `ucddb003`) containing simulated EEG signals and label structures.
