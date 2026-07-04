# backend/app/elevenlabs/service.py

"""Service utilities for proxying ElevenLabs Conversational AI SDK calls.

The implementation stores lightweight conversation sessions in an in‑memory
dictionary (session_id → Conversation object).  Each session is created via
`start_conversation` and cleared with `end_conversation`.  Audio chunks are
sent to the ElevenLabs SDK using the API key and the pre‑created agent ID.

This module deliberately contains **no secrets** – it reads the API key and
agent ID from environment variables that are loaded from the project's
`.env` file via `python-dotenv` (already used elsewhere in the project).
"""

import os
import uuid
import base64
from typing import Dict, Any
from elevenlabs.client import ElevenLabs

# Load secrets from the environment (already populated by `python-dotenv` in main)
_ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
_ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID")

if not _ELEVENLABS_API_KEY or not _ELEVENLABS_AGENT_ID:
    raise RuntimeError("ElevenLabs API key or Agent ID not configured in .env")

# Initialise the ElevenLabs client once
_client = ElevenLabs(api_key=_ELEVENLABS_API_KEY)

# In‑memory store for active conversations
_sessions: Dict[str, Any] = {}


def start_conversation() -> str:
    """Create a new conversation session and return its UUID.
    """
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {}
    return session_id


def end_conversation(session_id: str) -> None:
    """Remove a conversation from the in‑memory store.
    """
    _sessions.pop(session_id, None)


def _decode_audio(b64_audio: str) -> bytes:
    try:
        return base64.b64decode(b64_audio)
    except Exception as exc:
        raise ValueError("Invalid base64 audio payload") from exc


def _encode_audio(audio_bytes: bytes) -> str:
    return base64.b64encode(audio_bytes).decode("utf-8")


def process_message(session_id: str, b64_audio: str) -> Dict[str, str]:
    """Send an audio chunk to ElevenLabs and return the response.
    Returns a dict with ``audio`` (base64) and optional ``transcript``.
    """
    if session_id not in _sessions:
        raise ValueError("Invalid or expired session_id")

    audio_bytes = _decode_audio(b64_audio)

    try:
        response = _client.conversation.chat(
            agent_id=_ELEVENLABS_AGENT_ID,
            audio=audio_bytes,
        )
    except Exception as exc:
        raise RuntimeError(f"ElevenLabs SDK error: {exc}") from exc

    resp_audio = response.get("audio")
    transcript = response.get("transcript", "")
    if resp_audio is None:
        raise RuntimeError("ElevenLabs response missing audio data")
    return {"audio": _encode_audio(resp_audio), "transcript": transcript}
