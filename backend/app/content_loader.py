import json
import os
from functools import lru_cache
from typing import Dict, Any, List

from app.config import get_settings


def _topics_dir() -> str:
    settings = get_settings()
    base = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(base, settings.topic_content_dir.lstrip("./"))


@lru_cache()
def load_all_topics() -> List[Dict[str, Any]]:
    directory = _topics_dir()
    topics = []
    for filename in sorted(os.listdir(directory)):
        if filename.endswith(".json"):
            with open(os.path.join(directory, filename), "r", encoding="utf-8") as f:
                data = json.load(f)
                topics.append(data)
    return topics


def get_topic(topic_id: str) -> Dict[str, Any] | None:
    for topic in load_all_topics():
        if topic["id"] == topic_id:
            return topic
    return None
