# watcher.py
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from neuralspace.scanner import SecurityScanner
from filelock import FileLock

# Use a global lock file to prevent simultaneous writes
LOCK_PATH = "neuralspace.lock"

class DropHandler(FileSystemEventHandler):
    def __init__(self, quarantine_mode="rename"):
        super().__init__()
        self.quarantine_mode = quarantine_mode

    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".py"):
            return

        src_path = Path(event.src_path)
        print(f"[*] New file detected: {src_path}")

        # Acquire lock before scanning to prevent snapshot corruption
        with FileLock(LOCK_PATH):
            scanner = SecurityScanner(src_path.parent, quarantine_mode=self.quarantine_mode)
            scanner.scan_file(src_path)

def run_watcher(target_dir="./test_codebase", quarantine_mode="rename"):
    Path(target_dir).mkdir(exist_ok=True)
    observer = Observer()
    observer.schedule(DropHandler(quarantine_mode), target_dir, recursive=True)
    observer.start()
    print(f"[*] NeuralSpace is watching {target_dir} for new .py files...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    run_watcher()