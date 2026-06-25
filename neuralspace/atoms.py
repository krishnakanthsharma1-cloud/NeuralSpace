# atoms.py
import math
import hashlib
import os
import torch

# Cache pretrained weights at module level so every PureNeuralAtom
# instance doesn't re-read atom_weights.pth from disk individually
# (a FractalNode creates two atoms, and every node in the tree would
# otherwise trigger its own disk read + unpickle).
_WEIGHTS_CACHE = None
_WEIGHTS_PATH = "atom_weights.pth"


def _load_weights():
    global _WEIGHTS_CACHE
    if _WEIGHTS_CACHE is None and os.path.exists(_WEIGHTS_PATH):
        _WEIGHTS_CACHE = torch.load(_WEIGHTS_PATH, map_location='cpu')
    return _WEIGHTS_CACHE


class PureNeuralAtom:
    def __init__(self, seed, input_dim=512, feature_dim=256, load_pretrained=True):
        self.seed = seed
        weights = _load_weights() if load_pretrained else None

        if weights is not None:
            self.w_proj = weights['w_proj']
            self.b_proj = weights['b_proj']
            self.w_cls = weights['w_cls']
            self.b_cls = weights['b_cls']
        else:
            # Fallback: deterministic hash-based random initialization,
            # used only if no trained checkpoint is available yet.
            self.w_proj = [[(int(hashlib.sha256(f"{seed}_{r}_{c}".encode()).hexdigest()[:16], 16) / 1.8e19 * 2 - 1) for c in range(input_dim)] for r in range(feature_dim)]
            self.b_proj = [(int(hashlib.sha256(f"{seed}_b_{i}".encode()).hexdigest()[:16], 16) / 1.8e19 * 2 - 1) for i in range(feature_dim)]
            self.w_cls = [[(int(hashlib.sha256(f"{seed+99}_{r}_{c}".encode()).hexdigest()[:16], 16) / 1.8e19 * 2 - 1) for c in range(feature_dim)] for r in range(4)]
            self.b_cls = [(int(hashlib.sha256(f"{seed+99}_b_{i}".encode()).hexdigest()[:16], 16) / 1.8e19 * 2 - 1) for i in range(4)]

    def forward(self, x):
        # GELU(tanh-approx) projection, computed once per pre-activation
        # instead of three times per element as in the original version.
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
