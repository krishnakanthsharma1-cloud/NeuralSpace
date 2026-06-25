import json
import os
import time
import hashlib
import math
from neuralspace.tokenizer import code_to_512vec
from neuralspace.atoms import PureNeuralAtom

# --- MATH HELPERS ---
def cosine_similarity(v1, v2):
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(a * a for a in v2))
    return dot / (norm_a * norm_b) if norm_a > 0 and norm_b > 0 else 0.0

def quantize_int8(vec):
    return [int(max(-127, min(127, round(v * 127)))) for v in vec]

def dequantize_int8(q_vec):
    return [v / 127.0 for v in q_vec]

# --- FRACTAL NODE ---
class FractalNode:
    def __init__(self, node_id, parent_id, logic_seed, sent_seed, q_latent, depth):
        self.id = node_id
        self.parent_id = parent_id
        self.logic_seed = logic_seed
        self.sent_seed = sent_seed
        self.q_latent = q_latent
        self.depth = depth
        self.children = []
        self.last_accessed = time.time()
        self.logic_atom = PureNeuralAtom(self.logic_seed)
        self.sent_atom = PureNeuralAtom(self.sent_seed)

    def to_dict(self):
        return {
            "id": self.id, "parent_id": self.parent_id,
            "logic_seed": self.logic_seed, "sent_seed": self.sent_seed,
            "q_latent": self.q_latent, "depth": self.depth,
            "children": self.children, "last_accessed": self.last_accessed
        }

# --- COVALENT TREE ENGINE ---
class CovalentTreeEngine:
    def __init__(self, snapshot_path="tree_snapshot.json"):
        self.snapshot_path = snapshot_path
        self.nodes = {}
        self.root_id = "0x0000"
        self.max_depth = 5
        self.sim_threshold = 0.85
        
        # Golden Parameters from Batch-Forge
        self.logic_seed = 257
        self.sentinel_seed = 268
        self.logic_thresh = 0.2
        self.sentinel_thresh = 0.25
        
        self.load_snapshot()

    def load_snapshot(self):
        if os.path.exists(self.snapshot_path):
            with open(self.snapshot_path, 'r') as f:
                data = json.load(f)
                for k, v in data.items():
                    node = FractalNode(v["id"], v["parent_id"], v["logic_seed"], v["sent_seed"], v["q_latent"], v["depth"])
                    node.children = v["children"]
                    node.last_accessed = v["last_accessed"]
                    self.nodes[k] = node
        else:
            root_vec = [0.0] * 512
            root_node = FractalNode(self.root_id, None, self.logic_seed, self.sentinel_seed, quantize_int8(root_vec), 0)
            self.nodes[self.root_id] = root_node

    def save_snapshot(self):
        with open(self.snapshot_path, 'w') as f:
            json.dump({k: v.to_dict() for k, v in self.nodes.items()}, f, indent=4)

    def route_recursive(self, current_id, vec):
        node = self.nodes[current_id]
        if not node.children: return node
        best_child_id = None
        best_sim = -1.0
        for cid in node.children:
            child = self.nodes[cid]
            sim = cosine_similarity(vec, dequantize_int8(child.q_latent))
            if sim > best_sim:
                best_sim = sim
                best_child_id = cid
        if best_sim >= self.sim_threshold:
            return self.route_recursive(best_child_id, vec)
        return node

    def process_drop(self, code_string, file_id):
        vec = code_to_512vec(code_string)
        target_node = self.route_recursive(self.root_id, vec)
        
        s_score = target_node.sent_atom.forward(vec)[3]
        l_score = target_node.logic_atom.forward(vec)[0]
        
        # --- DIAGNOSTIC PRINT ---
        print(f"    [DEBUG] Checking {file_id}: S={s_score:.4f} (Thresh:{self.sentinel_thresh}), L={l_score:.4f} (Thresh:{self.logic_thresh})")
        
        status = "ALLOWED"
        # Logic enforcement
        if s_score >= self.sentinel_thresh: 
            status = "BLOCKED"
        elif l_score < self.logic_thresh: 
            status = "REJECTED"
        
        self.save_snapshot()
        return status, s_score, l_score, target_node.id