# run_benchmark.py
import os
import json
import subprocess
from pathlib import Path

# Helper to run subprocess with proper encoding
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

# -- Scan with NeuralSpace --
def scan_with_neuralspace(file_path):
    result = run_cmd(["neuralspace", "scan", str(file_path), "--quarantine", "rename"])
    if result and "BLOCKED" in result.stdout:
        return "BLOCKED"
    return "ALLOWED"

# -- Scan with Bandit (only for Python) --
def scan_with_bandit(file_path):
    ext = file_path.suffix.lower()
    if ext != '.py':
        return "SKIPPED"
    result = run_cmd(["bandit", "-f", "json", str(file_path)])
    if not result:
        return "ERROR"
    try:
        data = json.loads(result.stdout)
        if data.get("metrics", {}).get("_totals", {}).get("SEVERITY", {}).get("HIGH", 0) > 0:
            return "BLOCKED"
    except:
        pass
    return "ALLOWED"

# -- Scan with Semgrep (supports multiple languages) --
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

# -- Benchmark --
def run_benchmark():
    print("\n" + "="*70)
    print("🧠 NEURALSPACE BENCHMARK")
    print("="*70)
    print(f"{'File':35} | {'NS':8} | {'Bandit':8} | {'Semgrep':8} | {'Expected':10}")
    print("-"*70)

    results = []
    
    # Scan malicious files
    for folder in ["malicious", "safe"]:
        folder_path = Path("benchmark_dataset") / folder
        if not folder_path.exists():
            continue
        for file in folder_path.glob("*"):
            if file.suffix not in ['.py', '.js', '.go']:
                continue
            
            print(f"[*] Scanning {file.name}...")
            
            neuralspace_result = scan_with_neuralspace(file)
            bandit_result = scan_with_bandit(file)
            semgrep_result = scan_with_semgrep(file)
            
            # Determine expected result
            expected = "MALICIOUS" if folder == "malicious" else "SAFE"
            status = "✅" if (folder == "malicious" and neuralspace_result == "BLOCKED") or (folder == "safe" and neuralspace_result == "ALLOWED") else "❌"
            
            results.append({
                "file": str(file.name),
                "neuralspace": neuralspace_result,
                "bandit": bandit_result,
                "semgrep": semgrep_result,
                "expected": expected,
                "status": status
            })
            
            print(f"{str(file.name):35} | {neuralspace_result:8} | {bandit_result:8} | {semgrep_result:8} | {expected:10}  {status}")
            print("-"*70)
    
    # Summary
    total = len(results)
    correct = sum(1 for r in results if r["status"] == "✅")
    print(f"\n📊 SUMMARY: {correct}/{total} correct ({correct/total*100:.1f}%)")
    print("="*70)
    
    # Detailed breakdown
    print("\n📋 DETAILED BREAKDOWN:")
    for r in results:
        print(f"  {r['file']:30} → {r['status']} (NS: {r['neuralspace']}, Bandit: {r['bandit']}, Semgrep: {r['semgrep']})")

if __name__ == "__main__":
    run_benchmark()