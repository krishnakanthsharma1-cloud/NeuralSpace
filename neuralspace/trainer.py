# trainer.py
import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from pathlib import Path
from neuralspace.tokenizer import code_to_512vec

# --- 1. Define the Neural Atom with Regularization ---
class TrainableAtom(nn.Module):
    def __init__(self, input_dim=512, feature_dim=4, output_dim=4, dropout_rate=0.3):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, feature_dim, bias=True)
        self.fc2 = nn.Linear(feature_dim, output_dim, bias=True)
        
        # Dropout layer - randomly turns off 30% of neurons during training
        # This forces the network to learn redundant, robust features
        self.dropout = nn.Dropout(dropout_rate)
        
        # Initialize weights to match your hash-based random [-1, 1] distribution
        nn.init.uniform_(self.fc1.weight, a=-1.0, b=1.0)
        nn.init.uniform_(self.fc1.bias, a=-1.0, b=1.0)
        nn.init.uniform_(self.fc2.weight, a=-1.0, b=1.0)
        nn.init.uniform_(self.fc2.bias, a=-1.0, b=1.0)

    def forward(self, x):
        # GELU approximation (exactly as in atoms.py)
        pre_act = self.fc1(x)
        gelu = 0.5 * pre_act * (1.0 + torch.tanh(0.79788 * (pre_act + 0.044715 * pre_act**3)))
        
        # APPLY DROPOUT (only active during training, automatically disabled during inference)
        gelu = self.dropout(gelu)
        
        logits = self.fc2(gelu)
        return logits

# --- 2. Dataset Loader (Unchanged) ---
class CodeDataset(Dataset):
    def __init__(self, safe_dir, threat_dir):
        self.vectors = []
        self.labels = []
        
        for file in Path(safe_dir).rglob('*.py'):
            with open(file, 'r', errors='ignore') as f:
                vec = code_to_512vec(f.read())
                self.vectors.append(vec)
                self.labels.append(0)  # Class 0 = "Logic/Safe"
        
        for file in Path(threat_dir).rglob('*.py'):
            with open(file, 'r', errors='ignore') as f:
                vec = code_to_512vec(f.read())
                self.vectors.append(vec)
                self.labels.append(3)  # Class 3 = "Sentinel/Threat"
        
        self.vectors = torch.tensor(self.vectors, dtype=torch.float32)
        self.labels = torch.tensor(self.labels, dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.vectors[idx], self.labels[idx]

# --- 3. Training Loop with Weight Decay ---
def train_atoms():
    SAFE_DATA = "./training_data/safe"
    THREAT_DATA = "./training_data/threat"
    
    if not os.path.exists(SAFE_DATA) or not os.path.exists(THREAT_DATA):
        print("[ERROR] Please create './training_data/safe/' and './training_data/threat/'")
        return

    dataset = CodeDataset(SAFE_DATA, THREAT_DATA)
    loader = DataLoader(dataset, batch_size=min(4, len(dataset)), shuffle=True)
    
    model = TrainableAtom()
    
    # WEIGHT DECAY (L2 Regularization) - penalizes large weights
    # This smooths the decision boundary and prevents overfitting
    optimizer = optim.Adam(model.parameters(), lr=0.01, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss()
    
    print("[*] Starting Training with Dropout (30%) & Weight Decay...")
    for epoch in range(300):  # Increased epochs slightly; regularization needs more time
        model.train()  # Ensure Dropout is active
        total_loss = 0
        for vecs, labels in loader:
            optimizer.zero_grad()
            logits = model(vecs)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        if epoch % 30 == 0:
            print(f"  Epoch {epoch:3d} | Loss: {total_loss/len(loader):.6f}")
    
    # --- 4. Save weights (Dropout automatically turns OFF for inference) ---
    model.eval()  # Not strictly necessary for saving, but good practice
    trained_weights = {
        'w_proj': model.fc1.weight.detach().tolist(),
        'b_proj': model.fc1.bias.detach().tolist(),
        'w_cls': model.fc2.weight.detach().tolist(),
        'b_cls': model.fc2.bias.detach().tolist(),
    }
    
    torch.save(trained_weights, "atom_weights.pth")
    print("\n[SUCCESS] Regularized training complete! Weights saved to 'atom_weights.pth'")
    print("[INFO] Run python main.py to test the new generalized engine.")

if __name__ == "__main__":
    train_atoms()