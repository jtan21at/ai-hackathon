import base64
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from app.services.tts_service import synthesize_speech

router = APIRouter()


class TTSRequest(BaseModel):
    text: str


@router.post("/tts")
async def text_to_speech(body: TTSRequest):
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    audio_bytes = await synthesize_speech(body.text)

    if audio_bytes is None:
        # TTS not configured — return a clear signal to the frontend
        raise HTTPException(
            status_code=503,
            detail="TTS not configured. Add TTS_API_KEY and TTS_API_URL to .env.",
        )

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    return {"audio_base64": audio_b64, "format": "mp3"}
