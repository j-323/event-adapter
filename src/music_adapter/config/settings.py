import os
from functools import lru_cache
from pydantic import BaseSettings, Field, AnyHttpUrl

class Settings(BaseSettings):
    # Broker
    BROKER_URL: str = Field(..., env="BROKER_URL")
    IN_TOPIC: str = Field("raw.music.events", env="IN_TOPIC")
    OUT_TOPIC: str = Field("processed.music.events", env="OUT_TOPIC")

    # Services
    PREPROCESS_URL: AnyHttpUrl = Field(..., env="PREPROCESS_URL")
    GENERATION_URL: AnyHttpUrl = Field(..., env="GENERATION_URL")

    # Timeouts & Prefetch
    HTTP_TIMEOUT: int = Field(10, env="HTTP_TIMEOUT")
    BROKER_PREFETCH: int = Field(10, env="BROKER_PREFETCH")

    # JSON schema
    SCHEMA_PATH: str = Field("schemas/event_schema.json", env="SCHEMA_PATH")

    # Health endpoint
    HEALTH_PORT: int = Field(8000, env="HEALTH_PORT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()