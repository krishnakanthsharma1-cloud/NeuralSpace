# aggregator.py - Full version with Zero-Trust Security Mesh + God User
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from neuralspace.trust_layer import TrustNode
import os
import json
import hashlib
import subprocess
import tempfile
import time
from pathlib import Path
from datetime import datetime
from github import Github

app = FastAPI(title="NeuralSpace GitHub Integration")

# --- Configuration ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "")

# --- Initialize Trust Node ---
TRUST_NODE = TrustNode()
print(f"[*] Trust Node initialized. Node ID: {TRUST_NODE.node_id}")

# --- In-memory ledger ---
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
    <div class="card">
        <div>Trust Node</div>
        <div class="value" id="trust">Loading...</div>
    </div>
    <script>
        async function update() {
            const r = await fetch('/health');
            const data = await r.json();
            document.getElementById('total').textContent = data.threats_observed;
        }
        async function updateTrust() {
            try {
                const r = await fetch('/whisper', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: 'health'})
                });
                const data = await r.json();
                if (data.trust_node) {
                    document.getElementById('trust').textContent = data.trust_node.substring(0, 8) + '...';
                }
            } catch(e) {}
        }
        update();
        updateTrust();
        setInterval(update, 5000);
    </script>
</body>
</html>
"""

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML

# --- Report Threat (Trusted) ---
@app.post("/report-threat")
async def report_threat(request: Request):
    """Receive and verify signed threat reports."""
    try:
        payload = await request.json()
        
        # Check if the report is signed
        if "signature" not in payload or "node_id" not in payload:
            return {"status": "error", "message": "Unsigned report rejected"}
        
        # Verify the signature
        if not TRUST_NODE.verify_report(payload):
            # Decrease trust for this node
            TRUST_NODE.update_trust(payload["node_id"], False)
            return {"status": "rejected", "message": "Invalid signature"}
        
        # Extract the actual report
        report = payload["report"]
        node_id = payload["node_id"]
        
        # Check trust score
        trust_score = TRUST_NODE.get_trust_score(node_id)
        if trust_score < 0.3:
            return {"status": "rejected", "message": f"Low trust score: {trust_score:.2f}"}
        
        # Process the threat
        pattern_key = str(report.get("combo_hits", []))
        threat_id = hashlib.md5(pattern_key.encode()).hexdigest()[:8]
        
        if threat_id not in threat_ledger:
            threat_ledger[threat_id] = {
                "pattern": pattern_key,
                "count": 0,
                "first_seen": datetime.now().isoformat(),
                "node_id": node_id,
                "trust_score": trust_score
            }
        
        threat_ledger[threat_id]["count"] += 1
        
        # Update trust (verified report)
        TRUST_NODE.update_trust(node_id, True)
        
        print(f"[*] Threat from trusted node {node_id[:8]} recorded. Trust: {trust_score:.2f}")
        
        return {
            "status": "recorded",
            "threat_id": threat_id,
            "trust_score": trust_score,
            "total_threats": len(threat_ledger)
        }
        
    except Exception as e:
        print(f"[!] Error: {e}")
        return {"status": "error", "detail": str(e)}

# --- Main Webhook ---
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
            clone_url = payload.get("repository", {}).get("clone_url", "")
            pr_head_ref = payload.get("pull_request", {}).get("head", {}).get("ref", "main")
            pr_head_repo = payload.get("pull_request", {}).get("head", {}).get("repo", {}).get("clone_url", "")
            
            print(f"[*] PR #{pr_number} in {repo_name}")
            print(f"[*] Action: {action}, Branch: {pr_head_ref}")
            
            # Only scan on opened, synchronize, or reopened
            if action in ["opened", "synchronize", "reopened"]:
                result = await scan_pr(payload)
                return {"status": "scanned", "result": result}
            else:
                return {"status": "ignored", "reason": f"action {action}"}
                
        except Exception as e:
            print(f"[!] Error: {e}")
            return {"status": "error", "detail": str(e)}
    
    return {"status": "ignored", "event": event_type}

# --- Scan PR Function ---
async def scan_pr(payload):
    """Clone the PR branch, scan it, and post a comment."""
    
    if not GITHUB_TOKEN:
        print("[!] No GitHub token, skipping scan")
        return "No token provided"
    
    try:
        g = Github(GITHUB_TOKEN)
        repo_name = payload.get("repository", {}).get("full_name", "unknown")
        repo = g.get_repo(repo_name)
        pr_number = payload.get("number", 0)
        pr = repo.get_pull(pr_number)
        branch = payload.get("pull_request", {}).get("head", {}).get("ref", "main")
        clone_url = payload.get("pull_request", {}).get("head", {}).get("repo", {}).get("clone_url", "")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            clone_path = Path(tmpdir)
            repo_url = clone_url.replace("https://", f"https://x-access-token:{GITHUB_TOKEN}@")
            
            print(f"[*] Cloning branch {branch}")
            result = subprocess.run(
                ["git", "clone", "--branch", branch, "--depth", "1", repo_url, str(clone_path)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"[!] Clone failed: {result.stderr}")
                return "Clone failed"
            
            print("[*] Clone successful")
            
            # Get changed files
            changed_files = [f.filename for f in pr.get_files()]
            print(f"[*] Changed files: {changed_files}")
            
            # Import scanner
            import sys
            sys.path.insert(0, os.getcwd())
            from neuralspace.engine import CovalentTreeEngine
            
            engine = CovalentTreeEngine()
            results = []
            threat_count = 0
            
            for file_path in changed_files:
                full_path = clone_path / file_path
                if not full_path.exists():
                    continue
                
                ext = full_path.suffix.lower()
                if ext not in ['.py', '.js', '.ts', '.go', '.rs', '.jsx', '.tsx']:
                    continue
                
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()
                    
                    status, s_score, l_score, node_id, trace = engine.process_drop_explain(code, file_path)
                    
                    if status == "BLOCKED":
                        threat_count += 1
                    
                    results.append({
                        "file": file_path,
                        "status": status,
                        "sentinel": round(s_score, 4),
                        "logic": round(l_score, 4),
                        "trace": trace[:3] if trace else []
                    })
                    
                    print(f"[*] {file_path}: {status}")
                    
                except Exception as e:
                    print(f"[!] Error scanning {file_path}: {e}")
                    results.append({"file": file_path, "status": "ERROR", "error": str(e)})
            
            # Build comment
            comment_lines = []
            comment_lines.append(f"## 🧠 NeuralSpace Scan Results for PR #{pr_number}\n")
            
            if threat_count == 0:
                comment_lines.append("✅ **No threats detected** in this pull request.\n")
            else:
                comment_lines.append(f"⚠️ **{threat_count} threat(s) detected** in this pull request:\n")
                for r in results:
                    if r.get("status") == "BLOCKED":
                        comment_lines.append(f"- `{r['file']}` → 🔴 **BLOCKED** (S={r.get('sentinel', 0):.4f})")
                        for trace_line in r.get("trace", []):
                            comment_lines.append(f"  - {trace_line}")
                        comment_lines.append("")
            
            if threat_count == 0:
                comment_lines.append("---")
                comment_lines.append("✅ This PR is safe to merge. NeuralSpace found no malicious patterns.")
            
            comment_text = "\n".join(comment_lines)
            
            # Post comment
            print(f"[*] Posting comment to PR #{pr_number}")
            existing_comments = pr.get_issue_comments()
            for comment in existing_comments:
                if comment.user.login == "github-actions[bot]":
                    comment.edit(comment_text)
                    print("[*] Updated existing comment")
                    break
            else:
                pr.create_issue_comment(comment_text)
                print("[*] Created new comment")
            
            return f"Scanned {len(results)} files, {threat_count} threats found"
            
    except Exception as e:
        print(f"[!] Error in scan_pr: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}"

# --- GOD USER: Natural Language Commands ---
@app.post("/whisper")
async def whisper(request: Request):
    """
    The God User endpoint. Accept natural language commands to shape the universe.
    
    Commands:
    - "health" or "status" → Show universe health
    - "spawn branch" → Create a new branch
    - "show threats" → Show recent threats
    - "evolve" → Trigger an evolution cycle
    """
    try:
        payload = await request.json()
        command = payload.get("command", "").lower()
        
        print(f"[*] God User command: {command}")
        
        # --- Command: Health ---
        if "health" in command or "status" in command:
            return {
                "status": "executed",
                "action": "health",
                "total_threats": len(threat_ledger),
                "trust_node": TRUST_NODE.node_id,
                "trust_score": TRUST_NODE.trust_score,
                "timestamp": datetime.now().isoformat()
            }
        
        # --- Command: Spawn Branch ---
        elif "spawn" in command and "branch" in command:
            new_id = f"0x{int(time.time()) % 10000:04X}"
            print(f"[*] God User: Spawning new branch {new_id}")
            return {
                "status": "executed",
                "action": "spawn_branch",
                "branch_id": new_id,
                "message": f"🌱 Spawned new branch {new_id}"
            }
        
        # --- Command: Show Threats ---
        elif "threat" in command and ("show" in command or "list" in command or "recent" in command):
            threats = list(threat_ledger.values())[-5:]
            return {
                "status": "executed",
                "action": "show_threats",
                "threats": threats,
                "total_threats": len(threat_ledger),
                "count": len(threats)
            }
        
        # --- Command: Evolve ---
        elif "evolve" in command:
            return {
                "status": "executed",
                "action": "evolve",
                "message": "🧬 Evolution cycle triggered. The universe is adapting."
            }
        
        # --- Unknown Command ---
        else:
            return {
                "status": "unknown",
                "message": "Command not recognized. Try: 'health', 'spawn branch', 'show threats', or 'evolve'",
                "received": command
            }
            
    except Exception as e:
        print(f"[!] Error: {e}")
        return {"status": "error", "detail": str(e)}

# --- Root endpoint ---
@app.get("/")
async def root():
    return {
        "message": "🧠 NeuralSpace Universe is alive!",
        "endpoints": {
            "health": "/health",
            "dashboard": "/dashboard",
            "webhook": "/webhook (POST)",
            "report-threat": "/report-threat (POST)",
            "whisper": "/whisper (POST) - God User commands"
        },
        "version": "3.0.0",
        "features": [
            "Zero-Trust Security Mesh",
            "Autonomous Evolution (Anticipatory Fracturing)",
            "Emergent Intelligence (Hive Mind)",
            "Human-AI Symbiosis (God User)"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)