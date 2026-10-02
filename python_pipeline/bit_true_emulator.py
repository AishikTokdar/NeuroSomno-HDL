"""
NeuroSomno-HDL: Bit-True Hardware RTL Golden Emulator in Python
Integer arithmetic reference for the Verilog accelerator (zynet_top.v).
RTL parity must be measured separately with verify_rtl.py.
"""

import os
import numpy as np

def load_mif_array(filepath):
    """Loads a .mif file as an array of 16-bit signed integers."""
    vals = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                if len(line) != 16 or set(line) - {'0', '1'}:
                    raise ValueError(f'Invalid 16-bit binary word in {filepath}')
                raw = int(line, 2)
                if raw & 0x8000:
                    raw -= 0x10000
                vals.append(raw)
    return np.array(vals, dtype=np.int32)

class BitTrueNeuron:
    """Integer arithmetic reference for hardware/rtl/neuron.v."""
    def __init__(self, weights, bias, act_type="relu", sig_lut=None):
        self.weights = weights  # shape (num_weights,), int32
        self.bias = bias        # int32
        self.act_type = act_type
        self.sig_lut = sig_lut

    def compute(self, x_stream):
        """Computes MAC over stream of 16-bit signed inputs."""
        if len(x_stream) != len(self.weights):
            raise ValueError('Input length does not match neuron weights')
        if any(int(x) != x or not -32768 <= int(x) <= 32767 for x in x_stream):
            raise ValueError('Expected signed 16-bit Q3.13 integers')
        acc = 0
        for x, w in zip(x_stream, self.weights):
            prod = (int(x) * int(w)) >> 13
            acc += prod
        acc += self.bias
        
        if acc > 32767:
            acc_sat = 32767
        elif acc < -32768:
            acc_sat = -32768
        else:
            acc_sat = acc

        if self.act_type == "relu":
            return max(0, acc_sat)
        elif self.act_type == "sigmoid":
            # Mirror hardware sig_rom.v indexing: wire [9:0] index = i_data[15:6] + 10'd512;
            raw_16 = acc_sat & 0xFFFF
            bits_15_6 = (raw_16 >> 6) & 0x3FF
            idx = (bits_15_6 + 512) & 0x3FF
            return self.sig_lut[idx] if self.sig_lut is not None else acc_sat
        return acc_sat

class BitTrueNetwork:
    """Full 4-layer accelerator model matching zynet_top.v."""
    def __init__(self, mif_dir="hardware/mif"):
        self.mif_dir = mif_dir
        self.sig_lut = self._load_sigmoid_rom()
        self.l1 = self._build_layer(1, 30, 784, "relu")
        self.l2 = self._build_layer(2, 30, 30, "relu")
        self.l3 = self._build_layer(3, 10, 30, "sigmoid")
        self.l4 = self._build_layer(4, 2, 10, "linear")

    def _load_sigmoid_rom(self):
        sig_path = os.path.join(self.mif_dir, "sig_rom.mem")
        return load_mif_array(sig_path)

    def _build_layer(self, layer_idx, num_neurons, num_inputs, act_type):
        neurons = []
        for n in range(num_neurons):
            w_file = os.path.join(self.mif_dir, f"w_{layer_idx}_{n}.mif")
            b_file = os.path.join(self.mif_dir, f"b_{layer_idx}_{n}.mif")
            w = load_mif_array(w_file)
            bias_words = load_mif_array(b_file)
            if len(w) != num_inputs or len(bias_words) != 1:
                raise ValueError(f'Invalid parameter dimensions for layer {layer_idx}, neuron {n}')
            b = bias_words[0]
            neurons.append(BitTrueNeuron(w, b, act_type, self.sig_lut))
        return neurons

    def infer_sample(self, x_input):
        """Streams a single 784-element sample through the network."""
        l1_out = [n.compute(x_input) for n in self.l1]
        l2_out = [n.compute(l1_out) for n in self.l2]
        l3_out = [n.compute(l2_out) for n in self.l3]
        l4_out = [n.compute(l3_out) for n in self.l4]
        
        predicted_class = int(np.argmax(l4_out))
        return predicted_class, l4_out

def run_testbench_verification(mif_dir="hardware/mif"):
    """Loads test_data.txt and test_labels.txt and compares predictions."""
    data_file = os.path.join(mif_dir, "test_data.txt")
    labels_file = os.path.join(mif_dir, "test_labels.txt")
    
    if not os.path.exists(data_file) or not os.path.exists(labels_file):
        raise FileNotFoundError(f"Test vector files not found in {mif_dir}")
        
    print(f"[INFO] Initializing Bit-True RTL Emulator from {mif_dir}...")
    net = BitTrueNetwork(mif_dir)
    
    raw_data = load_mif_array(data_file)
    if len(raw_data) == 0 or len(raw_data) % 784:
        raise ValueError('Test vectors must contain complete 784-word frames')
    num_samples = len(raw_data) // 784
    
    labels = []
    with open(labels_file, "r") as fl:
        for line in fl:
            if line.strip():
                labels.append(int(line.strip(), 2))
                
    if len(labels) != num_samples or any(y not in (0, 1) for y in labels):
        raise ValueError('One binary label required for each test frame')
    correct = 0
    print(f"\n--- Running Bit-True Parity Simulation ({num_samples} Samples) ---")
    for i in range(num_samples):
        sample = raw_data[i * 784 : (i + 1) * 784]
        pred, logits = net.infer_sample(sample)
        act = labels[i]
        is_correct = (pred == act)
        if is_correct:
            correct += 1
        print(f"Sample {i:2d}: Pred = {pred}, Act = {act} {'[OK]' if is_correct else '[MISMATCH]'}")
        
    acc = (correct * 100.0) / num_samples
    print(f"\n[EMULATOR ACCURACY] {acc:.2f}% ({correct}/{num_samples} correct)")
    print("[INFO] Arithmetic reference only; use verify_rtl.py for measured RTL parity.")
    return correct, num_samples

if __name__ == "__main__":
    run_testbench_verification()
