"""IBM Text to Speech client."""

from typing import Optional

import httpx

from app.config import get_settings


async def synthesize_speech(text: str) -> Optional[bytes]:
    settings = get_settings()

    clean_text = " ".join(text.split()).strip()
    if not clean_text:
        return None

    providers = []
    if settings.tts_api_key and settings.tts_api_url:
        providers.append((settings.tts_api_url, settings.tts_api_key, settings.tts_default_voice))
    if settings.tts_backup_api_key and settings.tts_backup_api_url:
        providers.append((settings.tts_backup_api_url, settings.tts_backup_api_key, settings.tts_backup_voice or settings.tts_default_voice))

    if not providers:
        return None

    headers = {
        "Content-Type": "application/json",
        "Accept": "audio/mp3",
    }
    payload = {"text": clean_text[:4500]}
    last_error = None

    async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as client:
        for base_url, api_key, voice in providers:
            try:
                response = await client.post(
                    _synthesize_url(base_url),
                    params={"voice": voice},
                    headers=headers,
                    json=payload,
                    auth=("apikey", api_key),
                )
                response.raise_for_status()
                return response.content
            except httpx.HTTPError as exc:
                last_error = exc

    if last_error:
        raise last_error
    return None



def _synthesize_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/v1/synthesize"):
        return normalized
    if normalized.endswith("/v1"):
        return f"{normalized}/synthesize"
    return f"{normalized}/v1/synthesize"
