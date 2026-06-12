from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Vyapaar Saarthi"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "sqlite:///./vyapaar_saarthi.db"
    DATABASE_ECHO: bool = False

    # Google Cloud
    GCP_PROJECT_ID: str = "your-gcp-project-id"
    GCP_LOCATION: str = "us-central1"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None

    # Gemini Models
    GEMINI_FLASH_MODEL: str = "gemini-2.5-flash"
    GEMINI_PRO_MODEL: str = "gemini-2.5-pro"

    # Vertex AI Speech
    VERTEX_SPEECH_LANGUAGE: str = "hi-IN"

    # GCS Bucket
    GCS_BUCKET_NAME: str = "vyapaar-saarthi-uploads"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5174", "http://localhost:5173", "http://localhost:3000"]

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30

    # HITL
    HITL_CONFIDENCE_THRESHOLD: float = 0.8

    # API Keys (fallback for local dev)
    GEMINI_API_KEY: Optional[str] = None

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
