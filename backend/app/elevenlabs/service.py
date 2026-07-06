# backend/app/elevenlabs/service.py

"""Service utilities for proxying ElevenLabs Conversational AI SDK calls.

Generates a secure temporary signed URL for client-side connection.
Uses a direct HTTP call to avoid SDK version compatibility issues.
"""

import os
import httpx


def start_conversation() -> str:
    """Request a secure signed WebSocket URL from ElevenLabs Conversational AI.

    Reads API key and agent ID fresh from the environment on every call so
    that changes to .env (and a server restart) are always picked up.
    """
    api_key = os.getenv("ELEVENLABS_API_KEY")
    agent_id = os.getenv("ELEVENLABS_AGENT_ID")

    if not api_key or not agent_id:
        raise RuntimeError(
            "ElevenLabs API key or Agent ID not configured in .env. "
            "Set ELEVENLABS_API_KEY and ELEVENLABS_AGENT_ID and restart the server."
        )

    try:
        # Use direct HTTP call - more reliable than SDK across different environments
        response = httpx.get(
            f"https://api.elevenlabs.io/v1/convai/conversation/get_signed_url",
            params={"agent_id": agent_id},
            headers={"xi-api-key": api_key},
            timeout=15.0
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"ElevenLabs API error {response.status_code}: {response.text}"
            )
        data = response.json()
        return data["signed_url"]
    except httpx.RequestError as exc:
        raise RuntimeError(f"ElevenLabs network error: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"ElevenLabs SDK error: {exc}") from exc
