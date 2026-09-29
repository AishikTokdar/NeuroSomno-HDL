# Hardware RTL Architecture & Simulation Details

This directory contains the Verilog HDL implementation of the neural network accelerator and the simulation environment used to validate the model's accuracy in a software-only simulation environment.

---

## Hardware Accelerator Core Design

The accelerator is structured as a pipelined multi-layer feed-forward network with a layer architecture of **784 - 30 - 30 - 10 - 10** nodes:

```
Streamed EEG Input (AXI-Stream)
      │
      ▼
 [Layer 1] ──── (30 Neurons, ReLU activation)
      │
      ▼
 [Layer 2] ──── (30 Neurons, ReLU activation)
      │
      ▼
 [Layer 3] ──── (10 Neurons, Sigmoid ROM activation)
      │
      ▼
 [Layer 4] ──── (10 Neurons, Sigmoid ROM activation)
      │
      ▼
 [Argmax Comparator]
      │
      ▼
Predicted Class (0: Normal / 1: Apnea)
```

---

## Detailed Module Descriptions

*   **[`neuron.v`](rtl/neuron.v)**: Computes Multiply-Accumulate (MAC) operations, loads bias, and applies ReLU/Sigmoid activation functions. Features saturation logic (`+32767`/`-32768`) to prevent overflow wrap-around.
*   **[`weight_memory.v`](rtl/weight_memory.v)**: Dual-port BRAM blocks loaded with weight parameter arrays during startup using `$readmemb`.
*   **[`sig_rom.v`](rtl/sig_rom.v)**: ROM lookup table for Sigmoid activation using input index shifting:
    ```verilog
    wire [9:0] index = i_data[15:6] + 10'd512;
    ```
*   **[`relu.v`](rtl/relu.v)**: Saturated Rectified Linear Unit activation block.
*   **[`layer1.v`](rtl/layer1.v) to [`layer4.v`](rtl/layer4.v)**: Serialized layers that manage parallel execution of neuron compute elements and stream data forward.
*   **[`find_max_out.v`](rtl/find_max_out.v)**: Sequential argmax block that computes final class ID from Layer 4 output values.
*   **[`zynet_top.v`](rtl/zynet_top.v)**: Top-level neural network accelerator integrating Layer 1–4 pipelines with streaming input buffers.
*   **[`axi_lite_wrapper.v`](rtl/axi_lite_wrapper.v)**: Interfacing register map for weight loading, triggering, and control flow.
*   **[`ahi_tracker.v`](rtl/ahi_tracker.v)**: Real-time Apnea-Hypopnea Index clinical accumulator, severity classifier, and hypoxia duration alarm.
*   **[`conv1d_pe.v`](rtl/conv1d_pe.v)**: Streaming 1D Convolution Processing Element with sliding window sample buffer and parallel multiplier tree.
*   **[`maxpool1d.v`](rtl/maxpool1d.v)**: Streaming 1D Max Pooling module with configurable window size and stride.
*   **[`iir_notch_50hz.v`](rtl/iir_notch_50hz.v)**: Digital 2nd-order Direct-Form II Transposed IIR Notch filter for powerline hum elimination.
*   **[`iir_bandpass.v`](rtl/iir_bandpass.v)**: Digital 4th-order cascaded Biquad bandpass filter isolating 0.5–45 Hz physiological EEG cortical rhythms.

---

## Testbench Execution Sequence ([`tb_top_sim.v`](tb/tb_top_sim.v))

The main testbench simulates the ARM host behavior using the following AXI transaction sequence:
1.  **Reset**: Asserts reset to reset the state machines and counters.
2.  **Trigger Network**: Writes `32'h2` (Start bit) to `REG_CTRL` via AXI-Lite to configure the accelerator to stream data mode.
3.  **Stream Data**: Streams 784 16-bit elements of a test sample sequentially using the AXI-Stream interface.
4.  **Wait for Interrupt**: Pools the physical interrupt pin `intr` (or registers status bit `1` of `REG_STATUS`) to detect that classification is complete.
5.  **Read Prediction**: Reads `REG_NNOUT` to capture the predicted class (0/1) and compares it with [`test_labels.txt`](mif/test_labels.txt) to calculate accuracy.

---

## Simulation & Execution Guide

For full step-by-step instructions on running simulations and synthesis using either **Xilinx Vivado** (Primary Default) or **100% Open-Source Tools** (Icarus Verilog + GTKWave + Yosys), see the main [Execution Guide in README.md](../README.md#complete-step-by-step-execution-guide).

---

<a id="visualizing-waveforms"></a>
## Visualizing Waveforms in Vivado & GTKWave

### Vivado Waveform Viewer
1. Locate the simulation signal tree inside the **Scope** window.
2. Navigate to `tb_top_sim` -> `uut` -> `l1` (Layer 1).
3. Drag `o_data` and `o_valid` into the **Wave** window.
4. Right-click `o_data` -> **Radix** -> **Real Settings...** -> Choose **Fixed Point** -> **Signed** -> **Fraction Length: 13**.
5. Select **Waveform Style** -> **Analog** to display signals as continuous waveforms.

### GTKWave (Open-Source Viewer)
1. Generate `.vcd` trace output during Icarus simulation (`vvp sim_top`).
2. Open GTKWave: `gtkwave dump.vcd`.
3. Add internal layer registers and fixed-point data busses to the trace display window.

---

> [!IMPORTANT]
> The target hardware model uses 16-bit signed fixed-point math (`Q3.13` format). The simulation results demonstrate a hardware classification accuracy of **89.00%** on the full validation set. Note that the default 30-sample behavioral simulation testbench (`tb_top_sim.v`) will output either **86.67%** or **90.00%** accuracy in the simulator console, corresponding to this overall performance on this subset.
