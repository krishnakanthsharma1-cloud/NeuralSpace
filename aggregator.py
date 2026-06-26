# aggregator.py - Full version with PR scanning and commenting
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
import json
import os
import tempfile
import subprocess
import shutil
from pathlib import Path
from github import Github

app = FastAPI(title="NeuralSpace GitHub Integration")

# --- GitHub Configuration ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

if not GITHUB_TOKEN:
    print("WARNING: GITHUB_TOKEN not set. PR commenting will not work.")

# --- In-memory ledger for dashboard ---
threat_ledger = {}

# --- Health Check ---
@app.get("/health")
async def health():
    return {"status": "healthy", "threats_observed": len(threat_ledger)}

# --- Dashboard ---
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
        <div>Last Webhook</div>
        <div class="value" id="last">Waiting...</div>
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

# --- REPORT THREAT ENDPOINT (for CLI) ---
@app.post("/report-threat")
async def report_threat(request: Request):
    try:
        payload = await request.json()
        pattern_key = str(payload.get("combo_hits", []))
        threat_id = hashlib.md5(pattern_key.encode()).hexdigest()[:8]
        if threat_id not in threat_ledger:
            threat_ledger[threat_id] = {
                "pattern": pattern_key,
                "count": 0,
                "first_seen": datetime.now().isoformat()
            }
        threat_ledger[threat_id]["count"] += 1
        return {"status": "recorded"}
    except:
        return {"status": "error"}

# --- MAIN WEBHOOK ENDPOINT ---
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
            repo_clone_url = payload.get("repository", {}).get("clone_url", "")
            pr_head_ref = payload.get("pull_request", {}).get("head", {}).get("ref", "main")
            pr_head_repo = payload.get("pull_request", {}).get("head", {}).get("repo", {}).get("clone_url", "")
            
            print(f"[*] PR #{pr_number} in {repo_name} - Action: {action}")
            print(f"[*] Branch: {pr_head_ref}")
            
            # Only scan on opened, synchronize, or reopened events
            if action in ["opened", "synchronize", "reopened"]:
                # Clone and scan
                result = await scan_pr(repo_name, pr_number, pr_head_ref, pr_head_repo)
                return {"status": "scan_complete", "result": result}
            else:
                return {"status": "ignored", "reason": f"action {action} not scanned"}
                
        except Exception as e:
            print(f"[!] Error processing webhook: {e}")
            return {"status": "error", "detail": str(e)}
    
    return {"status": "ignored", "event": event_type}

# --- SCAN PR FUNCTION ---
async def scan_pr(repo_name, pr_number, branch_name, clone_url):
    """Clone the PR branch, scan it, and post a comment."""
    
    if not GITHUB_TOKEN:
        print("[!] No GitHub token, skipping scan")
        return "No token provided"
    
    try:
        # Initialize GitHub client
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        # Create temporary directory for cloning
        with tempfile.TemporaryDirectory() as tmpdir:
            clone_path = Path(tmpdir)
            
            # Clone the PR branch
            repo_url = clone_url.replace("https://", f"https://x-access-token:{GITHUB_TOKEN}@")
            print(f"[*] Cloning {repo_url} branch {branch_name}")
            
            result = subprocess.run(
                ["git", "clone", "--branch", branch_name, "--depth", "1", repo_url, str(clone_path)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"[!] Clone failed: {result.stderr}")
                return "Clone failed"
            
            print(f"[*] Clone successful. Scanning {clone_path}")
            
            # Determine which files changed in this PR
            changed_files = []
            for file in pr.get_files():
                changed_files.append(file.filename)
            
            print(f"[*] Changed files: {changed_files}")
            
            # Run the scanner on the cloned repository
            # We need to import the scanner from the neuralspace package
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            from neuralspace.scanner import SecurityScanner
            from neuralspace.engine import CovalentTreeEngine
            
            engine = CovalentTreeEngine()
            results = []
            
            # Scan each changed file
            for file_path in changed_files:
                full_path = clone_path / file_path
                if not full_path.exists():
                    continue
                    
                # Only scan if it's a code file
                ext = full_path.suffix.lower()
                if ext not in ['.py', '.js', '.ts', '.go', '.rs', '.jsx', '.tsx']:
                    continue
                
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()
                    
                    status, s_score, l_score, node_id, trace = engine.process_drop_explain(code, file_path.name)
                    
                    results.append({
                        "file": file_path,
                        "status": status,
                        "sentinel": s_score,
                        "logic": l_score,
                        "trace": trace[:3]  # Limit trace to top 3 lines
                    })
                    
                    print(f"[*] {file_path}: {status} (S={s_score:.4f}, L={l_score:.4f})")
                    
                except Exception as e:
                    print(f"[!] Error scanning {file_path}: {e}")
                    results.append({"file": file_path, "status": "ERROR", "error": str(e)})
            
            # Build comment
            comment_lines = []
            comment_lines.append(f"## 🧠 NeuralSpace Scan Results for PR #{pr_number}\n")
            
            threat_count = sum(1 for r in results if r.get("status") == "BLOCKED")
            
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
            
            # Post comment
            comment_text = "\n".join(comment_lines)
            print(f"[*] Posting comment to PR #{pr_number}")
            
            # Check if NeuralSpace already commented
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

if __name__ == "__main__":
    import uvicorn
    import hashlib
    from datetime import datetime
    uvicorn.run(app, host="0.0.0.0", port=10000)