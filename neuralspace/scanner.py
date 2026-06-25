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

        with open(self.log_file, "a") as log:
            log.write(f"\n--- SCAN STARTED: {self.target_dir} ---\n")

            for file_path in self.target_dir.rglob('*.py'):
                # Ignore already quarantined files and the quarantine directory
                if file_path.suffix == '.quarantined' or "_quarantine" in file_path.parts:
                    continue
                self._scan_one(file_path, log)

        print("-" * 65)
        print(f"[*] Scan Complete. Taxonomy snapshot saved. Log written to {self.log_file.name}")

    def scan_file(self, file_path):
        """Scan a single file (used by the live watcher so a file drop
        doesn't trigger a full re-scan of the entire directory)."""
        file_path = Path(file_path)
        print(f"\n[*] Scanning dropped file: {file_path}")
        with open(self.log_file, "a") as log:
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

        # Feed the fractal engine
        status, s_score, l_score, node_id = self.engine.process_drop(content, file_id)

        log_entry = f"[{status}] {file_id} | Node:{node_id} | S:{s_score:.4f} | L:{l_score:.4f}"
        print(log_entry)
        log.write(log_entry + "\n")

        # Execute Isolation Protocol
        if status == "BLOCKED":
            self.isolate_threat(file_path, file_id)

    def isolate_threat(self, original_path, file_id):
        if self.quarantine_mode == "rename":
            # Safest for version control: append .quarantined
            dest_path = original_path.with_suffix('.py.quarantined')
            original_path.rename(dest_path)
            print(f"    -> [QUARANTINE] Renamed to {dest_path.name}")
            
        elif self.quarantine_mode == "move":
            # Moves to isolated folder
            safe_name = file_id.replace("/", "_").replace("\\", "_") + ".quarantine"
            dest_path = self.quarantine_dir / safe_name
            shutil.move(str(original_path), str(dest_path))
            print(f"    -> [QUARANTINE] Moved to {dest_path.name}")