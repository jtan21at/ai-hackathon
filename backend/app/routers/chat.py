from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.content_loader import get_topic
from app.services.orchestrate import call_orchestrate

router = APIRouter()


class ChatRequest(BaseModel):
    topic_id: str
    question: str


@router.post("/chat")
async def chat(body: ChatRequest):
    topic = get_topic(body.topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    result = await call_orchestrate(
        topic_title=topic["title"],
        search_scope=topic["search_scope"],
        question=body.question,
    )

    return result
