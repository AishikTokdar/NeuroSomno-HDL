"""Validate every MIF parameter, sigmoid ROM and simulation vector."""
import argparse
import hashlib
import json
from pathlib import Path
import re

import numpy as np

ARCHITECTURE = (784, 30, 30, 10, 2)
ROOT = Path(__file__).resolve().parents[1]


def read_words(path, width=16):
    lines = path.read_text(encoding='ascii').splitlines()
    if not lines or any(not re.fullmatch('[01]{' + str(width) + '}', line) for line in lines):
        raise ValueError(f'{path.name}: expected nonempty, exact {width}-bit binary lines')
    values = np.array([int(line, 2) for line in lines], dtype=np.int32)
    return np.where(values >= 32768, values - 65536, values) if width == 16 else values


def validate_assets(mif_dir='hardware/mif', checkpoint=None):
    directory = Path(mif_dir)
    expected = {}
    for layer, (inputs, outputs) in enumerate(zip(ARCHITECTURE, ARCHITECTURE[1:]), 1):
        for neuron in range(outputs):
            expected[f'w_{layer}_{neuron}.mif'] = inputs
            expected[f'b_{layer}_{neuron}.mif'] = 1
    legacy = {f'{kind}_4_{neuron}.mif' for kind in ('w', 'b') for neuron in range(2, 10)}
    found = {p.name:p for p in directory.iterdir() if p.is_file() and p.suffix.lower()=='.mif'}
    errors, files, arrays = [], [], {}
    for missing in sorted(set(expected)-set(found)):
        errors.append(f'Missing active parameter file: {missing}')
    for name, path in sorted(found.items()):
        role = 'active' if name in expected else 'obsolete' if name in legacy else 'unexpected'
        record = {'file':name, 'role':role, 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        try:
            values = read_words(path)
            size = expected.get(name, 1 if name.startswith('b_') else 10)
            if role == 'unexpected':
                raise ValueError(f'{name}: unexpected parameter file')
            if len(values) != size:
                raise ValueError(f'{name}: {len(values)} words; expected {size}')
            arrays[name] = values
            record.update(words=len(values), minimum=int(values.min()), maximum=int(values.max()), valid=True)
        except (ValueError, UnicodeError) as exc:
            errors.append(str(exc)); record.update(valid=False, error=str(exc))
        files.append(record)
    manifest_path = directory/'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    if manifest.get('architecture') != list(ARCHITECTURE):
        errors.append('Manifest architecture differs from the active model or is missing')
    hashes = manifest.get('parameter_sha256', {})
    if hashes and set(hashes) != set(expected):
        errors.append('Manifest hashes must cover exactly the 144 active files')
    for record in files:
        if record['role']=='active' and hashes and hashes.get(record['file']) != record['sha256']:
            errors.append(f"{record['file']}: checksum differs from the export manifest")
    checkpoint_status = 'not supplied'
    if checkpoint is not None:
        import torch
        checkpoint = Path(checkpoint)
        state = torch.load(checkpoint, map_location='cpu', weights_only=True)
        if hashlib.sha256(checkpoint.read_bytes()).hexdigest() != manifest.get('checkpoint_sha256'):
            errors.append('Checkpoint checksum differs from the export manifest')
        for layer, outputs in enumerate(ARCHITECTURE[1:],1):
            for kind, tensor_key in [('w','weight'),('b','bias')]:
                values = state[f'fc{layer}.{tensor_key}'].detach().cpu().numpy().astype(np.float64)
                shape = (outputs, ARCHITECTURE[layer-1]) if kind=='w' else (outputs,)
                if values.shape != shape or not np.isfinite(values).all():
                    errors.append(f'Checkpoint fc{layer}.{tensor_key}: invalid shape or nonfinite data')
                    continue
                quantized = np.clip(np.rint(values*8192),-32768,32767).astype(np.int32)
                for neuron in range(outputs):
                    name = f'{kind}_{layer}_{neuron}.mif'
                    if name in arrays and not np.array_equal(arrays[name], np.atleast_1d(quantized[neuron])):
                        errors.append(f'{name}: values differ from the quantized checkpoint')
        checkpoint_status = 'compared every active word'
    auxiliaries = {}
    for name,width,length in [('sig_rom.mem',16,1024),('test_data.txt',16,30*784),('test_labels.txt',4,30)]:
        try:
            values = read_words(directory/name,width)
            if len(values) != length:
                raise ValueError(f'{name}: {len(values)} words; expected {length}')
            if name=='sig_rom.mem':
                x = (np.arange(1024)-512)/128
                if not np.array_equal(values,np.rint(8192/(1+np.exp(-x))).astype(np.int32)):
                    raise ValueError('Sigmoid ROM differs from the expected Q3.13 lookup table')
            if name=='test_labels.txt' and not np.isin(values,[0,1]).all():
                raise ValueError('Test labels must be classes 0 or 1')
            auxiliaries[name] = {'words':len(values),'valid':True,
                                  'sha256':hashlib.sha256((directory/name).read_bytes()).hexdigest()}
        except (ValueError,UnicodeError,OSError) as exc:
            errors.append(str(exc)); auxiliaries[name] = {'valid':False,'error':str(exc)}
    active = [r for r in files if r['role']=='active' and r['valid']]
    return {'valid':not errors,'mif_files_checked':len(found),'active_files':len(active),
            'active_parameters':sum(r['words'] for r in active),
            'obsolete_files':[r['file'] for r in files if r['role']=='obsolete'],
            'checkpoint':checkpoint_status,'manifest_checksums':bool(hashes),'errors':errors,
            'auxiliary_files':auxiliaries,'files':files}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mif-dir',default=str(ROOT/'hardware/mif'))
    parser.add_argument('--checkpoint',help='Compare every active word with a PyTorch checkpoint')
    parser.add_argument('--report',default=str(ROOT/'results/verification/mif_validation.json'))
    args = parser.parse_args()
    result = validate_assets(args.mif_dir,args.checkpoint)
    output = Path(args.report); output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f"MIF files: {result['mif_files_checked']}; active: {result['active_files']}; "
          f"parameters: {result['active_parameters']}; obsolete: {len(result['obsolete_files'])}")
    print('PASS' if result['valid'] else 'FAIL: '+'; '.join(result['errors']))
    return 0 if result['valid'] else 1


if __name__=='__main__':
    raise SystemExit(main())
