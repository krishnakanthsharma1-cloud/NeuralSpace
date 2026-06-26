# aggregator.py - Simplified with error handling
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import os
import json
import hashlib
from datetime import datetime

app = FastAPI(title="NeuralSpace Webhook")

# --- In-memory ledger for dashboard ---
threat_ledger = {}

# --- Health Check ---
@app.get("/health")
async def health():
    return {"status": "healthy", "threats_observed": len(threat_ledger)}

# --- Simple Dashboard ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>NeuralSpace Dashboard</title>
    <style>
        body { background: #0f172a; color: white; font-family: Arial; padding: 20px; }
        .card { background: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px; margin: 10px 0; }
        .value { font-size: 2rem; font-weight: bold; color: #60a5fa; }
    </style>
</head>
<body>
    <h1>🧠 NeuralSpace</h1>
    <div class="card">
        <div>Total Threats</div>
        <div class="value" id="total">0</div>
    </div>
    <script>
        async function update() {
            const r = await fetch('/health');
            const data = await r.json();
            document.getElementById('total').textContent = data.threats_observed;
        }
        update();
        setInterval(update, 5000);
    </script>
</body>
</html>
"""

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML

# --- Report Threat ---
@app.post("/report-threat")
async def report_threat(request: Request):
    try:
        payload = await request.json()
        pattern = str(payload.get("combo_hits", []))
        threat_id = hashlib.md5(pattern.encode()).hexdigest()[:8]
        if threat_id not in threat_ledger:
            threat_ledger[threat_id] = {"pattern": pattern, "count": 0}
        threat_ledger[threat_id]["count"] += 1
        return {"status": "recorded"}
    except:
        return {"status": "error"}

# --- Webhook Endpoint ---
@app.post("/webhook")
async def webhook(request: Request):
    body = await request.body()
    headers = dict(request.headers)
    event_type = headers.get("x-github-event", "unknown")
    
    print(f"[*] Webhook received: {event_type}")
    
    if event_type == "ping":
        return {"status": "pong"}
    
    if event_type == "pull_request":
        try:
            payload = await request.json()
            action = payload.get("action", "")
            pr_number = payload.get("number", 0)
            repo_name = payload.get("repository", {}).get("full_name", "unknown")
            branch = payload.get("pull_request", {}).get("head", {}).get("ref", "unknown")
            
            print(f"[*] PR #{pr_number} in {repo_name}")
            print(f"[*] Action: {action}, Branch: {branch}")
            
            # Try to run the scanner, but don't crash if it fails
            try:
                result = await scan_pr(payload)
                return {"status": "scanned", "result": result}
            except Exception as e:
                print(f"[!] Scanner error: {e}")
                return {"status": "webhook_received", "scanner": "failed", "error": str(e)}
                
        except Exception as e:
            print(f"[!] Error: {e}")
            return {"status": "error", "detail": str(e)}
    
    return {"status": "ignored", "event": event_type}

# --- Scanner Function ---
async def scan_pr(payload):
    """Try to import the scanner and run it."""
    try:
        # Try to import the scanner
        import sys
        import subprocess
        import tempfile
        from pathlib import Path
        
        print("[*] Attempting to import neuralspace.scanner...")
        
        # Add the current directory to Python path
        sys.path.insert(0, os.getcwd())
        
        from neuralspace.engine import CovalentTreeEngine
        
        pr_number = payload.get("number", 0)
        repo_name = payload.get("repository", {}).get("full_name", "unknown")
        branch = payload.get("pull_request", {}).get("head", {}).get("ref", "unknown")
        clone_url = payload.get("pull_request", {}).get("head", {}).get("repo", {}).get("clone_url", "")
        
        engine = CovalentTreeEngine()
        
        print(f"[*] Scanner loaded successfully. Would scan PR #{pr_number}")
        
        return {
            "status": "scanner_ready",
            "pr": pr_number,
            "repo": repo_name,
            "branch": branch,
            "message": "Scanner loaded successfully"
        }
        
    except ImportError as e:
        print(f"[!] ImportError: {e}")
        return {
            "status": "scanner_unavailable",
            "error": str(e),
            "message": "Scanner module not loaded. Check if neuralspace is installed."
        }
    except Exception as e:
        print(f"[!] Unexpected error: {e}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)