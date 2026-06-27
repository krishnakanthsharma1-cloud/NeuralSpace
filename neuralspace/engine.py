import json
import os
import time
import hashlib
import math
from neuralspace.tokenizer import code_to_512vec, code_to_512vec_with_language
from neuralspace.atoms import PureNeuralAtom
from neuralspace.hive_mind import HiveMind

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
        self.history = []

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
        self.logic_seed = 257
        self.sentinel_seed = 268
        self.logic_thresh = 0.2
        self.sentinel_thresh = 0.10  # Lowered for better detection
        self.hive_mind = HiveMind(consensus_threshold=0.7)
        self.load_snapshot()
        self.hive_mind.register_agent(self.root_id)

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

    def calculate_drift_velocity(self, node, vec):
        node.history.append(vec)
        if len(node.history) > 10:
            node.history.pop(0)
        if len(node.history) < 2:
            return 0.0
        total_drift = 0.0
        for i in range(1, len(node.history)):
            sim = cosine_similarity(node.history[i-1], node.history[i])
            drift = 1.0 - sim
            total_drift += drift
        return total_drift / (len(node.history) - 1)
    
    def anticipate_and_fracture(self, node, vec):
        drift_velocity = self.calculate_drift_velocity(node, vec)
        if drift_velocity > 0.5 and node.depth < self.max_depth:
            print(f"    [ARCHITECT] High drift velocity detected: {drift_velocity:.2f}")
            print(f"    [ARCHITECT] Anticipatory fracture! Spawning new branch...")
            new_id = f"0x{len(self.nodes):04X}"
            new_node = FractalNode(
                node_id=new_id,
                parent_id=node.id,
                logic_seed=self.logic_seed + len(self.nodes),
                sent_seed=self.sentinel_seed + len(self.nodes),
                q_latent=quantize_int8(vec),
                depth=node.depth + 1
            )
            self.nodes[new_id] = new_node
            node.children.append(new_id)
            self.hive_mind.register_agent(new_id)
            self.save_snapshot()
            print(f"    [ARCHITECT] 🚀 Spawned anticipatory branch: {new_id}")
            return new_node
        return node

    def query_hive_mind(self, vec, file_id):
        agent_ids = list(self.nodes.keys())
        for node_id in agent_ids:
            node = self.nodes[node_id]
            s_score = node.sent_atom.forward(vec)[3]
            confidence = min(1.0, len(node.children) / 10.0 + 0.5)
            self.hive_mind.submit_vote(node_id, s_score, confidence)
        return self.hive_mind.get_consensus(agent_ids)

    def _check_known_patterns(self, code_string: str) -> tuple:
        """
        DIRECT PRE-CHECK: Scan the raw code string for known dangerous patterns,
        including common obfuscation techniques.
        Returns (is_threat, reason)
        """
        # --- JavaScript / Node.js patterns ---
        if 'base64' in code_string and 'eval' in code_string:
            return (True, "base64 + eval (JavaScript obfuscated payload)")
        
        if 'eval' in code_string and 'Buffer.from' in code_string:
            return (True, "eval + Buffer.from (JavaScript obfuscation)")
        
        if 'require' in code_string and 'eval' in code_string:
            return (True, "require + eval (JavaScript remote code execution)")
        
        # --- Go patterns ---
        if 'syscall.Exec' in code_string:
            return (True, "syscall.Exec (Go shell execution)")
        
        if 'exec.Command' in code_string:
            return (True, "exec.Command (Go shell execution)")
        
        if 'syscall' in code_string and 'Exec' in code_string:
            return (True, "syscall + Exec (Go shell execution)")
        
        # --- Python patterns ---
        if 'exec(' in code_string and 'base64' in code_string:
            return (True, "exec + base64 (obfuscated payload)")
        
        if 'os.system' in code_string and 'rm -rf' in code_string:
            return (True, "os.system + rm -rf (destructive command)")
        
        # --- INDIRECTION / EVASION PATTERNS ---
        # 1. getattr(module, 'func')()
        if 'getattr(' in code_string and ('exec' in code_string or 'eval' in code_string):
            return (True, "getattr indirection (exec/eval)")
        
        # 2. eval(chr(97)+chr(98)+...)
        if 'eval(' in code_string and 'chr(' in code_string:
            return (True, "eval + chr (character obfuscation)")
        
        # 3. __import__('os').system(...)
        if "__import__" in code_string and ("exec" in code_string or "system" in code_string):
            return (True, "__import__ dynamic import")
        
        # 4. exec("""...""") with multiline
        if 'exec("""' in code_string and 'base64' in code_string:
            return (True, "exec + base64 with multiline")
        
        # 5. System command with string concatenation
        if 'system(' in code_string and ('+' in code_string or 'join' in code_string):
            return (True, "system call with string concatenation")
        
        return (False, "")

    def process_drop(self, code_string, file_id):
        vec = code_to_512vec_with_language(code_string, file_id)
        target_node = self.route_recursive(self.root_id, vec)
        s_score = target_node.sent_atom.forward(vec)[3]
        l_score = target_node.logic_atom.forward(vec)[0]
        print(f"    [DEBUG] Checking {file_id}: S={s_score:.4f} (Thresh:{self.sentinel_thresh}), L={l_score:.4f} (Thresh:{self.logic_thresh})")
        status = "ALLOWED"
        if s_score >= self.sentinel_thresh: 
            status = "BLOCKED"
        elif l_score < self.logic_thresh: 
            status = "REJECTED"
        self.save_snapshot()
        return status, s_score, l_score, target_node.id

    def process_drop_explain(self, code_string, file_id):
        """Runs the engine and returns a detailed decision trace."""
        
        # --- DIRECT PRE-CHECK: Check for known dangerous patterns ---
        is_threat, reason = self._check_known_patterns(code_string)
        if is_threat:
            print(f"    [PRE-CHECK] Dangerous pattern detected: {reason}")
            return "BLOCKED", 1.0, 0.0, "0x0000", [f"🔴 PRE-CHECK: {reason}"]
        
        # --- Otherwise, run the normal pipeline ---
        vec = code_to_512vec_with_language(code_string, file_id)
        target_node = self.route_recursive(self.root_id, vec)
        target_node = self.anticipate_and_fracture(target_node, vec)
        
        consensus = self.query_hive_mind(vec, file_id)
        print(f"    [HIVE] Consensus: {consensus['decision']} (Score: {consensus['consensus']:.2f})")
        
        s_score = target_node.sent_atom.forward(vec)[3]
        l_score = target_node.logic_atom.forward(vec)[0]
        
        trace = []
        from neuralspace.tokenizer import get_combination_hits
        hits = get_combination_hits(code_string)
        if hits:
            trace.append("⚠️  Dangerous combinations detected:")
            for hit in hits:
                trace.append(f"   - {hit} (+8.0 threat boost)")
        else:
            trace.append("✅ No dangerous combinations detected.")
        
        # --- ADD TAINT ANALYSIS RESULTS ---
        try:
            from neuralspace.ast_analyzer import code_to_features_with_taint
            ext = os.path.splitext(file_id)[1].lower() if '.' in file_id else '.py'
            print(f"    [DEBUG] Running taint analysis for {file_id} with ext={ext}")
            taint_results = code_to_features_with_taint(code_string, ext)
            print(f"    [DEBUG] Taint results: has_tainted_sink={taint_results['has_tainted_sink']}, flow={taint_results['taint_flow']}")
            if taint_results["has_tainted_sink"]:
                trace.append("🔍 TAINT ANALYSIS: Tainted data reaches dangerous sink!")
                for flow in taint_results["taint_flow"]:
                    trace.append(f"   - {flow[0]} → {flow[1]}")
        except Exception as e:
            trace.append(f"[!] Taint analysis skipped: {e}")
            print(f"    [DEBUG] Taint analysis error: {e}")
        
        trace.append(f"📊 Sentinel Score: {s_score:.4f} (Threshold: {self.sentinel_thresh})")
        trace.append(f"📊 Logic Score:    {l_score:.4f} (Threshold: {self.logic_thresh})")
        
        status = "ALLOWED"
        if s_score >= self.sentinel_thresh:
            status = "BLOCKED"
            trace.append("🚫 BLOCKED: Sentinel score exceeded threshold.")
        elif l_score < self.logic_thresh:
            status = "REJECTED"
            trace.append("🚫 REJECTED: Logic score below threshold.")
        else:
            trace.append("✅ ALLOWED: File passed all checks.")
        
        if consensus["decision"] == "THREAT" and status == "ALLOWED":
            status = "BLOCKED"
            trace.append("🧠 HIVE MIND: Collective consensus overrode individual decision.")
        
        # --- Signed reporting ---
        if status == "BLOCKED":
            try:
                import requests
                from neuralspace.trust_layer import TrustNode
                ext = os.path.splitext(file_id)[1].lstrip('.') if file_id else 'unknown'
                AGGREGATOR_URL = os.environ.get("NEURALSPACE_AGGREGATOR", "http://localhost:8000")
                report = {
                    "combo_hits": hits,
                    "sentinel_score": s_score,
                    "logic_score": l_score,
                    "node_path": target_node.id,
                    "language": ext,
                    "timestamp": str(time.time())
                }
                trust_node = TrustNode()
                signed_report = trust_node.sign_report(report)
                requests.post(f"{AGGREGATOR_URL}/report-threat", json=signed_report, timeout=2)
                print(f"[*] Signed threat report sent to aggregator")
            except Exception as e:
                print(f"[!] Reporting failed: {e}")
        
        self.save_snapshot()
        return status, s_score, l_score, target_node.id, trace