import asyncio
import os
from app.core.config import get_settings
from app.core.gemini_client import get_gemini_client

settings = get_settings()

prompt = """Tu Vyapaar Saarthi ka collections assistant hai.
Ek WhatsApp payment reminder likhna hai. Tone: firm aur urgent.

Details:
- Buyer ka naam: Suresh Enterprises
- Invoice number: #1
- Amount due: 1500
- Kitne din late: 15 din
- History: Yeh buyer ka pehla late payment hai.

Rules (inhe zaroor follow karo):
1. Hinglish mein likho — Hindi aur English ka natural mix
   jaise WhatsApp pe log baat karte hain
2. Maximum 5-6 lines, concise rakho
3. Greeting se shuru karo buyer ke naam ke saath
4. Amount clearly mention karo
5. Invoice number mention karo
6. Firm tone — clearly batao ki supply rok sakte hain
7. Koi emoji mat use karo
8. End mein sirf 'Vyapaar Saarthi' se sign off karo
9. Sirf message text likho — koi explanation, heading, ya
   extra text nahi

Sirf WhatsApp message likho:"""

async def run():
    client = get_gemini_client()
    res = client.models.generate_content(
        model=settings.GEMINI_FLASH_MODEL,
        contents=prompt,
        config={
            "temperature": 0.7,
            "max_output_tokens": 300,
        },
    )
    print("RESPONSE:")
    print(res.text)

if __name__ == "__main__":
    asyncio.run(run())
