import os
import random
import re
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Optional


app = FastAPI()

API_KEY = os.getenv("API_KEY")


SCAM_KEYWORDS = [
    "lottery", "won", "urgent", "upi", "bank",
    "account", "verify", "click", "link", "payment"
]

AGENT_RESPONSES = [
    "I’m not fully understanding this, can you explain again?",
    "Which bank is this related to?",
    "I got many messages like this before, how is this different?",
    "Can you please share the details properly?",
    "What should I do next?"
]

UPI_REGEX = r"\b[\w.\-]+@[\w]+\b"
URL_REGEX = r"https?://[^\s]+"
BANK_REGEX = r"\b\d{9,18}\b"

conversation_memory = {}

class ScamMessage(BaseModel):
    conversation_id: str
    message: str


def detect_scam(message: str) -> bool:
    message = message.lower()
    for word in SCAM_KEYWORDS:
        if word in message:
            return True
    return False


def extract_intelligence(message: str):
    return {
        "upi_ids": re.findall(UPI_REGEX, message),
        "phishing_links": re.findall(URL_REGEX, message),
        "bank_accounts": re.findall(BANK_REGEX, message)
    }


@app.post("/honeypot")
def honeypot(
    data: ScamMessage,
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    if authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    convo_id = data.conversation_id
    message = data.message

    if convo_id not in conversation_memory:
        conversation_memory[convo_id] = {
            "messages": [],
            "agent_active": False,
            "extracted": {
                "upi_ids": [],
                "phishing_links": [],
                "bank_accounts": []
            }
        }

    conversation_memory[convo_id]["messages"].append(message)

    scam_detected = detect_scam(message)

    if scam_detected:
        conversation_memory[convo_id]["agent_active"] = True
        agent_reply = random.choice(AGENT_RESPONSES)
    else:
        agent_reply = "Okay, noted."

    extracted_now = extract_intelligence(message)

    for key in extracted_now:
        conversation_memory[convo_id]["extracted"][key].extend(
            extracted_now[key]
        )

    return {
        "scam_detected": scam_detected,
        "agent_active": conversation_memory[convo_id]["agent_active"],
        "agent_reply": agent_reply,
        "extracted_intelligence": conversation_memory[convo_id]["extracted"]
    }

