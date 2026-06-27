# aggregator.py - Full version with Zero-Trust Security Mesh + Ollama Intent Parsing (Fixed Timeout)
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from neuralspace.trust_layer import TrustNode
import os
import json
import hashlib
import subprocess
import tempfile
import time
import requests
from pathlib import Path
from datetime import datetime
from github import Github

app = FastAPI(title="NeuralSpace GitHub Integration")

# --- Configuration ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "phi3:mini")

# --- Initialize Trust Node ---
TRUST_NODE = TrustNode()
print(f"[*] Trust Node initialized. Node ID: {TRUST_NODE.node_id}")

# --- In-memory ledger ---
threat_ledger = {}

# --- Federated Learning Storage ---
global_model_weights = {}
global_model_version = 0
federated_updates = []

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
        
        if "signature" not in payload or "node_id" not in payload:
            return {"status": "error", "message": "Unsigned report rejected"}
        
        if not TRUST_NODE.verify_report(payload):
            return {"status": "rejected", "message": "Invalid signature"}
        
        report = payload["report"]
        node_id = payload["node_id"]
        
        trust_score = TRUST_NODE.get_trust_score(node_id)
        if trust_score < 0.3:
            return {"status": "rejected", "message": f"Low trust score: {trust_score:.2f}"}
        
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
            
            changed_files = [f.filename for f in pr.get_files()]
            print(f"[*] Changed files: {changed_files}")
            
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

# =====================================================================
# 🧠 OLLAMA INTENT PARSER (Natural Language Understanding)
# =====================================================================

def parse_command_with_ollama(command: str):
    """
    Send the user's command to Ollama for intent parsing.
    Returns a dict with 'action' and 'target'.
    """
    system_prompt = (
        "You are a command parser for an AI security universe. "
        "Extract the primary action and target from the following user command. "
        "Valid actions: HEALTH, SPAWN_BRANCH, SHOW_THREATS, EVOLVE, SHOW_TREE. "
        "Return ONLY valid JSON in this exact format: {\"action\": \"ACTION_NAME\", \"target\": \"target_text\"}. "
        "If the command is unclear, set action to 'UNKNOWN'."
    )
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"{system_prompt}\n\nUser command: {command}\n\nJSON response:",
        "stream": False
    }
    
    try:
        # Increased timeout to 30 seconds for LLM inference
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            raw_response = result.get("response", "")
            print(f"[*] Ollama raw response: {raw_response}")
            
            # Try to extract JSON from the response
            try:
                start = raw_response.find('{')
                end = raw_response.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = raw_response[start:end]
                    parsed = json.loads(json_str)
                    if "action" in parsed:
                        return parsed
            except json.JSONDecodeError:
                pass
            
            # Fallback: extract action words from the raw response
            text = raw_response.lower()
            if "health" in text or "status" in text:
                return {"action": "HEALTH", "target": ""}
            elif "spawn" in text and "branch" in text:
                return {"action": "SPAWN_BRANCH", "target": ""}
            elif "threat" in text:
                return {"action": "SHOW_THREATS", "target": ""}
            elif "evolve" in text:
                return {"action": "EVOLVE", "target": ""}
            elif "tree" in text or "topology" in text:
                return {"action": "SHOW_TREE", "target": ""}
        
    except requests.exceptions.Timeout:
        print("[!] Ollama timeout (30s). Falling back to string matching.")
    except Exception as e:
        print(f"[!] Ollama error: {e}")
    
    # Fallback: use simple string matching
    return fallback_parse(command)

def fallback_parse(command: str):
    """Fallback parser if Ollama is unavailable."""
    command_lower = command.lower()
    if "health" in command_lower or "status" in command_lower:
        return {"action": "HEALTH", "target": ""}
    elif "spawn" in command_lower and "branch" in command_lower:
        return {"action": "SPAWN_BRANCH", "target": ""}
    elif "threat" in command_lower and ("show" in command_lower or "list" in command_lower):
        return {"action": "SHOW_THREATS", "target": ""}
    elif "evolve" in command_lower:
        return {"action": "EVOLVE", "target": ""}
    elif "tree" in command_lower or "topology" in command_lower:
        return {"action": "SHOW_TREE", "target": ""}
    else:
        return {"action": "UNKNOWN", "target": command_lower}

# =====================================================================
# 🗣️ GOD USER: Natural Language Commands (Using Ollama)
# =====================================================================

