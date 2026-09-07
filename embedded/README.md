# Embedded Edge Deployment & Drivers

This directory contains embedded runtime drivers and edge integration scripts for executing the NeuroSomno-HDL accelerator on Xilinx Zynq-7000 SoC platforms (such as the ZedBoard and PYNQ-Z2).

---

## Directory Contents

| Directory / File | Target Platform | Description |
| :--- | :--- | :--- |
| **[`pynq/neurosomno_overlay.py`](pynq/neurosomno_overlay.py)** | PYNQ Python (ARM Linux) | High-level Python driver interfacing with hardware MMIO registers, streaming test samples, and reading apnea telemetry. |
| **[`pynq/demo_inference.ipynb`](pynq/demo_inference.ipynb)** | Jupyter Notebook | Interactive walkthrough demonstrating overlay loading, single-sample inference, batch testing, and live AHI clinical monitoring. |
| **[`c_driver/neurosomno_hw.h`](c_driver/neurosomno_hw.h)** | Bare-metal / FreeRTOS / Linux | C header file declaring hardware base address (`0x43C00000`), register offsets, bitmasks, and clinical severity enums. |
| **[`c_driver/neurosomno_api.c`](c_driver/neurosomno_api.c)** | Standalone ARM Cortex-A9 | Low-level C implementation for accelerator initialization, weight programming, sample inference, and interrupt handling. |

---

## Memory Map & Register Offsets

The accelerator memory-mapped registers match the [System Architecture Overview](../docs/architecture_overview.md#3-register-configuration-map):

*   `0x00`: `REG_CTRL` — Control register (Soft reset: bit 0, Start: bit 1)
*   `0x04`: `REG_LAYER` — Layer target index (1–4)
*   `0x08`: `REG_NEURON` — Neuron target index (0–29)
*   `0x0C`: `REG_WADDR` — Weight address offset
*   `0x10`: `REG_WVAL` — Signed 16-bit Q3.13 weight data
*   `0x14`: `REG_BVAL` — Signed 16-bit Q3.13 bias data
*   `0x18`: `REG_WEN` — Weight write strobe
*   `0x1C`: `REG_BWEN` — Bias write strobe
*   `0x20`: `REG_NNOUT` — Argmax output prediction (0 = Normal, 1 = Apnea)
*   `0x24`: `REG_STATUS` — Status register (Done: bit 0, Intr: bit 1)
*   `0x28`: `REG_AHI_COUNT` — Cumulative clinical apnea episodes
*   `0x2C`: `REG_AHI_SEV` — Clinical severity index (0: Normal, 1: Mild, 2: Moderate, 3: Severe)

---

## Quickstart

### PYNQ-Z2 Python Overlay
```python
from embedded.pynq.neurosomno_overlay import NeuroSomnoOverlay

# Initialize overlay (uses simulated fallback if hardware bitstream is absent)
accel = NeuroSomnoOverlay("neurosomno.bit")
accel.soft_reset()

# Run single inference with 784-sample Q3.13 integer array
pred = accel.infer_sample(sample_data)
print(f"Predicted Class: {pred} ({'Apnea' if pred == 1 else 'Normal'})")
```

### Bare-Metal ARM Cortex-A9 (Xilinx SDK / Vitis)
Include [`c_driver/neurosomno_hw.h`](c_driver/neurosomno_hw.h) and compile [`c_driver/neurosomno_api.c`](c_driver/neurosomno_api.c) within your BSP standalone application.
