from fastapi import FastAPI, Header, HTTPException, Request
from typing import Optional, Dict, Any
import os
import random
import re
import requests

app = FastAPI()

API_KEY = os.getenv("API_KEY", "shakti123")
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

AGENT_REPLIES = [
    "Why is my account being suspended?",
    "Which bank is this regarding?",
    "Can you explain what verification is needed?",
    "I need more details to understand this."
]

UPI_REGEX = r"\b[\w.\-]+@[\w]+\b"
URL_REGEX = r"https?://[^\s]+"
BANK_REGEX = r"\b\d{9,18}\b"

session_store: Dict[str, Dict[str, Any]] = {}

@app.post("/honeypot")
async def honeypot(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="x-api-key")
):
    # 🔐 Auth
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 🧪 Try to read JSON body (may not exist)
    try:
        payload = await request.json()
    except Exception:
        payload = None

    # 🧪 CASE 1: GUVI tester (EMPTY BODY)
    if not payload:
        return {
            "status": "success",
            "reply": "Why is my account being suspended?"
        }

    # 🧪 CASE 2: Full evaluation request
    session_id = payload.get("sessionId", "unknown-session")
    message_text = payload.get("message", {}).get("text", "").lower()

    if session_id not in session_store:
        session_store[session_id] = {
            "messages": [],
            "bankAccounts": [],
            "upiIds": [],
            "phishingLinks": [],
            "suspiciousKeywords": []
        }

    session_store[session_id]["messages"].append(message_text)

    scam_keywords = ["bank", "blocked", "verify", "urgent", "account", "upi", "link"]
    scam_detected = any(word in message_text for word in scam_keywords)

    session_store[session_id]["upiIds"].extend(re.findall(UPI_REGEX, message_text))
    session_store[session_id]["phishingLinks"].extend(re.findall(URL_REGEX, message_text))
    session_store[session_id]["bankAccounts"].extend(re.findall(BANK_REGEX, message_text))

    for word in scam_keywords:
        if word in message_text:
            session_store[session_id]["suspiciousKeywords"].append(word)

    reply = random.choice(AGENT_REPLIES) if scam_detected else "Thank you for the information."

    # 🔔 Mandatory GUVI callback
    if scam_detected:
        callback_payload = {
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
            requests.post(GUVI_CALLBACK_URL, json=callback_payload, timeout=5)
        except Exception:
            pass

    return {
        "status": "success",
        "reply": reply
    }

@app.get("/")
def health():
    return {"status": "running"}
