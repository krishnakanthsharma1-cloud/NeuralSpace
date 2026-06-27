# atoms.py
import math
import hashlib
import os
import torch

# --- Per-seed weight cache (instead of global) ---
_WEIGHTS_CACHE = {}

def _load_weights_for_seed(seed):
    """Load weights specifically for a given seed."""
    if seed in _WEIGHTS_CACHE:
        return _WEIGHTS_CACHE[seed]
    
    weights_path = "atom_weights.pth"
    if os.path.exists(weights_path):
        # Load the base trained weights
        base_weights = torch.load(weights_path, map_location='cpu')
        # For now, we use the same weights for all seeds.
        # TODO: In the future, fine-tune per seed using the seed as a mutation key.
        _WEIGHTS_CACHE[seed] = base_weights
        return base_weights
    return None

class PureNeuralAtom:
    def __init__(self, seed, input_dim=512, feature_dim=256, load_pretrained=True):
        self.seed = seed
        weights = _load_weights_for_seed(seed) if load_pretrained else None

        if weights is not None:
            self.w_proj = weights['w_proj']
            self.b_proj = weights['b_proj']
            self.w_cls = weights['w_cls']
            self.b_cls = weights['b_cls']
        else:
            # Fallback: deterministic hash-based random initialization
            self.w_proj = [[(int(hashlib.sha256(f"{seed}_{r}_{c}".encode()).hexdigest()[:16], 16) / 1.8e19 * 2 - 1) for c in range(input_dim)] for r in range(feature_dim)]
            self.b_proj = [(int(hashlib.sha256(f"{seed}_b_{i}".encode()).hexdigest()[:16], 16) / 1.8e19 * 2 - 1) for i in range(feature_dim)]
            self.w_cls = [[(int(hashlib.sha256(f"{seed+99}_{r}_{c}".encode()).hexdigest()[:16], 16) / 1.8e19 * 2 - 1) for c in range(feature_dim)] for r in range(4)]
            self.b_cls = [(int(hashlib.sha256(f"{seed+99}_b_{i}".encode()).hexdigest()[:16], 16) / 1.8e19 * 2 - 1) for i in range(4)]

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