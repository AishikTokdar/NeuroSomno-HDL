#!/usr/bin/env bash

# NeuroSomno-HDL Execution & Verification Script
# Works on Linux, macOS, WSL, and Windows Git Bash / MSYS2

set -e

echo "========================================================"
echo "      NeuroSomno-HDL: Full Pipeline Execution          "
echo "========================================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ---------------------------------------------------------
# Phase 1: MATLAB Preprocessing & Quantization
# ---------------------------------------------------------
echo ""
echo "[Phase 1/2] Checking MATLAB Environment..."

if command -v matlab &> /dev/null; then
    echo "[INFO] MATLAB detected. Running preprocessing & model training pipeline..."
    if matlab -batch "run('matlab_preprocessing/preprocess_eeg.m'); run('matlab_preprocessing/segment_eeg.m'); run('matlab_preprocessing/handle_imbalance.m'); run('matlab_preprocessing/train_1dcnn.m'); run('matlab_preprocessing/extract_weights.m');"; then
        echo "[SUCCESS] MATLAB preprocessing and parameter extraction completed."
    else
        echo "[WARNING] MATLAB execution encountered an issue. Using pre-extracted hardware MIF files..."
    fi
elif command -v octave &> /dev/null; then
    echo "[INFO] GNU Octave detected. Running preprocessing & model training pipeline in Octave..."
    if octave --no-gui --eval "run('matlab_preprocessing/preprocess_eeg.m'); run('matlab_preprocessing/segment_eeg.m'); run('matlab_preprocessing/handle_imbalance.m'); run('matlab_preprocessing/train_1dcnn.m'); run('matlab_preprocessing/extract_weights.m');"; then
        echo "[SUCCESS] Octave preprocessing and parameter extraction completed."
    else
        echo "[WARNING] Octave execution encountered an issue. Using pre-extracted hardware MIF files..."
    fi
elif command -v python3 &> /dev/null || command -v python &> /dev/null; then
    PY_CMD="python3"
    command -v python3 &> /dev/null || PY_CMD="python"
    echo "[INFO] Running Python ML & Quantization Pipeline ($PY_CMD)..."
    $PY_CMD python_pipeline/preprocess_eeg.py
    $PY_CMD python_pipeline/train_model.py
    $PY_CMD python_pipeline/export_weights.py
    echo "[SUCCESS] Python pipeline completed."
else
    echo "[INFO] Utilizing pre-extracted memory initialization files (.mif / .mem / .txt) in hardware/mif/"
fi

# ---------------------------------------------------------
# Phase 2: Verilog Hardware RTL Behavioral Simulation & Synthesis
# ---------------------------------------------------------
echo ""
echo "[Phase 2/2] Checking Verilog Simulation & Synthesis Toolchain..."

if command -v vivado &> /dev/null; then
    echo "[INFO] Xilinx Vivado detected. Running batch simulation..."
    cat << 'EOF' > run_sim.tcl
create_project -force NeuroSomno_HDL ./vivado_proj -part xc7z020clg484-1
add_files [glob ./hardware/rtl/*.v]
add_files -fileset sim_1 [glob ./hardware/tb/*.v]
set_property top tb_top_sim [get_filesets sim_1]
set_property top_lib xil_defaultlib [get_filesets sim_1]
update_compile_order -fileset sim_1
launch_simulation
run -all
exit
EOF
    vivado -mode batch -source run_sim.tcl
    rm -f run_sim.tcl
    echo "[SUCCESS] Vivado behavioral simulation finished successfully."

elif command -v iverilog &> /dev/null; then
    echo "[INFO] Icarus Verilog (iverilog) detected. Compiling RTL & Testbench..."
    cd hardware/mif
    iverilog -g2012 -I ../rtl -o sim_top ../rtl/*.v ../tb/tb_top_sim.v
    echo "[INFO] Running VVP simulation..."
    vvp sim_top
    cd "$SCRIPT_DIR"
    echo "[SUCCESS] Icarus Verilog simulation finished successfully."

else
    echo "[INFO] Neither Xilinx Vivado nor Icarus Verilog (iverilog) was found in PATH."
    echo "[INFO] Verilog RTL files and simulation testbenches are located at:"
    echo "       - RTL: hardware/rtl/"
    echo "       - Testbench: hardware/tb/tb_top_sim.v"
    echo "       - MIF Memory Files: hardware/mif/"
fi

if command -v yosys &> /dev/null; then
    echo ""
    echo "[INFO] Yosys Open-Source Synthesis Suite detected. Running RTL synthesis check..."
    yosys -p "read_verilog -sv hardware/rtl/*.v; synth_xilinx -top zynet_top; stat"
    echo "[SUCCESS] Yosys RTL synthesis check completed."
fi

echo ""
echo "========================================================"
echo "          NeuroSomno-HDL Execution Complete            "
echo "========================================================"
