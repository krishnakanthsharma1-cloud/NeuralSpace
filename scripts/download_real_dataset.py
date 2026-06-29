# download_real_dataset.py
import os
import json
import requests
import zipfile
import shutil
from pathlib import Path
import subprocess

# Source: Backstabber's Knife Collection (malicious PyPI packages)
BACKSTABBER_URL = "https://github.com/cybersecsi/backstabbers-knife-collection/archive/refs/heads/main.zip"

# Known malicious package samples (as a fallback)
KNOWN_MALICIOUS = {
    "noblesse": "https://files.pythonhosted.org/packages/...",  # Example
    "colors": "https://files.pythonhosted.org/packages/...",
}

def download_backstabber():
    """Download the Backstabber's Knife Collection."""
    print("[*] Downloading Backstabber's Knife Collection...")
    try:
        response = requests.get(BACKSTABBER_URL, timeout=60)
        with open("benchmark_dataset/backstabber.zip", "wb") as f:
            f.write(response.content)
        print("[✓] Downloaded Backstabber collection.")
        return True
    except Exception as e:
        print(f"[!] Failed to download Backstabber: {e}")
        return False

def extract_malicious_samples():
    """Extract malicious Python samples from the dataset."""
    zip_path = "benchmark_dataset/backstabber.zip"
    extract_path = "benchmark_dataset/real_malicious"
    
    if not os.path.exists(zip_path):
        print("[!] Backstabber ZIP not found.")
        return
    
    os.makedirs(extract_path, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        print(f"[✓] Extracted malicious samples to {extract_path}")
    except Exception as e:
        print(f"[!] Extraction failed: {e}")

def create_safe_samples():
    """Create safe samples from popular libraries."""
    safe_samples = {
        "safe_flask.py": 'from flask import Flask\napp = Flask(__name__)\n@app.route("/")\ndef hello():\n    return "Hello World"',
        "safe_requests.py": 'import requests\nresponse = requests.get("https://api.github.com")\nprint(response.status_code)',
        "safe_django.py": 'import django\nprint(django.__version__)',
        "safe_numpy.py": 'import numpy as np\na = np.array([1,2,3])\nprint(a.mean())',
        "safe_pandas.py": 'import pandas as pd\ndf = pd.DataFrame({"a": [1,2,3]})\nprint(df)',
        "safe_scipy.py": 'import scipy\nprint(scipy.__version__)',
        "safe_plotly.py": 'import plotly\na = [1,2,3]\nprint(a)',
        "safe_selenium.py": 'from selenium import webdriver\ndriver = webdriver.Chrome()\nprint("Selenium")',
    }
    
    os.makedirs("benchmark_dataset/real_safe", exist_ok=True)
    for name, content in safe_samples.items():
        with open(f"benchmark_dataset/real_safe/{name}", "w") as f:
            f.write(content)
    print(f"[✓] Created {len(safe_samples)} safe samples.")

def main():
    os.makedirs("benchmark_dataset", exist_ok=True)
    
    # 1. Download Backstabber
    if download_backstabber():
        extract_malicious_samples()
    
    # 2. Create safe samples
    create_safe_samples()
    
    print("\n[✓] Dataset ready in ./benchmark_dataset/")
    print("   - Real malicious samples: benchmark_dataset/real_malicious/")
    print("   - Safe samples: benchmark_dataset/real_safe/")

if __name__ == "__main__":
    main()