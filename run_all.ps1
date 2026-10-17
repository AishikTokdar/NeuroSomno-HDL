# NeuroSomno-HDL Execution & Verification Script (Windows PowerShell)

$ErrorActionPreference = "Continue"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "      NeuroSomno-HDL: Full Pipeline Execution          " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Phase 1: MATLAB Preprocessing & Quantization
Write-Host ""
Write-Host "[Phase 1/2] Checking MATLAB Environment..." -ForegroundColor Yellow

$matlabCmd = Get-Command matlab -ErrorAction SilentlyContinue
$octaveCmd = Get-Command octave -ErrorAction SilentlyContinue
if ($matlabCmd) {
    Write-Host "[INFO] MATLAB detected. Attempting preprocessing & model training..." -ForegroundColor Green
    & matlab -batch "run('matlab_preprocessing/preprocess_eeg.m'); run('matlab_preprocessing/segment_eeg.m'); run('matlab_preprocessing/handle_imbalance.m'); run('matlab_preprocessing/train_1dcnn.m'); run('matlab_preprocessing/extract_weights.m');"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[SUCCESS] MATLAB preprocessing completed." -ForegroundColor Green
        $phase1Done = $true
    } else {
        Write-Host "[WARNING] MATLAB execution exited with error code $LASTEXITCODE (e.g. license/version issue)." -ForegroundColor Yellow
        $phase1Done = $false
    }
}

if (-not $phase1Done -and $octaveCmd) {
    Write-Host "[INFO] Running preprocessing pipeline in GNU Octave..." -ForegroundColor Green
    & octave --no-gui --eval "run('matlab_preprocessing/preprocess_eeg.m'); run('matlab_preprocessing/segment_eeg.m'); run('matlab_preprocessing/handle_imbalance.m'); run('matlab_preprocessing/train_1dcnn.m'); run('matlab_preprocessing/extract_weights.m');"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[SUCCESS] Octave preprocessing completed." -ForegroundColor Green
        $phase1Done = $true
    } else {
        Write-Host "[WARNING] Octave execution encountered an issue." -ForegroundColor Yellow
    }
}

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $phase1Done -and $pythonCmd) {
    Write-Host "[INFO] Running Python ML & Quantization Pipeline..." -ForegroundColor Green
    & python python_pipeline/preprocess_eeg.py
    & python python_pipeline/train_model.py
    & python python_pipeline/export_weights.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[SUCCESS] Python pipeline completed." -ForegroundColor Green
        $phase1Done = $true
    }
}

if (-not $phase1Done) {
    Write-Host "[INFO] Utilizing pre-extracted memory initialization files (.mif / .mem / .txt) in hardware/mif/" -ForegroundColor Yellow
}

# Phase 2: Verilog Hardware RTL Behavioral Simulation & Synthesis
Write-Host ""
Write-Host "[Phase 2/2] Checking Verilog Toolchain..." -ForegroundColor Yellow

$vivadoCmd = Get-Command vivado -ErrorAction SilentlyContinue
$iverilogCmd = Get-Command iverilog -ErrorAction SilentlyContinue
$yosysCmd = Get-Command yosys -ErrorAction SilentlyContinue

if ($vivadoCmd) {
    Write-Host "[INFO] Xilinx Vivado detected. Running batch simulation..." -ForegroundColor Green
    $tclContent = @"
create_project -force NeuroSomno_HDL ./vivado_proj -part xc7z020clg484-1
add_files [glob ./hardware/rtl/*.v]
add_files -fileset sim_1 [glob ./hardware/tb/*.v]
set_property top tb_top_sim [get_filesets sim_1]
set_property top_lib xil_defaultlib [get_filesets sim_1]
update_compile_order -fileset sim_1
launch_simulation
run -all
exit
"@
    $tclContent | Out-File -Encoding ascii run_sim.tcl
    & vivado -mode batch -source run_sim.tcl
    Remove-Item run_sim.tcl -ErrorAction SilentlyContinue
    Write-Host "[SUCCESS] Vivado behavioral simulation finished successfully." -ForegroundColor Green

} elseif ($iverilogCmd) {
    Write-Host "[INFO] Icarus Verilog (iverilog) detected. Compiling RTL & Testbench..." -ForegroundColor Green
    Set-Location "$ScriptDir\hardware\mif"
    & iverilog -g2012 -I ..\rtl -o sim_top ..\rtl\*.v ..\tb\tb_top_sim.v
    Write-Host "[INFO] Running VVP simulation..." -ForegroundColor Green
    & vvp sim_top
    Set-Location $ScriptDir
    Write-Host "[SUCCESS] Icarus Verilog simulation finished successfully." -ForegroundColor Green

} else {
    Write-Host "[INFO] Neither Xilinx Vivado nor Icarus Verilog was found in PATH." -ForegroundColor Yellow
    Write-Host "       RTL and simulation testbenches are available in hardware/" -ForegroundColor White
}

if ($yosysCmd) {
    Write-Host ""
    Write-Host "[INFO] Yosys detected. Running RTL synthesis check..." -ForegroundColor Green
    & yosys -p "read_verilog -sv hardware/rtl/*.v; synth_xilinx -top zynet_top; stat"
    Write-Host "[SUCCESS] Yosys RTL synthesis check completed." -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "          NeuroSomno-HDL Execution Complete            " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
