# atoms.py
import math
import hashlib
import os
import torch
import importlib.resources

# --- Per-seed weight cache ---
_WEIGHTS_CACHE = {}

def _load_weights_for_seed(seed):
    """Load weights specifically for a given seed."""
    if seed in _WEIGHTS_CACHE:
        return _WEIGHTS_CACHE[seed]
    
    try:
        # Load the pre-trained weights bundled with the package
        weights_file = importlib.resources.files('neuralspace') / 'atom_weights.pth'
        if weights_file.exists():
            weights = torch.load(str(weights_file), map_location='cpu')
            _WEIGHTS_CACHE[seed] = weights
            return weights
    except Exception:
        pass
    
    # Fallback: Try CWD (for development)
    if os.path.exists("atom_weights.pth"):
        weights = torch.load("atom_weights.pth", map_location='cpu')
        _WEIGHTS_CACHE[seed] = weights
        return weights
    
    return None

class PureNeuralAtom:
    # feature_dim is now 128 (larger network) to match the trainer
    def __init__(self, seed, input_dim=512, feature_dim=128, output_dim=4, load_pretrained=True):
        self.seed = seed
        self.input_dim = input_dim
        self.feature_dim = feature_dim
        
        weights = _load_weights_for_seed(seed) if load_pretrained else None

        if weights is not None:
            # If weights are from an older model with different dimensions, we should handle it,
            # but for now we assume they match the new architecture.
            self.w_proj = weights['w_proj']
            self.b_proj = weights['b_proj']
            self.w_cls = weights['w_cls']
            self.b_cls = weights['b_cls']
        else:
            # Fallback: deterministic hash-based random initialization
            self.w_proj = [[(int(hashlib.sha256(f"{seed}_{r}_{c}".encode()).hexdigest()[:16], 16) / 1.8e19 * 2 - 1) for c in range(input_dim)] for r in range(feature_dim)]
            self.b_proj = [(int(hashlib.sha256(f"{seed}_b_{i}".encode()).hexdigest()[:16], 16) / 1.8e19 * 2 - 1) for i in range(feature_dim)]
            self.w_cls = [[(int(hashlib.sha256(f"{seed+99}_{r}_{c}".encode()).hexdigest()[:16], 16) / 1.8e19 * 2 - 1) for c in range(feature_dim)] for r in range(output_dim)]
            self.b_cls = [(int(hashlib.sha256(f"{seed+99}_b_{i}".encode()).hexdigest()[:16], 16) / 1.8e19 * 2 - 1) for i in range(output_dim)]

    def forward(self, x):
        latent = []
        for wr, b in zip(self.w_proj, self.b_proj):
            pre_act = sum(w * xi for w, xi in zip(wr, x)) + b
            gelu = 0.5 * pre_act * (1.0 + math.tanh(0.79788 * (pre_act + 0.044715 * pre_act ** 3)))
            latent.append(gelu)

        logits = [sum(w * li for w, li in zip(wr, latent)) + b for wr, b in zip(self.w_cls, self.b_cls)]
        m = max(logits)
        exps = [math.exp(l - m) for l in logits]
        total = sum(exps)
        return [e / total for e in exps]