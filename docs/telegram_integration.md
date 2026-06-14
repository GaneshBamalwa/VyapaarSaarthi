# Telegram Integration Documentation

## Overview
The Telegram integration allows authorized users to interact with Vyapaar Saarthi directly from Telegram.
It acts as a pure communication channel without embedding any business logic.

## Architecture
- **Communication Layer (`app/communication`)**: Parses incoming text, detects intents using `IntentParser`, and extracts entities.
- **Service Layer (`app/services/communication_service.py`)**: Routes the detected intent to existing services (`IntakeService`, `OrderRepository`).
- **Telegram Layer (`app/integrations/telegram`)**: Handles Telegram API interaction, whitelist verification, and message formatting.

## Setup
1. Get a Telegram Bot Token from BotFather.
2. Add to `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=your_token
   TELEGRAM_ALLOWED_CHAT_IDS=12345678,87654321
   TELEGRAM_ADMIN_IDS=12345678
   ```
3. Run the bot locally:
   ```bash
   cd backend
   python -m app.integrations.telegram.bot
   ```

## Supported Commands
- `/start` - Start interaction
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
