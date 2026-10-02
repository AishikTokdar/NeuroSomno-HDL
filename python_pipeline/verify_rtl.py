"""Compile real RTL and compare every neuron output against the integer reference."""
import argparse
import json
import gzip
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from bit_true_emulator import BitTrueNetwork, load_mif_array

ROOT = Path(__file__).resolve().parents[1]


def verify(iverilog, vvp, mif_dir=None):
    if not iverilog or not vvp:
        raise RuntimeError("Icarus Verilog and vvp are required; add them to PATH or supply their paths")
    mif = Path(mif_dir or ROOT / "hardware/mif").resolve()
    net = BitTrueNetwork(str(mif))
    samples = load_mif_array(mif / "test_data.txt").reshape(-1, 784)
    if len(samples) != 30:
        raise ValueError("The current top-level regression bench requires 30 frames")
    expected = {}
    for i, sample in enumerate(samples):
        values = sample
        for layer, neurons in enumerate([net.l1, net.l2, net.l3, net.l4], 1):
            values = [n.compute(values) for n in neurons]
            expected.update({(i, layer, n): int(value) for n, value in enumerate(values)})
    with tempfile.TemporaryDirectory(prefix="neurosomno-parity-") as tmp:
        executable = str(Path(tmp) / "top.vvp")
        subprocess.run([iverilog, "-g2012", "-s", "tb_top_sim", "-o", executable,
                        *map(str, sorted((ROOT / "hardware/rtl").glob("*.v"))),
                        str(ROOT / "hardware/tb/tb_top_sim.v")], check=True, timeout=60)
        run = subprocess.run([vvp, executable, "+TRACE"], cwd=mif,
                             text=True, capture_output=True, check=True, timeout=60)
    observed = {}
    for sample, layer, neuron, value in re.findall(r"^TRACE (\d+) (\d+) (\d+) (\S+)$", run.stdout, re.M):
        key = (int(sample), int(layer), int(neuron))
        if key in observed:
            raise AssertionError(f"Duplicate RTL output {key}")
        observed[key] = int(value)  # Unknown X/Z data must fail, never map to zero.
    if observed != expected:
        mismatches = [(k, v, observed.get(k)) for k, v in expected.items() if observed.get(k) != v]
        raise AssertionError(f"RTL parity failed: {len(mismatches)} mismatches; first: {mismatches[:5]}")
    predictions = re.findall(r"^Sample (\d+): Pred = (\d+), Act = (\d+)$", run.stdout, re.M)
    if len(predictions) != len(samples):
        raise AssertionError("Incomplete classification trace")
    for sample, prediction, _ in predictions:
        if int(prediction) != net.infer_sample(samples[int(sample)])[0]:
            raise AssertionError(f"Classification differs for sample {sample}")
    report = {"frames": len(samples), "neuron_outputs_compared": len(expected),
              "mismatches": 0, "correct_labels": sum(p == y for _, p, y in predictions),
              "input_gaps": True, "data": "synthetic regression fixtures"}
    output = ROOT / "results/verification"
    output.mkdir(parents=True, exist_ok=True)
    (output / "rtl_trace.txt").write_text(run.stdout, encoding="utf-8")
    (output / "rtl_parity.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--iverilog", default=shutil.which("iverilog"))
    parser.add_argument("--vvp", default=shutil.which("vvp"))
    args = parser.parse_args()
    verify(args.iverilog, args.vvp)
