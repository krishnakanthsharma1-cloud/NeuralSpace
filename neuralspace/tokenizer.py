# tokenizer.py
import math
import hashlib
import re
from pathlib import Path

# --- Import the taint analyzer ---
try:
    from neuralspace.ast_analyzer import code_to_features_with_taint
    HAS_TAINT = True
except ImportError:
    HAS_TAINT = False
    print("[!] Taint analyzer not available. Falling back to regex tokenizer.")

# ======================================================================
# FALLBACK: REGEX-BASED TOKENIZER (with explicit pattern detection)
# ======================================================================
def code_to_512vec(code_string: str):
    counts = [0.0] * 512

    threat_indicators = {"os", "sys", "eval", "exec", "socket", "subprocess", "open", "rm", "rf", "input", "compile"}
    algo_indicators = {"def", "return", "sorted", "math", "len", "range", "int", "float", "list", "if", "else"}

    tokens = re.findall(r'\b\w+\b|[^\w\s]', code_string)

    for token in tokens:
        h_base = int(hashlib.md5(token.encode()).hexdigest(), 16) % 120
        if token in threat_indicators or '/' in token or '\\' in token or 'rm' in token:
            idx = 340 + h_base
        elif token in algo_indicators:
            idx = 20 + h_base
        else:
            idx = 160 + h_base
        counts[idx] += 1.0

    # --- Hard‑coded combination features (from tokens) ---
    token_set = set(tokens)

    has_requests = 'requests' in token_set
    has_exec = 'exec' in token_set
    has_eval = 'eval' in token_set
    has_base64 = 'base64' in token_set
    has_os = 'os' in token_set
    has_subprocess = 'subprocess' in token_set
    has_socket = 'socket' in token_set
    has_system = 'system' in token_set
    has_connect = 'connect' in token_set
    has_popen = 'Popen' in token_set

    # Python/JS combinations
    if has_requests and has_exec:
        counts[490] += 5.0
    if has_base64 and has_exec:
        counts[491] += 5.0
    if has_requests and has_base64 and has_exec:
        counts[492] += 8.0
    if has_os and has_system:
        counts[493] += 5.0
    if has_socket and has_connect:
        counts[494] += 5.0
    if has_subprocess and has_popen:
        counts[495] += 5.0
    if has_base64 and has_eval:
        counts[496] += 6.0
    if has_eval and 'require' in token_set:
        counts[497] += 4.0

    # --- EXPLICIT PATTERN DETECTION (with HIGH BOOST to guarantee detection) ---
    # 1. JavaScript: base64 + eval (direct string match) – BOOST 20.0
    if 'base64' in code_string and 'eval' in code_string:
        counts[496] += 20.0  # Increased from 10.0 to 20.0

    # 2. Go: syscall.Exec or exec.Command – BOOST 20.0
    if 'syscall.Exec' in code_string or 'exec.Command' in code_string:
        counts[498] += 20.0  # Increased from 10.0 to 20.0

    # 3. eval + Buffer.from (JavaScript obfuscation) – BOOST 20.0
    if 'eval' in code_string and 'Buffer.from' in code_string:
        counts[499] += 20.0  # Increased from 10.0 to 20.0

    # 4. JavaScript require + eval – BOOST 15.0
    if 'require' in code_string and 'eval' in code_string:
        counts[497] += 15.0

    # 5. Go syscall import + Exec – BOOST 20.0
    if 'syscall' in code_string and 'Exec' in code_string:
        counts[498] += 20.0

    # --- Byte trigram hashing ---
    raw = code_string.encode('utf-8', errors='replace')
    padded = raw + b'\x00\x00\x00'
    for i in range(len(raw)):
        tri_hash = ((padded[i] * 31 + padded[i+1]) * 31 + padded[i+2])
        idx = (tri_hash % 150) + 160
        counts[idx] += 0.5

    vec = [math.log1p(c) for c in counts]
    norm = math.sqrt(sum(v * v for v in vec))
    return [v / norm for v in vec] if norm > 0 else vec

# ======================================================================
# TAINT‑AWARE TOKENIZER
# ======================================================================
def code_to_512vec_with_taint(code_string: str, file_extension: str = '.py', use_taint: bool = True):
    if HAS_TAINT and use_taint:
        taint_features = code_to_features_with_taint(code_string, file_extension)
    else:
        taint_features = {
            "has_tainted_exec": False,
            "has_tainted_system": False,
            "has_tainted_eval": False,
            "has_tainted_sink": False,
            "taint_count": 0,
            "sink_count": 0,
            "sink_list": []
        }

    base_vec = code_to_512vec(code_string)

    # Add taint features
    if taint_features["has_tainted_exec"]:
        base_vec[480] += 8.0
    if taint_features["has_tainted_eval"]:
        base_vec[481] += 8.0
    if taint_features["has_tainted_system"]:
        base_vec[482] += 8.0
    if taint_features["has_tainted_sink"]:
        base_vec[483] += 5.0

    sink_count = min(taint_features["sink_count"], 5)
    base_vec[484] += sink_count * 2.0

    taint_count = min(taint_features["taint_count"], 5)
    base_vec[485] += taint_count * 2.0

    norm = math.sqrt(sum(v * v for v in base_vec))
    if norm > 0:
        return [v / norm for v in base_vec]
    return base_vec

# ======================================================================
# LANGUAGE‑AWARE ENTRY POINT
# ======================================================================
def code_to_512vec_with_language(code_string: str, file_path: str):
    ext = Path(file_path).suffix.lower()
    return code_to_512vec_with_taint(code_string, ext, use_taint=True)

# ======================================================================
# HELPERS FOR EXPLAINABILITY
# ======================================================================
def get_combination_hits(code_string: str):
    tokens = re.findall(r'\b\w+\b|[^\w\s]', code_string)
    token_set = set(tokens)

    hits = []
    has_requests = 'requests' in token_set
    has_exec = 'exec' in token_set
    has_eval = 'eval' in token_set
    has_base64 = 'base64' in token_set
    has_os = 'os' in token_set
    has_socket = 'socket' in token_set
    has_subprocess = 'subprocess' in token_set
    has_system = 'system' in token_set
    has_connect = 'connect' in token_set
    has_popen = 'Popen' in token_set

    if has_requests and has_exec:
        hits.append("requests + exec (potential remote code execution)")
    if has_base64 and has_exec:
        hits.append("base64 + exec (potential obfuscated payload)")
    if has_requests and has_base64 and has_exec:
        hits.append("requests + base64 + exec (triple threat combo)")
    if has_os and has_system:
        hits.append("os + system (shell command execution)")
    if has_socket and has_connect:
        hits.append("socket + connect (potential reverse shell)")
    if has_subprocess and has_popen:
        hits.append("subprocess + Popen (process spawning)")
    if has_base64 and has_eval:
        hits.append("base64 + eval (potential obfuscated payload)")
    if has_eval and 'require' in token_set:
        hits.append("eval + require (potential remote code execution)")

    # Explicit pattern hits
    if 'syscall.Exec' in code_string or 'exec.Command' in code_string:
        hits.append("syscall.Exec or exec.Command (Go shell execution)")
    if 'eval' in code_string and 'Buffer.from' in code_string:
        hits.append("eval + Buffer.from (JavaScript obfuscation)")

    return hits