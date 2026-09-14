"""
NeuroSomno-HDL: Standalone Python EEG Biosignal Preprocessing Pipeline
Processes raw EDF or synthetic EEG signals with 50 Hz IIR notch filter,
0.5-45 Hz 4th-order Butterworth bandpass filter, and 11-second sliding window segmentation.
"""

import os
import glob
import numpy as np
from scipy import signal

FS = 128
WINDOW_SEC = 11
STRIDE_SEC = 1
WINDOW_SAMPLES = WINDOW_SEC * FS  # 1408 samples per channel -> 2816 concatenated
STRIDE_SAMPLES = STRIDE_SEC * FS  # 128 samples

def design_notch_filter(fs=FS, f0=50.0, Q=35.0):
    """Design a 2nd-order IIR Notch filter at powerline frequency (50 Hz)."""
    b, a = signal.iirnotch(w0=f0, Q=Q, fs=fs)
    return b, a

def design_bandpass_filter(fs=FS, low=0.5, high=45.0, order=4):
    """Design a 4th-order Butterworth bandpass filter (0.5 to 45 Hz)."""
    nyq = 0.5 * fs
    b, a = signal.butter(order, [low / nyq, high / nyq], btype='bandpass')
    return b, a

def apply_filters(data, fs=FS):
    """Apply zero-phase Notch and Bandpass filtering."""
    b_notch, a_notch = design_notch_filter(fs)
    b_bp, a_bp = design_bandpass_filter(fs)
    notch_filtered = signal.filtfilt(b_notch, a_notch, data)
    bandpass_filtered = signal.filtfilt(b_bp, a_bp, notch_filtered)
    return bandpass_filtered

def normalize_zscore(window):
    """Zero-mean and unit-variance normalization."""
    std = np.std(window)
    if std == 0:
        return window - np.mean(window)
    return (window - np.mean(window)) / std

def generate_synthetic_patient(patient_id=1, duration_sec=600, fs=FS):
    """Generate structured synthetic EEG matching UCDDB characteristics for testing."""
    np.random.seed(42 + patient_id)
    t = np.arange(0, duration_sec, 1.0 / fs)
    # Baseline normal rhythm: 10 Hz alpha wave + 2 Hz delta wave + noise
    c3 = np.sin(2 * np.pi * 10 * t) + 0.5 * np.sin(2 * np.pi * 2 * t) + 0.1 * np.random.randn(len(t))
    c4 = np.sin(2 * np.pi * 10 * t + np.pi / 4) + 0.5 * np.sin(2 * np.pi * 2 * t) + 0.1 * np.random.randn(len(t))
    
    labels = np.zeros(duration_sec, dtype=np.int32)
    # Inject apnea events: 30-second windows with reduced amplitude every 120 seconds
    for idx in range(60, duration_sec - 30, 120):
        c3[idx * fs : (idx + 30) * fs] = 0.1 * np.random.randn(30 * fs)
        c4[idx * fs : (idx + 30) * fs] = 0.1 * np.random.randn(30 * fs)
        labels[idx : idx + 30] = 1
        
    return c3, c4, labels

def segment_signals(c3_filt, c4_filt, labels, fs=FS):
    """Segment continuous signals into 11-second overlapping windows (2816 samples)."""
    n_samples = len(c3_filt)
    num_windows = (n_samples - WINDOW_SAMPLES) // STRIDE_SAMPLES + 1
    
    segments = []
    window_labels = []
    
    for i in range(num_windows):
        start = i * STRIDE_SAMPLES
        end = start + WINDOW_SAMPLES
        
        c3_win = normalize_zscore(c3_filt[start:end])
        c4_win = normalize_zscore(c4_filt[start:end])
        seg = np.concatenate([c3_win, c4_win])  # 1408 + 1408 = 2816 features
        
        label_idx = min(int(start / fs) + 2, len(labels) - 1)
        lbl = int(labels[label_idx])
        
        segments.append(seg)
        window_labels.append(lbl)
        
    return np.array(segments, dtype=np.float32), np.array(window_labels, dtype=np.int64)

def run_preprocessing_pipeline(dataset_dir="dataset", output_file="dataset/eeg_data_split.npz"):
    """Main execution function loading EDF files or generating synthetic verification data."""
    os.makedirs(dataset_dir, exist_ok=True)
    edf_files = glob.glob(os.path.join(dataset_dir, "*.edf"))
    
    all_X, all_Y = [], []
    
    if len(edf_files) == 0:
        print("[INFO] No external .edf files found in dataset/. Generating 3 synthetic patient records...")
        for pid in range(1, 4):
            c3_raw, c4_raw, labels = generate_synthetic_patient(patient_id=pid)
            c3_filt = apply_filters(c3_raw)
            c4_filt = apply_filters(c4_raw)
            x_seg, y_seg = segment_signals(c3_filt, c4_filt, labels)
            all_X.append(x_seg)
            all_Y.append(y_seg)
    else:
        print(f"[INFO] Found {len(edf_files)} EDF recordings. Loading with MNE...")
        try:
            import mne
            for edf_path in edf_files:
                raw = mne.io.read_raw_edf(edf_path, preload=True, verbose=False)
                ch_names = [ch.upper() for ch in raw.ch_names]
                c3_idx = next((i for i, name in enumerate(ch_names) if 'C3' in name), 0)
                c4_idx = next((i for i, name in enumerate(ch_names) if 'C4' in name), 1)
                
                raw.resample(FS)
                data = raw.get_data()
                c3_raw = data[c3_idx]
                c4_raw = data[c4_idx]
                c3_filt = apply_filters(c3_raw)
                c4_filt = apply_filters(c4_raw)
                
                labels = np.zeros(len(c3_raw) // FS, dtype=np.int32)
                x_seg, y_seg = segment_signals(c3_filt, c4_filt, labels)
                all_X.append(x_seg)
                all_Y.append(y_seg)
        except ImportError:
            print("[WARNING] MNE library not installed. Falling back to synthetic generator...")
            for pid in range(1, 4):
                c3_raw, c4_raw, labels = generate_synthetic_patient(patient_id=pid)
                c3_filt = apply_filters(c3_raw)
                c4_filt = apply_filters(c4_raw)
                x_seg, y_seg = segment_signals(c3_filt, c4_filt, labels)
                all_X.append(x_seg)
                all_Y.append(y_seg)

    X = np.vstack(all_X)
    Y = np.concatenate(all_Y)
    
    # 80/10/10 Train/Val/Test Split
    n_samples = len(X)
    indices = np.random.permutation(n_samples)
    train_cut = int(0.80 * n_samples)
    val_cut = train_cut + int(0.10 * n_samples)
    
    train_idx = indices[:train_cut]
    val_idx = indices[train_cut:val_cut]
    test_idx = indices[val_cut:]
    
    np.savez_compressed(
        output_file,
        X_train=X[train_idx], Y_train=Y[train_idx],
        X_val=X[val_idx], Y_val=Y[val_idx],
        X_test=X[test_idx], Y_test=Y[test_idx]
    )
    
    print(f"[SUCCESS] Dataset partitioned: Train={len(train_idx)}, Val={len(val_idx)}, Test={len(test_idx)}")
    print(f"[SUCCESS] Saved preprocessed biosignals to {output_file}")

if __name__ == "__main__":
    run_preprocessing_pipeline()
