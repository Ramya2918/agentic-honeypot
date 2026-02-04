from fastapi import FastAPI, Header, HTTPException, Body
from typing import Optional, Dict, Any, List
import os
import random
import re
import requests

app = FastAPI()

# --------------------
# Config
# --------------------
API_KEY = os.getenv("API_KEY", "shakti123")
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# --------------------
# Agent replies
# --------------------
AGENT_REPLIES = [
    "Why is my account being suspended?",
    "Which bank is this regarding?",
    "Can you explain what verification is needed?",
    "I need more details to understand this."
]

# --------------------
# Regex patterns
# --------------------
UPI_REGEX = r"\b[\w.\-]+@[\w]+\b"
URL_REGEX = r"https?://[^\s]+"
BANK_REGEX = r"\b\d{9,18}\b"

# --------------------
# Memory (simple in-memory store)
# --------------------
session_store: Dict[str, Dict[str, Any]] = {}

# --------------------
# Honeypot Endpoint
# --------------------
@app.post("/honeypot")
def honeypot(
    payload: Optional[Dict[str, Any]] = Body(default=None),
    x_api_key: Optional[str] = Header(None, alias="x-api-key")
):
    # 🔐 Auth
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 🧪 Tester sends empty body
    if not payload:
        return {
            "status": "success",
            "reply": "Why is my account being suspended?"
        }

    session_id = payload.get("sessionId", "unknown-session")
    message_text = payload.get("message", {}).get("text", "").lower()
    history = payload.get("conversationHistory", [])

    # Init session
    if session_id not in session_store:
        session_store[session_id] = {
            "messages": [],
            "bankAccounts": [],
            "upiIds": [],
            "phishingLinks": [],
            "suspiciousKeywords": []
        }

    session_store[session_id]["messages"].append(message_text)

    # Scam detection
    scam_keywords = ["bank", "blocked", "verify", "urgent", "account", "upi", "link"]
    scam_detected = any(word in message_text for word in scam_keywords)

    # Intelligence extraction
    session_store[session_id]["upiIds"].extend(re.findall(UPI_REGEX, message_text))
    session_store[session_id]["phishingLinks"].extend(re.findall(URL_REGEX, message_text))
    session_store[session_id]["bankAccounts"].extend(re.findall(BANK_REGEX, message_text))

    for word in scam_keywords:
        if word in message_text:
            session_store[session_id]["suspiciousKeywords"].append(word)

    # Agent reply
    reply = random.choice(AGENT_REPLIES) if scam_detected else "Thank you for the information."

    # --------------------
    # FINAL CALLBACK (MANDATORY)
    # --------------------
    if scam_detected:
        payload = {
            "sessionId": session_id,
            "scamDetected": True,
            "totalMessagesExchanged": len(session_store[session_id]["messages"]),
            "extractedIntelligence": {
                "bankAccounts": list(set(session_store[session_id]["bankAccounts"])),
                "upiIds": list(set(session_store[session_id]["upiIds"])),
                "phishingLinks": list(set(session_store[session_id]["phishingLinks"])),
                "phoneNumbers": [],
                "suspiciousKeywords": list(set(session_store[session_id]["suspiciousKeywords"]))
            },
            "agentNotes": "Scammer used urgency and account suspension tactics"
        }

        try:
            requests.post(GUVI_CALLBACK_URL, json=payload, timeout=5)
        except Exception:
            pass  # Do not fail API if callback fails

    # --------------------
    # RESPONSE (EXACT FORMAT)
    # --------------------
    return {
        "status": "success",
        "reply": reply
    }

@app.get("/")
def health():
    return {"status": "running"}
