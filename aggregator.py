# aggregator.py (All-in-One: Dashboard + Threat Receiver + GitHub Webhook)
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import hashlib
import hmac
import os
from datetime import datetime
from typing import List, Optional

app = FastAPI(title="NeuralSpace Federated Intelligence")

# --- In-memory ledger ---
threat_ledger = {}

# --- GitHub Webhook Secret (set this in Render Environment Variables) ---
WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "your_secret_here")

# --- Data Models ---
class ThreatSignature(BaseModel):
    file_hash: str
    combo_hits: List[str]
    sentinel_score: float
    logic_score: float
    node_path: str
    language: Optional[str] = "unknown"
    timestamp: str

# --- Threat Reporting Endpoint ---
@app.post("/report-threat")
async def report_threat(signature: ThreatSignature):
    pattern_key = f"{'-'.join(sorted(signature.combo_hits))}:{signature.node_path}"
    threat_id = hashlib.sha256(pattern_key.encode()).hexdigest()[:16]
    
    if threat_id not in threat_ledger:
        threat_ledger[threat_id] = {
            "first_seen": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "occurrences": 1,
            "pattern": signature.combo_hits,
            "node_path": signature.node_path,
            "avg_sentinel": signature.sentinel_score,
            "avg_logic": signature.logic_score,
            "languages": {signature.language}
        }
        print(f"[!] New global threat pattern detected: {threat_id}")
    else:
        entry = threat_ledger[threat_id]
        entry["occurrences"] += 1
        entry["last_seen"] = datetime.now().isoformat()
        entry["avg_sentinel"] = (entry["avg_sentinel"] + signature.sentinel_score) / 2
        entry["avg_logic"] = (entry["avg_logic"] + signature.logic_score) / 2
        if signature.language not in entry["languages"]:
            entry["languages"].add(signature.language)
    
    return {"status": "recorded", "threat_id": threat_id, "total_threats": len(threat_ledger)}

# --- Global Threats Endpoint ---
@app.get("/global-threats")
async def get_global_threats(limit: int = 10):
    sorted_threats = sorted(
        threat_ledger.items(),
        key=lambda x: x[1]["occurrences"],
        reverse=True
    )[:limit]
    return {
        "total_threats": len(threat_ledger),
        "top_threats": [
            {
                "id": tid,
                "pattern": data["pattern"],
                "occurrences": data["occurrences"],
                "languages": list(data["languages"]),
                "avg_sentinel": round(data["avg_sentinel"], 4),
                "last_seen": data["last_seen"]
            }
            for tid, data in sorted_threats
        ]
    }

# --- Health Check ---
@app.get("/health")
async def health_check():
    return {"status": "healthy", "threats_observed": len(threat_ledger)}

# --- GITHUB WEBHOOK ENDPOINT ---
def verify_signature(request_body: bytes, signature: str) -> bool:
    """Verify that the webhook is from GitHub."""
    if not signature:
        return False
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        request_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@app.post("/webhook")
async def github_webhook(request: Request):
    """Receive webhooks from GitHub."""
    # 1. Verify signature
    signature = request.headers.get("X-Hub-Signature-256", "")
    if signature.startswith("sha256="):
        signature = signature[7:]
    
    body = await request.body()
    if not verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # 2. Parse the event
    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event", "unknown")
    
    print(f"[*] Received GitHub event: {event_type}")
    
    if event_type == "ping":
        return {"status": "pong"}
    
    if event_type == "pull_request":
        action = payload.get("action")
        pr_number = payload.get("number")
        repo_name = payload.get("repository", {}).get("full_name", "unknown")
        
        print(f"[*] PR #{pr_number} in {repo_name} - Action: {action}")
        
        # TODO: In the next phase, we will clone the repo and run the scanner here.
        # For now, we just acknowledge receipt.
        return {
            "status": "received",
            "event": event_type,
            "pr": pr_number,
            "repo": repo_name
        }
    
    return {"status": "ignored", "event": event_type}

# --- DASHBOARD (HTML) ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NeuralSpace Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: #0f172a; font-family: 'Inter', sans-serif; }
        .glass { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }
    </style>
</head>
<body class="text-white min-h-screen p-8">
    <div class="max-w-6xl mx-auto">
        <div class="flex justify-between items-center mb-8">
            <div>
                <h1 class="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">🧠 NeuralSpace</h1>
                <p class="text-gray-400">Global Threat Intelligence Network</p>
            </div>
            <div class="glass px-6 py-3 rounded-2xl text-sm">
                <span class="text-green-400">●</span> <span id="status-text">Live</span>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="glass p-6 rounded-2xl">
                <div class="text-gray-400 text-sm uppercase tracking-wider">Total Threats</div>
                <div class="text-3xl font-bold" id="total-threats">0</div>
            </div>
            <div class="glass p-6 rounded-2xl">
                <div class="text-gray-400 text-sm uppercase tracking-wider">Languages Covered</div>
                <div class="text-3xl font-bold" id="total-langs">5</div>
                <div class="text-xs text-gray-500">Python, JS, TS, Go, Rust</div>
            </div>
            <div class="glass p-6 rounded-2xl">
                <div class="text-gray-400 text-sm uppercase tracking-wider">Network Status</div>
                <div class="text-3xl font-bold text-green-400" id="network-status">✅ Active</div>
            </div>
        </div>

        <div class="glass rounded-2xl overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-800">
                <h2 class="text-xl font-semibold">📊 Top Global Threats</h2>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left">
                    <thead class="bg-gray-900/50 text-xs uppercase tracking-wider text-gray-400">
                        <tr>
                            <th class="px-6 py-3">Pattern</th>
                            <th class="px-6 py-3">Languages</th>
                            <th class="px-6 py-3">Occurrences</th>
                            <th class="px-6 py-3">Avg Sentinel</th>
                            <th class="px-6 py-3">Last Seen</th>
                        </tr>
                    </thead>
                    <tbody id="threat-table-body" class="divide-y divide-gray-800">
                        <tr><td colspan="5" class="text-center py-6 text-gray-500">Loading threats...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        async function fetchThreats() {
            try {
                const response = await fetch('/global-threats');
                const data = await response.json();
                document.getElementById('total-threats').innerText = data.total_threats || 0;
                const tbody = document.getElementById('threat-table-body');
                if (data.top_threats && data.top_threats.length > 0) {
                    tbody.innerHTML = data.top_threats.map(t => `
                        <tr class="hover:bg-white/5 transition">
                            <td class="px-6 py-4 font-mono text-sm">${t.pattern.join(' + ') || 'Unknown'}</td>
                            <td class="px-6 py-4 text-sm">${t.languages.join(', ')}</td>
                            <td class="px-6 py-4 font-bold text-blue-400">${t.occurrences}</td>
                            <td class="px-6 py-4 text-sm">${t.avg_sentinel || 0}</td>
                            <td class="px-6 py-4 text-sm text-gray-400">${new Date(t.last_seen).toLocaleString()}</td>
                        </tr>
                    `).join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="5" class="text-center py-6 text-gray-500">✅ No threats recorded yet. The network is clean.</td></tr>';
                }
            } catch (e) {
                document.getElementById('threat-table-body').innerHTML = '<tr><td colspan="5" class="text-center py-6 text-red-400">⚠️ Failed to fetch threat data.</td></tr>';
            }
        }
        fetchThreats();
        setInterval(fetchThreats, 5000);
    </script>
</body>
</html>
"""

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML

# --- Run the server ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)