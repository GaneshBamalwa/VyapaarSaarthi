import pytest
import datetime
from app.communication.parser import RegexIntentParser
from app.communication.intents import IntentType
from app.integrations.telegram.handlers import TelegramFormatter, is_authorized
from app.integrations.telegram.config import get_telegram_config
from app.communication.schemas import CommunicationResponse

def test_intent_detection_create_order():
    parser = RegexIntentParser()
    result = parser.parse("Create order for Ramesh Traders 20 cement bags tomorrow")
    assert result.intent == IntentType.CREATE_ORDER

def test_intent_detection_list_orders():
    parser = RegexIntentParser()
    result = parser.parse("list orders")
    assert result.intent == IntentType.LIST_ORDERS

def test_entity_extraction_and_date_parsing():
    parser = RegexIntentParser()
    result = parser.parse("change ORD-101 delivery to tomorrow")
    assert result.intent == IntentType.UPDATE_DELIVERY_DATE
    assert result.entities.get("order_id") == 101
    
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    assert result.entities.get("delivery_date") == tomorrow

def test_mark_completed_parsing():
    parser = RegexIntentParser()
    result = parser.parse("ORD-123 completed")
    assert result.intent == IntentType.MARK_COMPLETED
    assert result.entities.get("order_id") == 123

def test_response_formatting():
    response = CommunicationResponse(
        intent=IntentType.CREATE_ORDER,
        success=True,
        data={"order_id": 123},
        message="Order Created successfully."
    )
    formatted = TelegramFormatter.format_response(response)
    assert "✅ *Success*" in formatted
    assert "Order Created successfully." in formatted

    error_response = CommunicationResponse(
        intent=IntentType.CREATE_ORDER,
        success=False,
        message="Order ID missing."
    )
    formatted_err = TelegramFormatter.format_response(error_response)
    assert "❌ Order ID missing." in formatted_err

def test_telegram_authorization():
    # If no allowed users, it returns True for dev
    config = get_telegram_config()
    config.TELEGRAM_ALLOWED_CHAT_IDS = "123,456"
    assert is_authorized(123) is True
    assert is_authorized(789) is False
