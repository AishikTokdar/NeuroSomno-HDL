"""Run the full existing Python pipeline in isolation, without changing fixtures.

Run from the repository root: python -u tests/audit_training.py
Training seeds NumPy/PyTorch; this checks the complete pipeline in isolation.
Synthetic data and patient-disjoint overlapping windows are smoke-test inputs,
not evidence of performance on unseen patients.
"""
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python_pipeline"))


def main():
    import torch
    from train_model import train_and_evaluate
    from export_weights import export_model_weights, export_test_vectors
    from bit_true_emulator import run_testbench_verification
    torch.set_num_threads(2)
    previous = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="neurosomno-training-") as tmp:
        try:
            os.chdir(tmp)
            print(f"ISOLATED_TRAINING {tmp}", flush=True)
            train_and_evaluate()
            export_model_weights()
            export_test_vectors()
            run_testbench_verification()
        finally:
            os.chdir(previous)


if __name__ == "__main__":
    main()
