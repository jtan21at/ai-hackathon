from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Union
from app.content_loader import get_topic

router = APIRouter()


class QuizSubmit(BaseModel):
    topic_id: str
    question_id: str
    user_answer: Union[str, list[str]]


@router.post("/quiz/submit")
def submit_quiz(body: QuizSubmit):
    topic = get_topic(body.topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    question = next(
        (q for q in topic["trivia_questions"] if q["id"] == body.question_id), None
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    q_type = question.get("type", "single")
    correct_answer = question["correct_answer"]

    if q_type == "multiple":
        # Both must be sorted lists for comparison
        user_set = sorted([a.strip() for a in body.user_answer]) if isinstance(body.user_answer, list) else []
        correct_set = sorted([a.strip() for a in correct_answer])
        correct = user_set == correct_set
    else:
        user_ans = body.user_answer if isinstance(body.user_answer, str) else ""
        correct = user_ans.strip() == str(correct_answer).strip()

    return {
        "correct": correct,
        "correct_answer": correct_answer,
        "explanation": question["explanation"],
        "sources": question["curated_sources"],
        "type": q_type,
        "difficulty": question.get("difficulty", "medium"),
    }
