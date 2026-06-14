import logging
import httpx
from app.integrations.whatsapp.config import get_whatsapp_config

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """Thin wrapper around the Meta WhatsApp Cloud API (Graph API)."""

    def __init__(self):
        self.config = get_whatsapp_config()

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.config.WHATSAPP_TOKEN}",
        }

    async def send_text(self, to: str, body: str) -> None:
        """Send a plain/markdown text message to a WhatsApp user.

        WhatsApp supports *bold*, _italic_, ~strikethrough~ and ```mono``` —
        the same `*...*` bold syntax the Telegram formatter already emits.
        """
        url = f"{self.config.base_url}/{self.config.WHATSAPP_PHONE_NUMBER_ID}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": body},
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=self._headers, json=payload)
            if resp.status_code >= 400:
                logger.error(f"WhatsApp send_text failed [{resp.status_code}]: {resp.text}")
            resp.raise_for_status()

    async def download_media(self, media_id: str) -> bytes:
        """Resolve a media id to its temporary URL and download the raw bytes."""
        async with httpx.AsyncClient(timeout=60) as client:
            meta_url = f"{self.config.base_url}/{media_id}"
            meta_resp = await client.get(meta_url, headers=self._headers)
            meta_resp.raise_for_status()
            media_url = meta_resp.json()["url"]

            # The media URL must be fetched with the same bearer auth header.
            media_resp = await client.get(media_url, headers=self._headers)
            media_resp.raise_for_status()
            return media_resp.content
