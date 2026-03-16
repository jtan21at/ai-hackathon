"""
watsonx Orchestrate research skill client.

Calls the Orchestrate skill API with a system prompt and user question.
Returns synthesized answer text + Tavily source URLs.

When credentials are not configured, returns a stub response so the
quiz path and UI work during development without IBM access.
"""

import httpx
from app.config import get_settings


SYSTEM_PROMPT_TEMPLATE = """You are an educational assistant helping a beginner learn about {topic_title}.

You have access to a web search tool. Use it to find information relevant to the user's question about {search_scope}.

Rules you must follow without exception:
1. Search before answering. Do not answer from memory alone.
2. Answer ONLY using information found in your search results.
3. Do NOT generate, guess, or invent any URLs or source links.
   Source links will be attached separately by the system.
4. If the search results do not contain enough information to answer the question, say exactly:
   "I don't have enough information on that right now. Try checking the sources below or rephrasing your question."
5. Keep your answer under 150 words.
6. Use simple, beginner-friendly language. Define technical terms before using them.
7. Stay focused on {topic_title}. If the question is unrelated, say:
   "I'm focused on {topic_title} right now — ask me anything about that!"

User question: {question}"""


async def call_orchestrate(
    topic_title: str,
    search_scope: str,
    question: str,
) -> dict:
    settings = get_settings()

    # If no credentials configured, return a stub so the UI still works
    if not settings.orchestrate_api_key or not settings.orchestrate_skill_id:
        return _stub_response(topic_title, question)

    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        topic_title=topic_title,
        search_scope=search_scope,
        question=question,
    )

    headers = {
        "Authorization": f"Bearer {settings.orchestrate_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "instance_id": settings.orchestrate_instance_id,
        "skill_id": settings.orchestrate_skill_id,
        "input": {
            "system_prompt": prompt,
            "user_message": question,
        },
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.orchestrate_api_url}/skills/invoke",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    answer = data.get("output", {}).get("text", "No answer returned.")
    sources = [
        {
            "title": s.get("title", "Source"),
            "url": s["url"],
            "excerpt": s.get("snippet", ""),
        }
        for s in data.get("sources", [])
        if s.get("url")
    ]

    return {"answer": answer, "sources": sources}


def _stub_response(topic_title: str, question: str) -> dict:
    return {
        "answer": (
            f"[Demo mode — Orchestrate not connected] "
            f"This is where the live research answer about '{question}' would appear. "
            f"Once you add your watsonx Orchestrate credentials to .env, "
            f"this chatbot will search the web and synthesize a real answer about {topic_title}."
        ),
        "sources": [
            {
                "title": "watsonx Orchestrate — IBM",
                "url": "https://www.ibm.com/products/watsonx-orchestrate",
                "excerpt": "Add ORCHESTRATE_API_KEY and ORCHESTRATE_SKILL_ID to .env to enable live research.",
            }
        ],
    }
