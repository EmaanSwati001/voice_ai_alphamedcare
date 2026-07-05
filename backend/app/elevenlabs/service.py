# backend/app/elevenlabs/service.py

"""Service utilities for proxying ElevenLabs Conversational AI SDK calls.

Generates a secure temporary signed URL for client-side connection.
"""

import os
from elevenlabs.client import ElevenLabs

# Load secrets from the environment
_ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
_ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID")

if not _ELEVENLABS_API_KEY or not _ELEVENLABS_AGENT_ID:
    raise RuntimeError("ElevenLabs API key or Agent ID not configured in .env")

# Initialise the ElevenLabs client once
_client = ElevenLabs(api_key=_ELEVENLABS_API_KEY)


def start_conversation() -> str:
    """Request a secure signed WebSocket URL from ElevenLabs Conversational AI.
    """
    try:
        response = _client.conversational_ai.conversations.get_signed_url(
            agent_id=_ELEVENLABS_AGENT_ID
        )
        return response.signed_url
    except Exception as exc:
        raise RuntimeError(f"ElevenLabs SDK error: {exc}") from exc
