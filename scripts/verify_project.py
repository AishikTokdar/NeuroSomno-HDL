"""One reproducible software verification entry point; failures propagate to CI."""
import argparse
import json
import gzip
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'results/verification'
LOGS = ROOT / '.cache/verification'


def run(name, command, *, cwd=ROOT, timeout=180):
    print(f'[CHECK] {name}', flush=True)
    result = subprocess.run(list(map(str, command)), cwd=cwd, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    with gzip.open(LOGS/(name+'.txt.gz'),'wt',encoding='utf-8') as log:
        log.write(result.stdout)
    if result.returncode:
        print(result.stdout)
        raise RuntimeError(f'{name} failed with exit code {result.returncode}')
    print(f'[PASS] {name}', flush=True)


def main():
    parser = argparse.ArgumentParser()
    for tool in ('iverilog', 'vvp', 'yosys', 'node', 'gcc'):
        parser.add_argument('--' + tool, default=shutil.which(tool))
    parser.add_argument('--train', action='store_true', help='Retrain and replace active fixtures before verification')
    parser.add_argument('--synthesize', action='store_true', help='Also map the core to Xilinx 7-series cells (requires Yosys)')
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    for tool in ('iverilog', 'vvp', 'node', 'gcc'):
        if not getattr(args, tool):
            raise RuntimeError(f'Required tool missing: {tool}')
    if args.synthesize and not args.yosys:
        raise RuntimeError('--synthesize requires Yosys')
    if args.train:
        run('training', [sys.executable, '-u', '-c',
            "import sys,torch;sys.path.insert(0,'python_pipeline');torch.set_num_threads(2);"
            "from train_model import train_and_evaluate;from export_weights import export_model_weights,export_test_vectors;"
            "train_and_evaluate();export_model_weights();export_test_vectors()"], timeout=600)
    run('regressions', [sys.executable, 'tests/audit_project.py', '--iverilog', args.iverilog, '--vvp', args.vvp])
    evidence = json.loads((OUTPUT / 'evidence.json').read_text())
    if evidence['summary']['skipped']:
        raise RuntimeError('Verification skipped required regression checks')
    memory_command = [sys.executable, 'python_pipeline/verify_quantization.py']
    checkpoint = ROOT / 'models/fcn_model.pt'
    if checkpoint.exists():
        memory_command += ['--checkpoint', str(checkpoint)]
    run('parameter_integrity', memory_command)
    run('rtl_parity', [sys.executable, 'python_pipeline/verify_rtl.py', '--iverilog', args.iverilog, '--vvp', args.vvp])
    run('dashboard', [args.node, 'tests/audit_dashboard.cjs'])
    with tempfile.TemporaryDirectory(prefix='neurosomno-c-test-') as tmp:
        executable = Path(tmp) / ('driver.exe' if sys.platform == 'win32' else 'driver')
        run('c_compile', [args.gcc, '-Wall', '-Wextra', '-Werror', '-std=c11',
                         'tests/test_c_driver.c', 'embedded/c_driver/neurosomno_api.c', '-o', executable])
        run('c_runtime', [executable])
    if args.yosys:
        sources = ' '.join('"' + p.as_posix() + '"' for p in sorted((ROOT / 'hardware/rtl').glob('*.v')))
        synthesis = ('synth_xilinx -family xc7 -top zynet_top -noiopad' if args.synthesize else
                     'hierarchy -top zynet_top; proc')
        run('synthesis' if args.synthesize else 'yosys_check',
            [args.yosys, '-Q', '-T', '-p', f'read_verilog -sv {sources}; {synthesis}; check -assert; stat'],
            cwd=ROOT / 'hardware/mif', timeout=900)
    summary = {'regressions': evidence['summary'],
               'rtl_parity': json.loads((OUTPUT / 'rtl_parity.json').read_text()),
               'memory_assets': {k:v for k,v in json.loads((OUTPUT/'mif_validation.json').read_text()).items()
                                 if k not in ('files','auxiliary_files')},
               'dashboard': '5 functional checks; mock DOM, no rendering test',
               'c_driver': 'compiled and executed with mock MMIO/transport',
               'synthesis': 'Xilinx 7-series mapping' if args.synthesize else
                            'Yosys structural check' if args.yosys else 'not run: Yosys unavailable',
               'vendor_timing_power_and_physical_board': 'not verified',
               'real_patient_accuracy': 'not verified'}
    (OUTPUT / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print('[SUCCESS] Software checks completed. See results/verification/summary.json')


if __name__ == '__main__':
    main()
