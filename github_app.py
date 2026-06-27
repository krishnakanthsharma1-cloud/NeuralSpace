# github_app.py
from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib
import os
import json
from neuralspace.scanner import SecurityScanner
from neuralspace.tokenizer import code_to_512vec
import tempfile
import shutil
from pathlib import Path

app = FastAPI(title="NeuralSpace GitHub App")

# Your GitHub App secret (set in GitHub App settings)
WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "your_secret_here")

def verify_signature(request_body, signature):
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
async def handle_webhook(request: Request):
    # Verify the request is from GitHub
    signature = request.headers.get("X-Hub-Signature-256")
    if signature:
        signature = signature.replace("sha256=", "")
    
    body = await request.body()
    if not verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event")
    
    if event_type == "pull_request":
        # Get the code from the PR
        pr_url = payload["pull_request"]["url"]
        # Clone the repo and scan the changes
        # This is where you'd integrate with GitHub's API to fetch the PR diff
        return {"status": "PR received"}
    
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)