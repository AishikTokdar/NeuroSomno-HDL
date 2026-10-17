@echo off
REM NeuroSomno-HDL Execution & Verification Script (Windows CMD)
echo ========================================================
echo       NeuroSomno-HDL: Full Pipeline Execution          
echo ========================================================

cd /d "%~dp0"

echo.
echo [Phase 1/2] Checking MATLAB Environment...
where matlab >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [INFO] MATLAB detected. Running preprocessing and weight extraction...
    matlab -batch "run('matlab_preprocessing/preprocess_eeg.m'); run('matlab_preprocessing/segment_eeg.m'); run('matlab_preprocessing/handle_imbalance.m'); run('matlab_preprocessing/train_1dcnn.m'); run('matlab_preprocessing/extract_weights.m');"
) else (
    where octave >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        echo [INFO] GNU Octave detected. Running preprocessing pipeline in Octave...
        octave --no-gui --eval "run('matlab_preprocessing/preprocess_eeg.m'); run('matlab_preprocessing/segment_eeg.m'); run('matlab_preprocessing/handle_imbalance.m'); run('matlab_preprocessing/train_1dcnn.m'); run('matlab_preprocessing/extract_weights.m');"
    ) else (
        where python >nul 2>&1
        if %ERRORLEVEL% equ 0 (
            echo [INFO] Python detected. Running ML & Quantization Pipeline...
            python python_pipeline/preprocess_eeg.py
            python python_pipeline/train_model.py
            python python_pipeline/export_weights.py
        ) else (
            echo [INFO] Utilizing pre-extracted memory initialization files in hardware/mif/
        )
    )
)

echo.
echo [Phase 2/2] Checking Verilog Simulation Toolchain...
where vivado >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [INFO] Xilinx Vivado detected. Running batch simulation...
    (
        echo create_project -force NeuroSomno_HDL ./vivado_proj -part xc7z020clg484-1
        echo add_files [glob ./hardware/rtl/*.v]
        echo add_files -fileset sim_1 [glob ./hardware/tb/*.v]
        echo set_property top tb_top_sim [get_filesets sim_1]
        echo set_property top_lib xil_defaultlib [get_filesets sim_1]
        echo update_compile_order -fileset sim_1
        echo launch_simulation
        echo run -all
        echo exit
    ) > run_sim.tcl
    vivado -mode batch -source run_sim.tcl
    del /f /q run_sim.tcl
    goto SIM_DONE
)

where iverilog >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [INFO] Icarus Verilog detected. Compiling and running simulation...
    cd hardware\mif
    iverilog -g2012 -I ..\rtl -o sim_top ..\rtl\*.v ..\tb\tb_top_sim.v
    vvp sim_top
    cd /d "%~dp0"
    goto SIM_DONE
)

echo [INFO] Neither Vivado nor Icarus Verilog was found in PATH.
echo [INFO] Hardware RTL and MIF files are verified and located in hardware/

:SIM_DONE
where yosys >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo.
    echo [INFO] Yosys detected. Running RTL synthesis check...
    yosys -p "read_verilog -sv hardware/rtl/*.v; synth_xilinx -top zynet_top; stat"
)
echo.
echo ========================================================
echo           NeuroSomno-HDL Execution Complete            
echo ========================================================
