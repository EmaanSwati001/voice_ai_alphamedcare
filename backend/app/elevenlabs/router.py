# backend/app/elevenlabs/router.py

"""FastAPI router that proxies ElevenLabs Conversational AI SDK calls.

Provides three endpoints:
* POST /start – create a conversation session, returns session_id.
* POST /message – send base64‑encoded audio to ElevenLabs, receive base64 response audio and transcript.
* POST /end – terminate the session.

All secrets are kept on the backend; the frontend never sees the API key or Agent ID.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict

from .service import start_conversation, end_conversation, process_message

router = APIRouter()


class StartResponse(BaseModel):
    session_id: str

@router.post("/start", response_model=StartResponse)
def start():
    try:
        return {"session_id": start_conversation()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class MessageRequest(BaseModel):
    session_id: str
    audio: str  # base64‑encoded audio chunk

class MessageResponse(BaseModel):
    audio: str  # base64‑encoded response audio
    transcript: str = ""

@router.post("/message", response_model=MessageResponse)
def message(req: MessageRequest):
    try:
        result: Dict[str, str] = process_message(req.session_id, req.audio)
        return {"audio": result["audio"], "transcript": result.get("transcript", "")}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=502, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class EndRequest(BaseModel):
    session_id: str

@router.post("/end")
def end(req: EndRequest):
    try:
        end_conversation(req.session_id)
        return {"detail": "conversation ended"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
