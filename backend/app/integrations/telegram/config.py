from pydantic_settings import BaseSettings
import os
import sys

class TelegramConfig(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_ALLOWED_CHAT_IDS: str = ""
    TELEGRAM_ADMIN_IDS: str = ""
    
    @property
    def allowed_users(self) -> list[int]:
        if not self.TELEGRAM_ALLOWED_CHAT_IDS:
            return []
        return [int(x.strip()) for x in self.TELEGRAM_ALLOWED_CHAT_IDS.split(",") if x.strip()]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

def get_telegram_config() -> TelegramConfig:
    try:
        return TelegramConfig()
    except Exception as e:
        print(f"CRITICAL ERROR: Telegram configuration missing. {e}")
        sys.exit(1)
