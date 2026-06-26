# aggregator.py - Minimal version for testing webhook
from fastapi import FastAPI, Request
import json

app = FastAPI(title="NeuralSpace Webhook Test")

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/webhook")
async def webhook(request: Request):
    # Get the raw body
    body = await request.body()
    print(f"[*] Webhook received! Body: {body[:200]}...")  # Print first 200 chars
    
    # Get headers
    headers = dict(request.headers)
    print(f"[*] Headers: {headers}")
    
    # Parse event type
    event_type = headers.get("x-github-event", "unknown")
    print(f"[*] Event type: {event_type}")
    
    # Try to parse JSON
    try:
        payload = await request.json()
        if event_type == "pull_request":
            pr_number = payload.get("number", "unknown")
            repo = payload.get("repository", {}).get("full_name", "unknown")
            action = payload.get("action", "unknown")
            print(f"[*] PR #{pr_number} in {repo} - Action: {action}")
    except:
        pass
    
    return {"status": "ok", "event": event_type}

@app.get("/")
async def root():
    return {"message": "NeuralSpace Webhook Test Server is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)