from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
from pydantic import model_validator
import os


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
    GOOGLE_CLOUD_PROJECT: str = "sahayak-ai-12345"
    GOOGLE_CLOUD_LOCATION: str = "us-central1"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    USE_VERTEX_AI: bool = True

    # Legacy compatibility fields (populated from GOOGLE_CLOUD_* if not explicitly set)
    GCP_PROJECT_ID: Optional[str] = None
    GCP_LOCATION: Optional[str] = None

    # Gemini Models
    GEMINI_FLASH_MODEL: str = "gemini-2.5-flash"
    GEMINI_PRO_MODEL: str = "gemini-2.5-pro"
    GEMINI_LIVE_MODEL: str = "gemini-live-2.5-flash-native-audio"

    # Speech Models (Cloud STT)
    STT_MODEL: str = "chirp_2"
    STT_LANGUAGE: str = "hi-IN"
    STT_GEMINI_MODEL: str = "gemini-2.5-flash"

    # Speech Models (Gemini TTS)
    TTS_GEMINI_MODEL: str = "gemini-2.5-flash-preview-tts"
    TTS_GEMINI_VOICE: str = "Aoede"
    TTS_LANGUAGE: str = "hi-IN"

    # Legacy compatibility settings (mapped from STT_LANGUAGE if not set)
    VERTEX_SPEECH_LANGUAGE: Optional[str] = None

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
    USE_MOCK_GCP: bool = False

    # Telegram Integration
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_ALLOWED_CHAT_IDS: str = ""
    TELEGRAM_ADMIN_IDS: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }

    @model_validator(mode="after")
    def populate_compatibility_and_credentials(self) -> "Settings":
        # Resolve legacy GCP project ID/location
        if not self.GCP_PROJECT_ID:
            self.GCP_PROJECT_ID = self.GOOGLE_CLOUD_PROJECT
        if not self.GCP_LOCATION:
            self.GCP_LOCATION = self.GOOGLE_CLOUD_LOCATION
            
        # Resolve legacy Speech Language
        if not self.VERTEX_SPEECH_LANGUAGE:
            self.VERTEX_SPEECH_LANGUAGE = self.STT_LANGUAGE

        # Expose credentials file path to Google libraries through env var
        if self.GOOGLE_APPLICATION_CREDENTIALS:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.GOOGLE_APPLICATION_CREDENTIALS
            
        return self


@lru_cache()
def get_settings() -> Settings:
    return Settings()
