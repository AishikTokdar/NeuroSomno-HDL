# Validation Results & Synthesis Reports

This document contains detailed performance benchmarks and device utilization reports for both the software and hardware components of the **NeuroSomno-HDL** framework.

---

## 1. MATLAB Classification Performance

The models were evaluated using two distinct training dataset balancing configurations to assess performance improvements:

### Software Evaluation Metrics

| Metric | Random Oversampling | SMOTE |
| :--- | :---: | :---: |
| **Accuracy** | 99.53% | **99.62%** |
| **Balanced Accuracy** | 91.23% | **91.58%** |
| **Sensitivity (Recall)** | 82.61% | **83.33%** |
| **Specificity** | **99.85%** | 99.84% |
| **Precision** | **91.57%** | 86.96% |
| **F1 Score** | **0.8686** | 0.8511 |

---

## 2. FPGA RTL Accelerator Resource Utilization

The Verilog RTL design was synthesized and implemented targeting the **Xilinx ZedBoard (XC7Z020-CLG484-1)** FPGA.

### Device Resource Utilization Report

| Resource | Available | Used (Neuron Module) | Used (Full FCN Accelerator) | Utilization % (Full) |
| :--- | :---: | :---: | :---: | :---: |
| **LUT** | 53,200 | 51 | 6,290 | 11.82% |
| **FF** | 106,400 | 43 | 6,653 | 6.25% |
| **DSP** | 220 | 2 | 160 *[1]* | **72.73%** |
| **BRAM** | 140 | 0.50 | 15.00 *[2]* | 10.71% |

*[1] Theoretical minimum is 80 DSPs (1 per neuron). Vivado infers 2 DSPs per neuron due to port signedness and packing constraints.*
*[2] Sigmoid ROMs are synthesized as Distributed ROM using LUTs. If mapped to BRAM, utilization is 25 BRAMs.*

### Power Analysis (Vivado Power Analyzer)
*   **Total On-Chip Power:** **0.368 W**
*   **Dynamic Power:** 0.243 W (66%)
*   **Device Static Power:** 0.125 W (34%)
*   **Junction Temperature:** 26.5 °C (Thermal Margin: 58.5 °C)

---

## 3. Timing Constraints Report

A clock constraint of **10.000 ns** (100 MHz clock frequency) was applied to the design. The timing summary reports clean closure without any violations:

*   **Target Clock Period:** 10.000 ns
*   **Worst Negative Slack (WNS):** **4.156 ns** (Met)
*   **Worst Hold Slack (WHS):** **0.082 ns** (Met)
*   **Maximum Target Frequency (Fmax):** $\approx \mathbf{171.12\text{ MHz}}$

> [!NOTE]
> The ~10% drop in accuracy in the hardware compared to MATLAB (from 99.62% to 89.00%) is a standard consequence of 16-bit signed fixed-point quantization (Q3.13 format) constraints. Note that the default Vivado testbench (`tb_top_sim.v`) only runs a subset of 30 samples to minimize simulation time, which will output either **86.67%** or **90.00%** accuracy in the console, corresponding to this 89.00% overall quantized model performance.
