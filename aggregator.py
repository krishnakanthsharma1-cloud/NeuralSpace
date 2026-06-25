# aggregator.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import hashlib
import json
from datetime import datetime
from typing import List, Optional

app = FastAPI(
    title="NeuralSpace Federated Intelligence",
    description="Global threat intelligence aggregator for the NeuralSpace network.",
    version="1.0.0"
)

# In-memory ledger (use Redis/PostgreSQL in production)
threat_ledger = {}

class ThreatSignature(BaseModel):
    file_hash: str
    combo_hits: List[str]
    sentinel_score: float
    logic_score: float
    node_path: str
    language: Optional[str] = "unknown"
    timestamp: str

@app.post("/report-threat")
async def report_threat(signature: ThreatSignature):
    # Generate a unique ID for this threat pattern
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
    
    return {
        "status": "recorded",
        "threat_id": threat_id,
        "total_threats": len(threat_ledger)
    }

@app.get("/global-threats")
async def get_global_threats(limit: int = 10):
    """Retrieve the top N most frequent global threat patterns."""
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
                "avg_sentinel": round(data["avg_sentinel"], 4)
            }
            for tid, data in sorted_threats
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "threats_observed": len(threat_ledger)}

# To run: uvicorn aggregator:app --host 0.0.0.0 --port 8000