"""
IBM Text to Speech client.

Converts text to MP3 audio. Returns raw bytes.
Falls back to None when credentials are not configured.
"""

import httpx
import base64
from app.config import get_settings


async def synthesize_speech(text: str) -> bytes | None:
    settings = get_settings()

    if not settings.tts_api_key or not settings.tts_api_url:
        return None

    url = f"{settings.tts_api_url}/v1/synthesize"
    params = {"voice": settings.tts_default_voice}
    headers = {
        "Content-Type": "application/json",
        "Accept": "audio/mp3",
    }
    payload = {"text": text}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            params=params,
            headers=headers,
            json=payload,
            auth=("apikey", settings.tts_api_key),
        )
        response.raise_for_status()
        return response.content
