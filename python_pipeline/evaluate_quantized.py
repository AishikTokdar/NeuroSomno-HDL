"""Evaluate the integer FCN on the complete held-out split, separately from RTL."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from bit_true_emulator import BitTrueNetwork
from train_model import NeuroSomnoFCN, compute_metrics, downsample_signals

ROOT = Path(__file__).resolve().parents[1]


def evaluate(dataset_path, mif_dir, output_path):
    dataset_path, mif_dir = Path(dataset_path), Path(mif_dir)
    with np.load(dataset_path, allow_pickle=False) as dataset:
        x, y = dataset['X_test'], dataset['Y_test']
        subjects = sorted(set(dataset['subjects_test'].tolist()))
        synthetic = bool(dataset['synthetic'])
    if not len(y) or len(x) != len(y):
        raise ValueError('A nonempty, aligned held-out split is required')
    floating_inputs = downsample_signals(x)
    quantized = np.clip(np.rint(floating_inputs.astype(np.float64)*8192), -32768, 32767).astype(np.int32)
    net = BitTrueNetwork(str(mif_dir))
    predictions = np.array([net.infer_sample(sample)[0] for sample in quantized])
    metrics = compute_metrics(y, predictions)
    metrics['confusion'] = {key:int(np.sum((y==truth)&(predictions==pred)))
                            for key,truth,pred in [('tn',0,0),('fp',0,1),('fn',1,0),('tp',1,1)]}
    manifest = json.loads((mif_dir/'manifest.json').read_text(encoding='utf-8'))
    report = {'evaluation':'integer arithmetic reference; not a full-split RTL simulation',
              'data':'synthetic' if synthetic else 'annotated EDF', 'test_windows':len(y),
              'subjects':subjects, 'format':'signed Q3.13', 'metrics':metrics,
              'checkpoint_sha256':manifest['checkpoint_sha256'],
              'dataset_sha256':hashlib.sha256(dataset_path.read_bytes()).hexdigest()}
    checkpoint = ROOT/'models/fcn_model.pt'
    if checkpoint.exists():
        if hashlib.sha256(checkpoint.read_bytes()).hexdigest() != manifest['checkpoint_sha256']:
            raise ValueError('Local floating-point checkpoint does not match the exported network')
        model = NeuroSomnoFCN()
        model.load_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=True))
        model.eval()
        with torch.no_grad():
            floating_predictions = model(torch.from_numpy(floating_inputs)).argmax(1).numpy()
        report['floating_point_comparison'] = {'windows':len(y),
            'different_class_decisions':int(np.sum(floating_predictions != predictions))}
    output = Path(output_path); output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    return report


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset',default=str(ROOT/'dataset/eeg_data_split.npz'))
    parser.add_argument('--mif-dir',default=str(ROOT/'hardware/mif'))
    parser.add_argument('--output',default=str(ROOT/'results/verification/quantized_metrics.json'))
    args = parser.parse_args()
    evaluate(args.dataset,args.mif_dir,args.output)
