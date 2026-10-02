"""
NeuroSomno-HDL: Standalone Python EEG Biosignal Preprocessing Pipeline
Processes raw EDF or synthetic EEG signals with 50 Hz IIR notch filter,
0.5-45 Hz 4th-order Butterworth bandpass filter, and 11-second sliding window segmentation.
"""

import os
from pathlib import Path
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
    rng = np.random.default_rng(42 + patient_id)
    t = np.arange(0, duration_sec, 1.0 / fs)
    # Baseline normal rhythm: 10 Hz alpha wave + 2 Hz delta wave + noise
    c3 = np.sin(2 * np.pi * 10 * t) + 0.5 * np.sin(2 * np.pi * 2 * t) + 0.1 * rng.standard_normal(len(t))
    c4 = np.sin(2 * np.pi * 10 * t + np.pi / 4) + 0.5 * np.sin(2 * np.pi * 2 * t) + 0.1 * rng.standard_normal(len(t))
    
    labels = np.zeros(duration_sec, dtype=np.int32)
    # Inject apnea events: 30-second windows with reduced amplitude every 120 seconds
    for idx in range(60, duration_sec - 30, 120):
        c3[idx * fs : (idx + 30) * fs] = 0.1 * rng.standard_normal(30 * fs)
        c4[idx * fs : (idx + 30) * fs] = 0.1 * rng.standard_normal(30 * fs)
        labels[idx : idx + 30] = 1
        
    return c3, c4, labels

def segment_signals(c3_filt, c4_filt, labels, fs=FS):
    """Segment continuous signals into 11-second overlapping windows (2816 samples)."""
    c3_filt, c4_filt, labels = map(np.asarray, (c3_filt, c4_filt, labels))
    n_samples = len(c3_filt)
    window_samples, stride_samples = int(WINDOW_SEC * fs), int(STRIDE_SEC * fs)
    if fs <= 100 or n_samples != len(c4_filt) or n_samples < window_samples:
        raise ValueError('Aligned channels of at least 11 seconds at fs > 100 Hz required')
    if labels.ndim != 1 or len(labels) < n_samples // fs or not np.isin(labels, [0, 1]).all():
        raise ValueError('Annotations must supply one binary label per second')
    if not np.isfinite(c3_filt).all() or not np.isfinite(c4_filt).all():
        raise ValueError('Channels must be finite')
    num_windows = (n_samples - window_samples) // stride_samples + 1
    
    segments = []
    window_labels = []
    
    for i in range(num_windows):
        start = i * stride_samples
        end = start + window_samples
        
        c3_win = normalize_zscore(c3_filt[start:end])
        c4_win = normalize_zscore(c4_filt[start:end])
        seg = np.concatenate([c3_win, c4_win])  # 1408 + 1408 = 2816 features
        
        label_idx = int((end - 1) / fs)
        lbl = int(labels[label_idx])
        
        segments.append(seg)
        window_labels.append(lbl)
        
    return np.array(segments, dtype=np.float32), np.array(window_labels, dtype=np.int64)

def run_preprocessing_pipeline(dataset_dir="dataset", output_file="dataset/eeg_data_split.npz"):
    """Split patients before windowing; EDFs require explicit *_labels.npy annotations.

    Recording names sharing the prefix before '_' belong to the same patient.
    Annotation arrays contain exactly one 0/1 label per whole second at 128 Hz.
    No EDF files means an explicitly reported three-patient synthetic smoke set.
    """
    os.makedirs(dataset_dir, exist_ok=True)
    edf_files = sorted(str(p) for p in Path(dataset_dir).iterdir() if p.suffix.lower() == '.edf')
    patients = {}
    if not edf_files:
        print('[INFO] SYNTHETIC smoke data: three patients; not clinical validation.')
        for pid in range(1, 4):
            patients[str(pid)] = [generate_synthetic_patient(patient_id=pid)]
    else:
        import mne
        for edf_path in edf_files:
            annotation = Path(edf_path).with_name(Path(edf_path).stem + '_labels.npy')
            if not annotation.is_file():
                raise FileNotFoundError(f'Required apnea annotations missing: {annotation}')
            raw = mne.io.read_raw_edf(edf_path, preload=True, verbose=False)
            names = [ch.upper() for ch in raw.ch_names]
            indices = []
            for channel in ('C3', 'C4'):
                matches = [i for i, name in enumerate(names) if channel in name]
                if len(matches) != 1:
                    raise ValueError(f'{edf_path}: expected exactly one {channel} channel')
                indices.append(matches[0])
            raw.resample(FS)
            channels = raw.get_data(picks=indices)
            labels = np.load(annotation, allow_pickle=False)
            if labels.shape != (channels.shape[1] // FS,) or not np.isin(labels, [0, 1]).all():
                raise ValueError(f'{annotation}: one binary label per second required')
            patient = Path(edf_path).stem.split('_')[0]
            patients.setdefault(patient, []).append((channels[0], channels[1], labels))
    identifiers = sorted(patients)
    if len(identifiers) < 3:
        raise ValueError('At least three independent patients required for train/validation/test splits')
    identifiers = np.random.default_rng(42).permutation(identifiers)
    n = len(identifiers)
    n_test = max(1, round(n * 0.1))
    n_val = max(1, round(n * 0.1))
    groups = {'train': identifiers[:n-n_val-n_test],
              'val': identifiers[n-n_val-n_test:n-n_test], 'test': identifiers[n-n_test:]}
    output = {'synthetic': np.array(not bool(edf_files)), 'sample_rate': np.array(FS)}
    for split, ids in groups.items():
        windows, targets, subjects = [], [], []
        for pid in ids:
            for c3, c4, labels in patients[pid]:
                x, y = segment_signals(apply_filters(c3), apply_filters(c4), labels)
                windows.append(x); targets.append(y); subjects.extend([pid] * len(y))
        output['X_' + split] = np.vstack(windows)
        output['Y_' + split] = np.concatenate(targets)
        output['subjects_' + split] = np.array(subjects)
        print(f'[INFO] {split}: {len(subjects)} windows from patients {list(ids)}')
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_file, **output)
    print(f'[SUCCESS] Saved patient-separated biosignals to {output_file}')

if __name__ == '__main__':
    run_preprocessing_pipeline()
