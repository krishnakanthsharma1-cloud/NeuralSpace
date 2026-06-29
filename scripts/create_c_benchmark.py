# scripts/create_c_benchmark.py
import os
from pathlib import Path

def create_c_benchmark():
    os.makedirs("benchmark_dataset/malicious", exist_ok=True)
    os.makedirs("benchmark_dataset/safe", exist_ok=True)

    # C malicious samples
    c_malicious = [
        ('c_mal_1.c', '#include <stdlib.h>\nint main() { system("rm -rf /"); return 0; }'),
        ('c_mal_2.c', '#include <stdio.h>\nint main() { popen("ls", "r"); return 0; }'),
    ]
    # C safe samples
    c_safe = [
        ('c_safe_1.c', '#include <stdio.h>\nint main() { printf("Hello"); return 0; }'),
        ('c_safe_2.c', '#include <math.h>\nint main() { double x = sqrt(16); return 0; }'),
    ]

    # C++ malicious samples
    cpp_malicious = [
        ('cpp_mal_1.cpp', '#include <cstdlib>\nint main() { std::system("rm -rf /"); return 0; }'),
        ('cpp_mal_2.cpp', '#include <unistd.h>\nint main() { execl("/bin/sh", "sh", "-c", "echo malicious", NULL); return 0; }'),
    ]
    # C++ safe samples
    cpp_safe = [
        ('cpp_safe_1.cpp', '#include <iostream>\nint main() { std::cout << "Hello"; return 0; }'),
        ('cpp_safe_2.cpp', '#include <vector>\nint main() { std::vector<int> v = {1,2,3}; return 0; }'),
    ]

    for name, content in c_malicious:
        with open(f"benchmark_dataset/malicious/{name}", "w") as f:
            f.write(content)
    for name, content in c_safe:
        with open(f"benchmark_dataset/safe/{name}", "w") as f:
            f.write(content)
    for name, content in cpp_malicious:
        with open(f"benchmark_dataset/malicious/{name}", "w") as f:
            f.write(content)
    for name, content in cpp_safe:
        with open(f"benchmark_dataset/safe/{name}", "w") as f:
            f.write(content)

    print("[✓] Added C/C++ samples to benchmark_dataset/")
    print(f"   - {len(c_malicious) + len(cpp_malicious)} malicious C/C++ files")
    print(f"   - {len(c_safe) + len(cpp_safe)} safe C/C++ files")

if __name__ == "__main__":
    create_c_benchmark()