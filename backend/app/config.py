from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    orchestrate_api_url: str = ""
    orchestrate_api_key: str = ""
    orchestrate_instance_id: str = ""
    orchestrate_skill_id: str = ""

    tavily_api_key: str = ""

    tts_api_url: str = ""
    tts_api_key: str = ""
    tts_default_voice: str = "en-US_AllisonV3Voice"

    topic_content_dir: str = "./content/topics"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
