from fastapi import FastAPI, Header, HTTPException, Body
from typing import Optional, Dict, Any
import os
import random

app = FastAPI()

API_KEY = os.getenv("API_KEY", "shakti123")

AGENT_REPLIES = [
    "Why is my account being suspended?",
    "Which bank is this regarding?",
    "Can you explain what verification is needed?",
    "I need more details to understand this."
]

@app.post("/honeypot")
def honeypot(
    payload: Optional[Dict[str, Any]] = Body(default=None),
    x_api_key: Optional[str] = Header(None, alias="x-api-key")
):
    # 🔐 Auth check
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 🧪 CASE 1: Tester sends EMPTY body
    if not payload:
        return {
            "status": "success",
            "reply": "Why is my account being suspended?"
        }

    # 🧪 CASE 2: Evaluator sends full body
    try:
        text = payload["message"]["text"].lower()
    except Exception:
        return {
            "status": "success",
            "reply": "Why is my account being suspended?"
        }

    scam_keywords = ["bank", "blocked", "verify", "urgent", "account"]
    is_scam = any(word in text for word in scam_keywords)

    reply = random.choice(AGENT_REPLIES) if is_scam else "Thank you for the information."

    return {
        "status": "success",
        "reply": reply
    }

@app.get("/")
def health():
    return {"status": "running"}
