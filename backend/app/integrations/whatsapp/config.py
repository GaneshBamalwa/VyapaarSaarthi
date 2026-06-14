from pydantic_settings import BaseSettings
import sys


class WhatsAppConfig(BaseSettings):
    # Permanent / system-user access token from the Meta App
    WHATSAPP_TOKEN: str = ""
    # Phone Number ID of the WhatsApp Business number (from Meta dashboard)
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    # Token you choose and also enter in the Meta webhook config to verify the callback
    WHATSAPP_VERIFY_TOKEN: str = "vyapaar-saarthi-verify"
    # Graph API version
    WHATSAPP_API_VERSION: str = "v21.0"
    # Comma separated whitelist of E.164 numbers (without +), empty = allow all (dev)
    WHATSAPP_ALLOWED_NUMBERS: str = ""

    @property
    def allowed_users(self) -> list[str]:
        if not self.WHATSAPP_ALLOWED_NUMBERS:
            return []
        return [x.strip() for x in self.WHATSAPP_ALLOWED_NUMBERS.split(",") if x.strip()]

    @property
    def base_url(self) -> str:
        return f"https://graph.facebook.com/{self.WHATSAPP_API_VERSION}"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


def get_whatsapp_config() -> WhatsAppConfig:
    try:
        return WhatsAppConfig()
    except Exception as e:
        print(f"CRITICAL ERROR: WhatsApp configuration missing. {e}")
        sys.exit(1)