@app.post("/whisper")
async def whisper(request: Request):
    """
    The God User endpoint. Accept natural language commands.
    Uses Ollama for real intent parsing.
    """
    try:
        payload = await request.json()
        command = payload.get("command", "").strip()
        
        print(f"[*] God User command: {command}")
        
        # Parse the command using Ollama
        parsed = parse_command_with_ollama(command)
        action = parsed.get("action", "UNKNOWN")
        target = parsed.get("target", "")
        
        print(f"[*] Parsed intent: {action} (Target: {target})")
        
        # --- Execute the action ---
        if action == "HEALTH":
            return {
                "status": "executed",
                "action": "health",
                "total_threats": len(threat_ledger),
                "trust_node": TRUST_NODE.node_id,
                "trust_score": TRUST_NODE.trust_score,
                "timestamp": datetime.now().isoformat(),
                "parsed_from": command
            }
        
        elif action == "SPAWN_BRANCH":
            import sys
            from neuralspace.engine import FractalNode, quantize_int8, CovalentTreeEngine
            
            new_id = f"0x{int(time.time()) % 10000:04X}"
            engine = CovalentTreeEngine()
            root_node = engine.nodes[engine.root_id]
            
            new_node = FractalNode(
                node_id=new_id,
                parent_id=root_node.id,
                logic_seed=engine.logic_seed + len(engine.nodes),
                sent_seed=engine.sentinel_seed + len(engine.nodes),
                q_latent=quantize_int8([0.0] * 512),
                depth=1
            )
            
            engine.nodes[new_id] = new_node
            root_node.children.append(new_id)
            engine.save_snapshot()
            
            print(f"[*] God User: Spawned new branch {new_id}")
            return {
                "status": "executed",
                "action": "spawn_branch",
                "branch_id": new_id,
                "message": f"🌱 Spawned new branch {new_id}",
                "parsed_from": command
            }
        
        elif action == "SHOW_THREATS":
            threats = list(threat_ledger.values())[-5:]
            return {
                "status": "executed",
                "action": "show_threats",
                "threats": threats,
                "total_threats": len(threat_ledger),
                "count": len(threats),
                "parsed_from": command
            }
        
        elif action == "EVOLVE":
            import sys
            from neuralspace.engine import FractalNode, quantize_int8, CovalentTreeEngine
            
            engine = CovalentTreeEngine()
            new_id = f"0x{int(time.time()) % 10000:04X}"
            root_node = engine.nodes[engine.root_id]
            
            new_node = FractalNode(
                node_id=new_id,
                parent_id=root_node.id,
                logic_seed=engine.logic_seed + len(engine.nodes) + 100,
                sent_seed=engine.sentinel_seed + len(engine.nodes) + 100,
                q_latent=quantize_int8([0.0] * 512),
                depth=1
            )
            
            engine.nodes[new_id] = new_node
            root_node.children.append(new_id)
            engine.save_snapshot()
            
            return {
                "status": "executed",
                "action": "evolve",
                "message": f"🧬 Evolution cycle triggered. New branch {new_id} spawned.",
                "parsed_from": command
            }
        
        elif action == "SHOW_TREE":
            import sys
            from neuralspace.engine import CovalentTreeEngine
            engine = CovalentTreeEngine()
            tree_structure = {
                "nodes": len(engine.nodes),
                "root": engine.root_id,
                "children": {
                    node_id: node.children 
                    for node_id, node in engine.nodes.items()
                }
            }
            return {
                "status": "executed",
                "action": "show_tree",
                "tree": tree_structure,
                "parsed_from": command
            }
        
        else:
            return {
                "status": "unknown",
                "message": "Command not recognized. Try: 'health', 'spawn branch', 'show threats', 'evolve', or 'show tree'",
                "received": command,
                "parsed": parsed
            }
            
    except Exception as e:
        print(f"[!] Error: {e}")
        return {"status": "error", "detail": str(e)}

# =====================================================================
# 🌐 FEDERATED LEARNING ENDPOINTS
# =====================================================================

@app.post("/federated/update")
async def federated_update(request: Request):
    """Receive a weight update from a node."""
    global global_model_version
    
    try:
        payload = await request.json()
        node_id = payload.get("node_id", "unknown")
        delta = payload.get("delta", {})
        model_version = payload.get("model_version", 0)
        
        federated_updates.append({
            "node_id": node_id,
            "timestamp": time.time(),
            "delta": delta,
            "model_version": model_version
        })
        
        print(f"[*] Federated update from node {node_id[:8]}")
        
        # If we have enough updates, aggregate them
        if len(federated_updates) >= 3:
            result = aggregate_updates()
            if result:
                global_model_weights = result["weights"]
                global_model_version += 1
                print(f"[*] Global model version {global_model_version} updated!")
                federated_updates.clear()
        
        return {
            "status": "received",
            "new_version": global_model_version
        }
        
    except Exception as e:
        print(f"[!] Federated update error: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/federated/global")
async def get_global_model():
    """Retrieve the latest global model weights."""
    return {
        "version": global_model_version,
        "weights": global_model_weights,
        "total_updates": len(federated_updates)
    }

def aggregate_updates():
    """Aggregate weight updates using FedAvg."""
    if not federated_updates:
        return None
    
    try:
        import numpy as np
        all_deltas = [u["delta"] for u in federated_updates]
        aggregated = {}
        for delta in all_deltas:
            for name, values in delta.items():
                if name not in aggregated:
                    aggregated[name] = []
                aggregated[name].append(values)
        
        result = {}
        for name, values_list in aggregated.items():
            avg = np.mean(values_list, axis=0)
            result[name] = avg.tolist()
        
        return {
            "weights": result,
            "num_nodes": len(federated_updates)
        }
        
    except Exception as e:
        print(f"[!] Aggregation failed: {e}")
        return None

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
            "whisper": "/whisper (POST) - God User commands",
            "federated/update": "/federated/update (POST)",
            "federated/global": "/federated/global (GET)"
        },
        "version": "4.0.0",
        "features": [
            "Zero-Trust Security Mesh (RSA + PKI)",
            "Autonomous Evolution (Anticipatory Fracturing)",
            "Emergent Intelligence (Hive Mind)",
            "Human-AI Symbiosis (God User)",
            "Federated Learning (FedAvg)"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)