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

*   **`neuron.v`**: Computes Multiply-Accumulate (MAC) operations, loads bias, and applies ReLU/Sigmoid activation functions. Features saturation logic (`+32767`/`-32768`) to prevent overflow wrap-around.
*   **`weight_memory.v`**: Dual-port BRAM blocks loaded with weight parameter arrays during startup using `$readmemb`.
*   **`sig_rom.v`**: ROM lookup table for Sigmoid activation using input index shifting:
    ```verilog
    wire [9:0] index = i_data[15:6] + 10'd512;
    ```
*   **`relu.v`**: Saturated Rectified Linear Unit activation block.
*   **`layer1.v` to `layer4.v`**: Serialized layers that manage parallel execution of neuron compute elements and stream data forward.
*   **`find_max_out.v`**: Sequential argmax block that computes final class ID from Layer 4 output values.
*   **`axi_lite_wrapper.v`**: Interfacing register map for weight loading, triggering, and control flow.

---

## Testbench Execution Sequence (`tb_top_sim.v`)

The main testbench simulates the ARM host behavior using the following AXI transaction sequence:
1.  **Reset**: Asserts reset to reset the state machines and counters.
2.  **Trigger Network**: Writes `32'h2` (Start bit) to `REG_CTRL` via AXI-Lite to configure the accelerator to stream data mode.
3.  **Stream Data**: Streams 784 16-bit elements of a test sample sequentially using the AXI-Stream interface.
4.  **Wait for Interrupt**: Pools the physical interrupt pin `intr` (or registers status bit `1` of `REG_STATUS`) to detect that classification is complete.
5.  **Read Prediction**: Reads `REG_NNOUT` to capture the predicted class (0/1) and compares it with `test_labels.txt` to calculate accuracy.

---

## Detailed Vivado Simulation Run Guide

Follow these steps to set up and run behavioral simulations:

### 1. File Import
*   Create a project named `NeuroSomno_HDL` in Vivado.
*   Import all Verilog files from `hardware/rtl/` as **Design Sources**.
*   Import all Verilog files from `hardware/tb/` as **Simulation Sources**.
*   Import `hardware/constraints/zedboard.xdc` as a **Constraints File**.

### 2. Configure Simulation Working Directory
To ensure the simulation can read `.mif` and `.txt` files using `$readmemb`:
*   Go to **Settings** > **Simulation**.
*   Set the **Simulation Run Directory** option to your local `hardware/mif/` folder path.
*   *Alternative:* Copy all files from `hardware/mif/` directly to `<project_name>.sim/sim_1/behav/xsim/`.

### 3. Run Behavioral Simulation
*   Click **Run Simulation** -> **Run Behavioral Simulation**.
*   In the simulator console, run: `run -all`.
*   Verify prediction outputs in the Tcl Console.

> [!IMPORTANT]
> The target hardware model uses 16-bit signed fixed-point math (`Q3.13` format). The simulation results demonstrate a hardware classification accuracy of **89.00%** on the full validation set. Note that the default 30-sample behavioral simulation testbench (`tb_top_sim.v`) will output either **86.67%** or **90.00%** accuracy in the simulator console, corresponding to this overall performance on this subset.
