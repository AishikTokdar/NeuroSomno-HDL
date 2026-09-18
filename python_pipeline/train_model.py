"""
NeuroSomno-HDL: PyTorch Model Training & SMOTE Class Balancing Suite
Trains the 15-layer Hybrid 1D-CNN on full 2816-sample signals,
and the hardware-aligned 784-input Quantized FCN model.
"""

import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from scipy.interpolate import interp1d

class Hybrid1DCNN(nn.Module):
    """15-layer 1D Convolutional Neural Network matching MATLAB global_model architecture."""
    def __init__(self, num_classes=2):
        super(Hybrid1DCNN, self).__init__()
        self.features = nn.Sequential(
            nn.BatchNorm1d(1),
            nn.Conv1d(1, 3, kernel_size=100, stride=2, padding=50),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2, stride=2),
            nn.Conv1d(3, 50, kernel_size=10, stride=1, padding=5),
            nn.MaxPool1d(kernel_size=2, stride=2),
            nn.ReLU(),
            nn.Conv1d(50, 30, kernel_size=30, stride=1, padding=15),
            nn.MaxPool1d(kernel_size=2, stride=2),
            nn.ReLU(),
            nn.BatchNorm1d(30)
        )
        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(30, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        out = self.classifier(x)
        return out

class NeuroSomnoFCN(nn.Module):
    """4-Layer Fully Connected Hardware-Aligned Network (784-30-30-10-10)."""
    def __init__(self, num_classes=2):
        super(NeuroSomnoFCN, self).__init__()
        self.fc1 = nn.Linear(784, 30)
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Linear(30, 30)
        self.relu2 = nn.ReLU()
        self.fc3 = nn.Linear(30, 10)
        self.sig3 = nn.Sigmoid()
        self.fc4 = nn.Linear(10, 10)
        self.sig4 = nn.Sigmoid()
        self.out_head = nn.Linear(10, num_classes)

    def forward(self, x):
        x = self.relu1(self.fc1(x))
        x = self.relu2(self.fc2(x))
        x = self.sig3(self.fc3(x))
        x = self.sig4(self.fc4(x))
        logits = self.out_head(x)
        return logits

def apply_smote(X, Y, k_neighbors=5):
    """Applies SMOTE neighborhood interpolation on minority class (Apnea = 1)."""
    idx_0 = np.where(Y == 0)[0]
    idx_1 = np.where(Y == 1)[0]
    n0, n1 = len(idx_0), len(idx_1)
    
    if n1 >= n0 or n1 == 0:
        return X, Y
    
    diff = n0 - n1
    X_minority = X[idx_1]
    synthetic = np.zeros((diff, X.shape[1]), dtype=np.float32)
    
    for i in range(diff):
        base_idx = np.random.randint(0, n1)
        base = X_minority[base_idx]
        dists = np.sum((X_minority - base) ** 2, axis=1)
        sort_idx = np.argsort(dists)
        k_pool = min(k_neighbors + 1, n1)
        neighbor_idx = sort_idx[np.random.randint(1, k_pool)] if k_pool > 1 else 0
        neighbor = X_minority[neighbor_idx]
        synthetic[i] = base + np.random.rand() * (neighbor - base)
        
    X_balanced = np.vstack([X[idx_0], X[idx_1], synthetic])
    Y_balanced = np.concatenate([np.zeros(n0, dtype=np.int64), np.ones(n1, dtype=np.int64), np.ones(diff, dtype=np.int64)])
    
    perm = np.random.permutation(len(X_balanced))
    return X_balanced[perm], Y_balanced[perm]

def downsample_signals(X, target_len=784):
    """Interpolates signals from 2816 to 784 points for FCN input."""
    n_samples, orig_len = X.shape
    t_orig = np.linspace(0, 1, orig_len)
    t_target = np.linspace(0, 1, target_len)
    f = interp1d(t_orig, X, axis=1, kind='linear')
    return f(t_target).astype(np.float32)

def compute_metrics(y_true, y_pred):
    """Computes clinical performance metrics."""
    tp = np.sum((y_true == 1) & (y_pred == 1))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    
    accuracy = (tp + tn) / (tp + tn + fp + fn + 1e-12)
    sensitivity = tp / (tp + fn + 1e-12)  # Recall
    specificity = tn / (tn + fp + 1e-12)
    precision = tp / (tp + fp + 1e-12)
    balanced_acc = 0.5 * (sensitivity + specificity)
    f1 = 2 * (precision * sensitivity) / (precision + sensitivity + 1e-12)
    
    return {
        "accuracy": accuracy * 100,
        "balanced_acc": balanced_acc * 100,
        "sensitivity": sensitivity * 100,
        "specificity": specificity * 100,
        "precision": precision * 100,
        "f1": f1
    }

def train_and_evaluate(dataset_path="dataset/eeg_data_split.npz", models_dir="models"):
    """Trains both 1D-CNN and FCN models, printing comparative metrics."""
    os.makedirs(models_dir, exist_ok=True)
    if not os.path.exists(dataset_path):
        print("[INFO] Dataset not found, running preprocessing first...")
        from preprocess_eeg import run_preprocessing_pipeline
        run_preprocessing_pipeline()
        
    data = np.load(dataset_path)
    X_train, Y_train = data['X_train'], data['Y_train']
    X_val, Y_val = data['X_val'], data['Y_val']
    X_test, Y_test = data['X_test'], data['Y_test']
    
    print(f"[INFO] Raw Class Distribution: Normal(0)={np.sum(Y_train==0)}, Apnea(1)={np.sum(Y_train==1)}")
    X_train_bal, Y_train_bal = apply_smote(X_train, Y_train)
    print(f"[INFO] After SMOTE Balancing: Total={len(X_train_bal)}, Balanced 50/50")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Training execution device: {device}")
    
    # 1. Train 15-Layer 1D-CNN
    print("\n--- Training 15-Layer Hybrid 1D-CNN (Full 2816 Resolution) ---")
    cnn_model = Hybrid1DCNN().to(device)
    train_loader = DataLoader(
        TensorDataset(torch.from_numpy(X_train_bal).unsqueeze(1), torch.from_numpy(Y_train_bal)),
        batch_size=64, shuffle=True
    )
    optimizer = optim.Adam(cnn_model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()
    
    cnn_model.train()
    for epoch in range(1, 11):
        running_loss = 0.0
        for bx, by in train_loader:
            bx, by = bx.to(device), by.to(device)
            optimizer.zero_grad()
            out = cnn_model(bx)
            loss = criterion(out, by)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
        if epoch % 5 == 0 or epoch == 10:
            print(f"Epoch {epoch}/10 - Loss: {running_loss/len(train_loader):.4f}")
            
    cnn_model.eval()
    with torch.no_grad():
        test_x = torch.from_numpy(X_test).unsqueeze(1).to(device)
        cnn_preds = cnn_model(test_x).argmax(dim=1).cpu().numpy()
    cnn_metrics = compute_metrics(Y_test, cnn_preds)
    print(f"[CNN RESULTS] Accuracy: {cnn_metrics['accuracy']:.2f}% | Balanced Acc: {cnn_metrics['balanced_acc']:.2f}% | F1: {cnn_metrics['f1']:.4f}")
    torch.save(cnn_model.state_dict(), os.path.join(models_dir, "cnn_model.pt"))

    # 2. Train Downsampled FCN for Hardware HDL Quantization
    print("\n--- Training Hardware-Target FCN (784-30-30-10-10) ---")
    X_train_fcn = downsample_signals(X_train_bal, 784)
    X_test_fcn = downsample_signals(X_test, 784)
    
    fcn_model = NeuroSomnoFCN().to(device)
    fcn_loader = DataLoader(
        TensorDataset(torch.from_numpy(X_train_fcn), torch.from_numpy(Y_train_bal)),
        batch_size=64, shuffle=True
    )
    fcn_opt = optim.Adam(fcn_model.parameters(), lr=1e-3)
    
    fcn_model.train()
    for epoch in range(1, 11):
        running_loss = 0.0
        for bx, by in fcn_loader:
            bx, by = bx.to(device), by.to(device)
            fcn_opt.zero_grad()
            out = fcn_model(bx)
            loss = criterion(out, by)
            loss.backward()
            fcn_opt.step()
            running_loss += loss.item()
        if epoch % 5 == 0 or epoch == 10:
            print(f"Epoch {epoch}/10 - Loss: {running_loss/len(fcn_loader):.4f}")
            
    fcn_model.eval()
    with torch.no_grad():
        fcn_preds = fcn_model(torch.from_numpy(X_test_fcn).to(device)).argmax(dim=1).cpu().numpy()
    fcn_metrics = compute_metrics(Y_test, fcn_preds)
    print(f"[FCN RESULTS] Accuracy: {fcn_metrics['accuracy']:.2f}% | Balanced Acc: {fcn_metrics['balanced_acc']:.2f}% | F1: {fcn_metrics['f1']:.4f}")
    torch.save(fcn_model.state_dict(), os.path.join(models_dir, "fcn_model.pt"))
    print(f"[SUCCESS] Saved model checkpoints to {models_dir}/")

if __name__ == "__main__":
    train_and_evaluate()
