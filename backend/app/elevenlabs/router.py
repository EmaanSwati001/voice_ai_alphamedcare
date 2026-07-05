# backend/app/elevenlabs/router.py

"""FastAPI router that proxies ElevenLabs Conversational AI SDK calls.

Provides endpoints to establish secure client-side sessions.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .service import start_conversation

router = APIRouter()


class StartResponse(BaseModel):
    signed_url: str

@router.post("/start", response_model=StartResponse)
def start():
    try:
        signed_url = start_conversation()
        return {"signed_url": signed_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class MessageRequest(BaseModel):
    session_id: str
    audio: str

class MessageResponse(BaseModel):
    audio: str
    transcript: str = ""

# Deprecated/Placeholder endpoint for backwards compatibility
@router.post("/message", response_model=MessageResponse)
def message(req: MessageRequest):
    return {"audio": "", "transcript": "Deprecated. Direct client-side WebSocket is now used."}


class EndRequest(BaseModel):
    session_id: str

# Deprecated/Placeholder endpoint for backwards compatibility
@router.post("/end")
def end(req: EndRequest):
    return {"detail": "conversation ended"}
