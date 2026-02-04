from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import random

# -------------------
# App setup
# -------------------
app = FastAPI()

# API Key (keep default for safety if env not set)
API_KEY = os.getenv("API_KEY", "shakti123")

# -------------------
# Request Models (MATCHES EVALUATOR FORMAT)
# -------------------

class MessagePayload(BaseModel):
    sender: str
    text: str
    timestamp: int

class ScamRequest(BaseModel):
    sessionId: str
    message: MessagePayload
    conversationHistory: List[dict] = []
    metadata: Optional[dict] = None

# -------------------
# Agent replies (simple & safe)
# -------------------
AGENT_REPLIES = [
    "Why is my account being suspended?",
    "Which bank is this regarding?",
    "Can you explain what verification is needed?",
    "I need more details to understand this."
]

# -------------------
# Honeypot Endpoint
# -------------------
@app.post("/honeypot")
def honeypot(
    data: ScamRequest,
    x_api_key: Optional[str] = Header(None, alias="x-api-key")
):
    # Authentication check (as per evaluator)
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Extract scam message text
    text = data.message.text.lower()

    # Simple scam detection (rule-based)
    scam_keywords = ["bank", "blocked", "verify", "urgent", "account"]
    is_scam = any(word in text for word in scam_keywords)

    # Agent reply
    if is_scam:
        reply = random.choice(AGENT_REPLIES)
    else:
        reply = "Thank you for the information."

    # EXACT response format expected by evaluator
    return {
        "status": "success",
        "reply": reply
    }

# -------------------
# Optional health check (safe)
# -------------------
@app.get("/")
def health():
    return {"status": "running"}
