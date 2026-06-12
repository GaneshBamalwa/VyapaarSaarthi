from google import genai
from google.genai import types
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

_client: genai.Client | None = None


def get_gemini_client() -> genai.Client:
    global _client
    if _client is None:
        try:
            if settings.GEMINI_API_KEY:
                _client = genai.Client(api_key=settings.GEMINI_API_KEY)
                logger.info("Gemini client initialized with API key")
            else:
                _client = genai.Client(
                    vertexai=True,
                    project=settings.GCP_PROJECT_ID,
                    location=settings.GCP_LOCATION,
                )
                logger.info("Gemini client initialized with Vertex AI")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise
    return _client
