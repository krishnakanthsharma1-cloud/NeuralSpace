# neuralspace/scanner.py
import os
import shutil
from pathlib import Path
from neuralspace.engine import CovalentTreeEngine

class SecurityScanner:
    def __init__(self, target_dir, quarantine_mode="rename"):
        self.target_dir = Path(target_dir)
        self.quarantine_mode = quarantine_mode
        self.log_file = self.target_dir / "security_log.txt"
        self.engine = CovalentTreeEngine()
        
        if self.quarantine_mode == "move":
            self.quarantine_dir = self.target_dir / "_quarantine"
            if not self.quarantine_dir.exists():
                self.quarantine_dir.mkdir()

    def run_scan(self):
        print(f"\n[*] Initiating Deep Scan on: {self.target_dir}")
        print("-" * 65)

        with open(self.log_file, "a", encoding='utf-8') as log:
            log.write(f"\n--- SCAN STARTED: {self.target_dir} ---\n")

            # Scan multiple language extensions
            extensions = {'.py', '.js', '.ts', '.go', '.rs', '.cpp', '.c', '.h', '.jsx', '.tsx'}
            for file_path in self.target_dir.rglob('*'):
                if file_path.suffix in extensions:
                    self._scan_one(file_path, log)

        print("-" * 65)
        print(f"[*] Scan Complete. Taxonomy snapshot saved. Log written to {self.log_file.name}")

    def scan_file(self, file_path):
        """Scan a single file (used by the live watcher)."""
        file_path = Path(file_path)
        print(f"\n[*] Scanning dropped file: {file_path}")
        with open(self.log_file, "a", encoding='utf-8') as log:
            log.write(f"\n--- FILE DROP: {file_path} ---\n")
            self._scan_one(file_path, log)

    def _scan_one(self, file_path, log):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"[!] Error reading {file_path.name}: {e}")
            return

        try:
            file_id = str(file_path.relative_to(self.target_dir))
        except ValueError:
            file_id = file_path.name

        # --- 1. Run the engine ---
        status, s_score, l_score, node_id, trace = self.engine.process_drop_explain(content, file_id)

        # --- 2. Print the standard log ---
        log_entry = f"[{status}] {file_id} | Node:{node_id} | S:{s_score:.4f} | L:{l_score:.4f}"
        print(log_entry)
        log.write(log_entry + "\n")

        # --- 3. PRINT THE DECISION TRACE ---
        if status == "BLOCKED":
            print(f"    🔍 DECISION TRACE:")
            for line in trace:
                print(f"       {line}")
            log.write("    DECISION TRACE:\n")
            for line in trace:
                log.write(f"       {line}\n")

        # --- 4. Execute Isolation Protocol ---
        if status == "BLOCKED":
            self.isolate_threat(file_path, file_id)

    def isolate_threat(self, original_path, file_id):
        if self.quarantine_mode == "rename":
            dest_path = original_path.with_suffix(original_path.suffix + '.quarantined')
            original_path.rename(dest_path)
            print(f"    -> [QUARANTINE] Renamed to {dest_path.name}")
            
        elif self.quarantine_mode == "move":
            safe_name = file_id.replace("/", "_").replace("\\", "_") + ".quarantine"
            dest_path = self.quarantine_dir / safe_name
            shutil.move(str(original_path), str(dest_path))
            print(f"    -> [QUARANTINE] Moved to {dest_path.name}")