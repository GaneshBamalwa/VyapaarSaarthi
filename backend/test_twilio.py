import asyncio
import os
from app.core.config import get_settings
from app.agents.collections.whatsapp_service import send_whatsapp_message

async def run():
    res = await send_whatsapp_message("+919674411734", "Hello test,\nThis is ₹1500 test.\nEnd of message.")
    print("Twilio response:", res)

if __name__ == "__main__":
    asyncio.run(run())
