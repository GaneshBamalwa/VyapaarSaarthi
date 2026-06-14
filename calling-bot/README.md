# Vyapaar Saarthi — Calling Bot 📞

Receive phone calls and drive the **same** business pipeline as the Telegram bot.

```
Caller speaks  ──▶  Twilio (speech → text)  ──▶  this service
                                                     │
                                                     ▼
                         backend  POST /api/communication/message
                         (CommunicationService → intent → orders)
                                                     │
                                                     ▼
                         spoken reply  ◀──  Twilio <Say>  ◀── this service
```

Twilio's built-in speech recognition does the audio→text step (via
`<Gather input="speech">`), so the transcript is handed straight to the backend's
shared `CommunicationService` — the exact pipeline Telegram uses for voice notes.

## Prerequisites

- The **backend** running and reachable (default `http://localhost:8000`).
- A **Twilio account** with a **Voice-capable phone number**.
- `ngrok` (or any public HTTPS tunnel) to expose this service to Twilio.

## Setup

```bash
cd calling-bot
python -m venv venv && source venv/Scripts/activate   # Windows Git Bash
# (PowerShell: .\venv\Scripts\Activate.ps1)
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
- `BACKEND_URL` — where the backend is (e.g. `http://localhost:8000`).
- `VOICE_LANGUAGE` — `hi-IN` (Hindi) or `en-IN`.
- `TWILIO_AUTH_TOKEN` — from the Twilio console (enables webhook validation).
- `PUBLIC_BASE_URL` — your ngrok HTTPS URL (only needed when validation is on).

## Run

1. **Start the backend** (separate terminal, from `backend/`):
   ```bash
   uvicorn app.main:app --port 8000
   ```
2. **Start this service:**
   ```bash
   python main.py        # listens on :8002
   ```
   Check: <http://localhost:8002/health>
3. **Expose it** (separate terminal):
   ```bash
   ngrok http 8002
   ```
   Put the `https://…ngrok-free.app` URL into `PUBLIC_BASE_URL` and restart.
4. **Point Twilio at it:** Twilio Console → your number → **Voice Configuration**
   → *A call comes in* → **Webhook**:
   `https://<your-ngrok>/voice/incoming` (HTTP **POST**).
5. **Call the number** and speak, e.g. *"Create order for Ramesh, 20 cement bags, tomorrow"* or *"pending orders"*. Say *"bye"* to hang up.

## Notes

- Natural Hinglish (e.g. *"Ramesh ko 20 cement bags kal bhej do"*) only routes
  correctly when the backend uses the Gemini intent parser
  (`TELEGRAM_USE_GEMINI=true` in the backend `.env`). The default regex parser
  needs English keywords like *"create order"*, *"pending"*, *"ORD-1 completed"*.
- `bot.py` in this folder is an unrelated legacy legal Q&A chatbot and is not part
  of the calling feature — it can be removed.
