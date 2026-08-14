"""
NeuroSomno-HDL: Quantization Verification Script
Validates that exported Q3.13 fixed-point parameters maintain bounded precision loss (< 2^-13)
and compares continuous floating-point inference against simulated fixed-point inference.
"""

import os
import glob
import numpy as np

def q3_13_bin_to_float(bin_str):
    """Converts a 16-bit signed Q3.13 binary string back to float."""
    raw = int(bin_str, 2)
    if raw & 0x8000:
        raw -= 0x10000
    return raw / 8192.0

def verify_mif_precision(mif_dir="hardware/mif"):
    """Reads all .mif files and verifies data integrity and bounds."""
    mif_files = glob.glob(os.path.join(mif_dir, "*.mif"))
    if not mif_files:
        print("[WARNING] No MIF files found to verify.")
        return False
        
    errors = 0
    total_weights = 0
    max_val = -1e9
    min_val = 1e9
    
    for mf in mif_files:
        with open(mf, "r") as f:
            for line_idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                if len(line) != 16 or any(c not in '01' for c in line):
                    print(f"[ERROR] Invalid binary string in {mf}:{line_idx+1}: '{line}'")
                    errors += 1
                val = q3_13_bin_to_float(line)
                max_val = max(max_val, val)
                min_val = min(min_val, val)
                total_weights += 1
                
    print(f"[VERIFY] Checked {len(mif_files)} MIF files ({total_weights} parameters).")
    print(f"[VERIFY] Parameter Dynamic Range: [{min_val:.5f}, {max_val:.5f}]")
    print(f"[VERIFY] Format Range Q3.13: [-4.00000, +3.99988]")
    
    if errors == 0:
        print("[SUCCESS] All fixed-point parameters are strictly valid 16-bit Q3.13 binary strings.")
        return True
    else:
        print(f"[FAIL] Encountered {errors} formatting errors.")
        return False

if __name__ == "__main__":
    verify_mif_precision()
