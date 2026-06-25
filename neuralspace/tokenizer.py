import math
import hashlib
import re

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

    # --- Check for dangerous combinations ---
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

    # High-risk combinations — add a big boost to dedicated feature indices
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

    # --- Byte trigram hashing (your original logic) ---
    raw = code_string.encode('utf-8', errors='replace')
    padded = raw + b'\x00\x00\x00'
    for i in range(len(raw)):
        tri_hash = ((padded[i] * 31 + padded[i+1]) * 31 + padded[i+2])
        idx = (tri_hash % 150) + 160
        counts[idx] += 0.5

    vec = [math.log1p(c) for c in counts]
    norm = math.sqrt(sum(v * v for v in vec))
    return [v / norm for v in vec] if norm > 0 else vec