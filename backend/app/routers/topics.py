from fastapi import APIRouter, HTTPException
from app.content_loader import load_all_topics, get_topic

router = APIRouter()


@router.get("/topics")
def list_topics():
    topics = load_all_topics()
    return [
        {
            "id": t["id"],
            "title": t["title"],
            "subtitle": t["subtitle"],
            "category": t["topic_metadata"]["category"],
            "difficulty": t["topic_metadata"]["difficulty"],
            "estimated_minutes": t["topic_metadata"]["estimated_minutes"],
        }
        for t in topics
    ]


@router.get("/topics/{topic_id}")
def get_topic_detail(topic_id: str):
    topic = get_topic(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Strip sensitive/internal fields before returning
    questions_public = [
        {
            "id": q["id"],
            "question": q["question"],
            "choices": q["choices"],
        }
        for q in topic["trivia_questions"]
    ]

    return {
        "id": topic["id"],
        "title": topic["title"],
        "subtitle": topic["subtitle"],
        "primer": topic["primer"],
        "trivia_questions": questions_public,
        "topic_metadata": topic["topic_metadata"],
    }
