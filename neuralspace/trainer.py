# trainer.py
import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from pathlib import Path
from neuralspace.tokenizer import code_to_512vec  # FIXED: added neuralspace. prefix

# --- 1. Define the Neural Atom with larger capacity ---
class TrainableAtom(nn.Module):
    def __init__(self, input_dim=512, feature_dim=128, hidden_dim=32, output_dim=4, dropout_rate=0.3):
        super().__init__()
        # Two hidden layers: 512→128→32→4
        self.fc1 = nn.Linear(input_dim, feature_dim, bias=True)
        self.fc2 = nn.Linear(feature_dim, hidden_dim, bias=True)
        self.fc3 = nn.Linear(hidden_dim, output_dim, bias=True)
        
        # Dropout to prevent overfitting
        self.dropout = nn.Dropout(dropout_rate)
        
        # Initialize weights
        nn.init.uniform_(self.fc1.weight, a=-1.0, b=1.0)
        nn.init.uniform_(self.fc1.bias, a=-1.0, b=1.0)
        nn.init.uniform_(self.fc2.weight, a=-1.0, b=1.0)
        nn.init.uniform_(self.fc2.bias, a=-1.0, b=1.0)
        nn.init.uniform_(self.fc3.weight, a=-1.0, b=1.0)
        nn.init.uniform_(self.fc3.bias, a=-1.0, b=1.0)

    def forward(self, x):
        # GELU activation for first layer
        pre_act1 = self.fc1(x)
        gelu1 = 0.5 * pre_act1 * (1.0 + torch.tanh(0.79788 * (pre_act1 + 0.044715 * pre_act1**3)))
        gelu1 = self.dropout(gelu1)
        
        # GELU activation for second layer
        pre_act2 = self.fc2(gelu1)
        gelu2 = 0.5 * pre_act2 * (1.0 + torch.tanh(0.79788 * (pre_act2 + 0.044715 * pre_act2**3)))
        gelu2 = self.dropout(gelu2)
        
        logits = self.fc3(gelu2)
        return logits

# --- 2. Dataset Loader (unchanged) ---
class CodeDataset(Dataset):
    def __init__(self, safe_dir, threat_dir):
        self.vectors = []
        self.labels = []
        
        for file in Path(safe_dir).rglob('*.py'):
            with open(file, 'r', errors='ignore') as f:
                vec = code_to_512vec(f.read())
                self.vectors.append(vec)
                self.labels.append(0)
        
        for file in Path(threat_dir).rglob('*.py'):
            with open(file, 'r', errors='ignore') as f:
                vec = code_to_512vec(f.read())
                self.vectors.append(vec)
                self.labels.append(3)
        
        self.vectors = torch.tensor(self.vectors, dtype=torch.float32)
        self.labels = torch.tensor(self.labels, dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.vectors[idx], self.labels[idx]

# --- 3. Training Loop ---
def train_atoms():
    SAFE_DATA = "./training_data/safe"
    THREAT_DATA = "./training_data/threat"
    
    if not os.path.exists(SAFE_DATA) or not os.path.exists(THREAT_DATA):
        print("[ERROR] Please create './training_data/safe/' and './training_data/threat/'")
        return

    dataset = CodeDataset(SAFE_DATA, THREAT_DATA)
    loader = DataLoader(dataset, batch_size=min(4, len(dataset)), shuffle=True)
    
    model = TrainableAtom()  # 512→128→32→4
    optimizer = optim.Adam(model.parameters(), lr=0.01, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss()
    
    print("[*] Starting Training with larger network (512→128→32→4) and Dropout (30%) & Weight Decay...")
    for epoch in range(300):
        model.train()
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
    
    # --- 4. Save weights ---
    model.eval()
    trained_weights = {
        # Layer 1 (input to first hidden)
        'w_proj': model.fc1.weight.detach().tolist(),
        'b_proj': model.fc1.bias.detach().tolist(),
        # Layer 2 (first hidden to second hidden)
        'w_proj2': model.fc2.weight.detach().tolist(),
        'b_proj2': model.fc2.bias.detach().tolist(),
        # Layer 3 (second hidden to output)
        'w_cls': model.fc3.weight.detach().tolist(),
        'b_cls': model.fc3.bias.detach().tolist(),
    }
    
    torch.save(trained_weights, "atom_weights.pth")
    print("\n[SUCCESS] Regularized training complete! Weights saved to 'atom_weights.pth'")
    print("[INFO] Run python main.py to test the new generalized engine.")

if __name__ == "__main__":
    train_atoms()