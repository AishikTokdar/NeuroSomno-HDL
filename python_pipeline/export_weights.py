"""
NeuroSomno-HDL: Python Fixed-Point Q3.13 Weight Extraction & MIF Generator
Converts PyTorch neural network weights to 16-bit signed fixed-point (Q3.13) format
and exports .mif, sig_rom.mem, and simulation test vectors test_data.txt / test_labels.txt.
"""

import os
import numpy as np
import torch

FRAC_BITS = 13
TOTAL_BITS = 16
MAX_INT = (1 << (TOTAL_BITS - 1)) - 1   # +32767
MIN_INT = -(1 << (TOTAL_BITS - 1))      # -32768

def float_to_q3_13_bin(val):
    """Converts a float to 16-bit signed Q3.13 binary string in two's complement."""
    scaled = int(round(float(val) * (1 << FRAC_BITS)))
    clamped = max(MIN_INT, min(MAX_INT, scaled))
    twos_comp = clamped & 0xFFFF
    return format(twos_comp, '016b')

def q3_13_bin_to_float(bin_str):
    """Converts a 16-bit signed Q3.13 binary string back to float."""
    raw = int(bin_str, 2)
    if raw & 0x8000:
        raw -= 0x10000
    return raw / (1 << FRAC_BITS)

def generate_sigmoid_rom(output_path="hardware/mif/sig_rom.mem"):
    """Generates 1024-word precomputed Sigmoid activation table matching hardware LUT."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        for i in range(1024):
            x = (i - 512) / 128.0
            s = 1.0 / (1.0 + np.exp(-x))
            f.write(f"{float_to_q3_13_bin(s)}\n")
    print(f"[SUCCESS] Exported 1024-word Sigmoid ROM to {output_path}")

def export_model_weights(model_path="models/fcn_model.pt", mif_dir="hardware/mif"):
    """Exports layer weights and biases from PyTorch model to .mif files."""
    os.makedirs(mif_dir, exist_ok=True)
    
    if not os.path.exists(model_path):
        print(f"[INFO] Model checkpoint {model_path} not found. Running training first...")
        from train_model import train_and_evaluate
        train_and_evaluate()
        
    from train_model import NeuroSomnoFCN
    model = NeuroSomnoFCN()
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    model.eval()
    
    layers = [
        (1, model.fc1.weight.detach().numpy(), model.fc1.bias.detach().numpy()),
        (2, model.fc2.weight.detach().numpy(), model.fc2.bias.detach().numpy()),
        (3, model.fc3.weight.detach().numpy(), model.fc3.bias.detach().numpy()),
        (4, model.fc4.weight.detach().numpy(), model.fc4.bias.detach().numpy()),
    ]
    
    total_mifs = 0
    for layer_idx, W, B in layers:
        num_neurons = W.shape[0]
        for n in range(num_neurons):
            w_file = os.path.join(mif_dir, f"w_{layer_idx}_{n}.mif")
            with open(w_file, "w") as fw:
                for w_val in W[n]:
                    fw.write(f"{float_to_q3_13_bin(w_val)}\n")
            
            b_file = os.path.join(mif_dir, f"b_{layer_idx}_{n}.mif")
            with open(b_file, "w") as fb:
                fb.write(f"{float_to_q3_13_bin(B[n])}\n")
            
            total_mifs += 2
            
    print(f"[SUCCESS] Exported {total_mifs} parameter MIF files to {mif_dir}/")
    generate_sigmoid_rom(os.path.join(mif_dir, "sig_rom.mem"))

def export_test_vectors(dataset_path="dataset/eeg_data_split.npz", mif_dir="hardware/mif", num_samples=30):
    """Exports behavioral simulation test vectors matching tb_top_sim testbench."""
    os.makedirs(mif_dir, exist_ok=True)
    if not os.path.exists(dataset_path):
        from preprocess_eeg import run_preprocessing_pipeline
        run_preprocessing_pipeline()
        
    data = np.load(dataset_path)
    X_test = data['X_test']
    Y_test = data['Y_test']
    
    from train_model import downsample_signals
    X_fcn = downsample_signals(X_test[:num_samples], 784)
    Y_sub = Y_test[:num_samples]
    
    data_file = os.path.join(mif_dir, "test_data.txt")
    labels_file = os.path.join(mif_dir, "test_labels.txt")
    
    with open(data_file, "w") as fd:
        for i in range(num_samples):
            for j in range(784):
                fd.write(f"{float_to_q3_13_bin(X_fcn[i, j])}\n")
                
    with open(labels_file, "w") as fl:
        for i in range(num_samples):
            lbl_bin = format(int(Y_sub[i]), '04b')
            fl.write(f"{lbl_bin}\n")
            
    print(f"[SUCCESS] Exported {num_samples} simulation test vectors to {data_file} and {labels_file}")

if __name__ == "__main__":
    export_model_weights()
    export_test_vectors()
