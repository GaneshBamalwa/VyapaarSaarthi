# WhatsApp Integration Documentation

## Overview
The WhatsApp integration provides the **exact same functionality** as the Telegram
bot — authorized users interact with Vyapaar Saarthi from WhatsApp. It acts as a pure
communication channel without embedding any business logic, reusing the same
`CommunicationService`, intent parser, and order services.

## Architecture
- **Communication Layer (`app/communication`)**: Parses incoming text, detects intents using `IntentParser`, and extracts entities. *(shared with Telegram)*
- **Service Layer (`app/services/communication_service.py`)**: Routes the detected intent to existing services (`IntakeService`, `OrderRepository`). *(shared with Telegram)*
- **WhatsApp Layer (`app/integrations/whatsapp`)**: `config.py` (settings), `client.py` (send text / download media via the Graph API), `handlers.py` (whitelist verification, message routing, voice transcription, response formatting).
- **Webhook Router (`app/routers/whatsapp.py`)**: Mounted on the existing FastAPI app at `/api/whatsapp/webhook`.

### Why a webhook (not long polling)?
Telegram supports long polling (the bot runs as a standalone `python -m` process).
WhatsApp's Cloud API is **webhook only** — Meta pushes inbound messages to an HTTPS
endpoint. The integration is therefore mounted on the running FastAPI server rather
than run as a separate process.

## Setup
1. Create a Meta App with the **WhatsApp** product (https://developers.facebook.com).
2. From the WhatsApp dashboard, note the **Phone Number ID** and generate an access token.
3. Add to `.env`:
   ```env
   WHATSAPP_TOKEN=your_cloud_api_token
   WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
   WHATSAPP_VERIFY_TOKEN=vyapaar-saarthi-verify
   WHATSAPP_API_VERSION=v21.0
   WHATSAPP_ALLOWED_NUMBERS=919876543210,919812345678
   ```
4. Run the backend (the webhook is part of the FastAPI app):
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```
5. Expose it publicly (e.g. `ngrok http 8000`) and configure the Meta webhook:
   - **Callback URL**: `https://<your-domain>/api/whatsapp/webhook`
   - **Verify token**: the same value as `WHATSAPP_VERIFY_TOKEN`
   - Subscribe to the **messages** field.

## Supported Commands
- `/start` (or "hi" / "namaste") - Start interaction
- `/help` - View help
- `/orders` - List 20 most recent orders
- `/pending` - List pending orders
- `/today` - List today's deliveries
- `/overdue` - List overdue orders

## Natural Language Intents
- **Create Order**: "Create order for Ramesh 20 cement bags tomorrow"
- **Search**: "Search ORD-123"
- **Update Delivery**: "Change ORD-123 delivery to tomorrow"
- **Mark Complete**: "ORD-123 completed"

## Voice Notes
WhatsApp voice notes (OGG Opus) are downloaded via the media endpoint, transcribed
through Gemini/Cloud Speech-to-Text (`speech_to_text`), and routed exactly like a
typed message — identical to the Telegram voice flow.
