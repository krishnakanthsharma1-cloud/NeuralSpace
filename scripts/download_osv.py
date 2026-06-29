# download_osv.py
import json
import os
import requests
from pathlib import Path

def download_osv_malicious():
    """Download real malicious package data from OSV."""
    print("[*] Downloading OSV malicious packages feed...")
    
    # OSV malicious packages feed URL
    url = "https://osv-vulnerabilities.storage.googleapis.com/malicious.json"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"[*] Downloaded {len(data)} entries from OSV.")
            return data
        else:
            print(f"[!] Failed to download OSV data: Status {response.status_code}")
            return None
    except Exception as e:
        print(f"[!] Error downloading OSV data: {e}")
        return None

def extract_package_urls(osv_data):
    """Extract package URLs from OSV data."""
    urls = []
    for entry in osv_data:
        for affected in entry.get("affected", []):
            for pkg in affected.get("package", []):
                if pkg.get("purl"):
                    urls.append(pkg["purl"])
    return urls

def main():
    osv_data = download_osv_malicious()
    if not osv_data:
        print("[!] Could not download OSV data. Using synthetic dataset as fallback.")
        # Run the synthetic generator as fallback
        os.system("python scripts/download_dataset.py")
        return
    
    # Extract URLs
    urls = extract_package_urls(osv_data)
    print(f"[*] Extracted {len(urls)} package URLs.")
    
    # Save the raw data for reference
    with open("benchmark_dataset/osv_raw.json", "w") as f:
        json.dump(osv_data, f, indent=2)
    
    print("[✓] OSV data saved to benchmark_dataset/osv_raw.json")
    print("[*] Note: For a complete benchmark, download the actual package files.")
    print("[*] For now, we will use the synthetic dataset + OSV metadata.")

if __name__ == "__main__":
    main()