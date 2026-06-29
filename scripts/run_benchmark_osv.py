# run_benchmark_osv.py
import os
import json
import subprocess
from pathlib import Path

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

def scan_directory(dir_path, label):
    """Scan all files in a directory."""
    results = []
    if not dir_path.exists():
        return results
    for file in dir_path.glob("*"):
        if file.suffix in ['.py', '.js', '.go', '.c', '.cpp', '.java']:
            if file.is_file():
                ns_result = scan_with_neuralspace(file)
                bandit_result = scan_with_bandit(file)
                semgrep_result = scan_with_semgrep(file)
                results.append({
                    "file": file.name,
                    "path": str(file),
                    "neuralspace": ns_result,
                    "bandit": bandit_result,
                    "semgrep": semgrep_result,
                    "expected": label,
                    "correct": (label == "MALICIOUS" and ns_result == "BLOCKED") or (label == "SAFE" and ns_result == "ALLOWED")
                })
    return results

def run_benchmark_osv():
    print("\n" + "="*70)
    print("🧠 NEURALSPACE BENCHMARK (Real + Synthetic)")
    print("="*70)
    
    # Check for real datasets
    real_malicious = Path("benchmark_dataset/real_malicious")
    real_safe = Path("benchmark_dataset/real_safe")
    synthetic_malicious = Path("benchmark_dataset/malicious")
    synthetic_safe = Path("benchmark_dataset/safe")
    
    all_results = []
    
    # Scan real malicious if exists
    if real_malicious.exists():
        print(f"[*] Scanning real malicious samples from {real_malicious}...")
        results = scan_directory(real_malicious, "MALICIOUS")
        all_results.extend(results)
        print(f"    Found {len(results)} real malicious files.")
    
    # Scan real safe if exists
    if real_safe.exists():
        print(f"[*] Scanning real safe samples from {real_safe}...")
        results = scan_directory(real_safe, "SAFE")
        all_results.extend(results)
        print(f"    Found {len(results)} real safe files.")
    
    # Scan synthetic malicious if exists
    if synthetic_malicious.exists():
        print(f"[*] Scanning synthetic malicious samples from {synthetic_malicious}...")
        results = scan_directory(synthetic_malicious, "MALICIOUS")
        all_results.extend(results)
        print(f"    Found {len(results)} synthetic malicious files.")
    
    # Scan synthetic safe if exists
    if synthetic_safe.exists():
        print(f"[*] Scanning synthetic safe samples from {synthetic_safe}...")
        results = scan_directory(synthetic_safe, "SAFE")
        all_results.extend(results)
        print(f"    Found {len(results)} synthetic safe files.")
    
    if not all_results:
        print("[!] No files found to scan.")
        return
    
    # Summary
    print("\n" + "="*70)
    print("📊 BENCHMARK SUMMARY")
    print("="*70)
    print(f"{'File':35} | {'NS':12} | {'Bandit':10} | {'Semgrep':10} | {'Expected':10} | {'Result':6}")
    print("-"*85)
    
    for r in all_results:
        status = "✅" if r["correct"] else "❌"
        print(f"{r['file'][:35]:35} | {r['neuralspace']:12} | {r['bandit']:10} | {r['semgrep']:10} | {r['expected']:10} | {status:6}")
    
    total = len(all_results)
    correct = sum(1 for r in all_results if r["correct"])
    ns_blocked = sum(1 for r in all_results if r["neuralspace"] == "BLOCKED")
    total_malicious = sum(1 for r in all_results if r["expected"] == "MALICIOUS")
    safe_allowed = sum(1 for r in all_results if r["expected"] == "SAFE" and r["neuralspace"] == "ALLOWED")
    total_safe = sum(1 for r in all_results if r["expected"] == "SAFE")
    
    print("-"*85)
    print(f"📊 SUMMARY: {correct}/{total} correct ({correct/total*100:.1f}%)")
    print(f"   Malicious Detection: {ns_blocked}/{total_malicious} ({ns_blocked/total_malicious*100:.1f}%)")
    print(f"   Safe Files Allowed: {safe_allowed}/{total_safe} ({safe_allowed/total_safe*100:.1f}%)")
    
    print("\n📋 DETAILED BREAKDOWN:")
    for r in all_results:
        status = "✅" if r["correct"] else "❌"
        print(f"  {r['file']:35} → {status} (NS: {r['neuralspace']}, Bandit: {r['bandit']}, Semgrep: {r['semgrep']})")
    
    print("="*70)

if __name__ == "__main__":
    run_benchmark_osv()