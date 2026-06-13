import re
import datetime
from typing import Dict, Any, Optional
from app.communication.intents import IntentType
from app.communication.schemas import IntentParseResult
from app.core.config import get_settings

class IntentParser:
    def parse(self, text: str) -> IntentParseResult:
        raise NotImplementedError

class RegexIntentParser(IntentParser):
    def parse(self, text: str) -> IntentParseResult:
        text = text.lower().strip()
        entities: Dict[str, Any] = {}
        
        # Mark completed
        if "completed" in text or "complete" in text or "close" in text:
            match = re.search(r'(?i)ord[ -]?(\d+)', text)
            if match:
                entities["order_id"] = int(match.group(1))
                return IntentParseResult(intent=IntentType.MARK_COMPLETED, entities=entities)

        # Update delivery date
        if "change" in text and "delivery" in text or "update delivery" in text or "move" in text:
            match = re.search(r'(?i)ord[ -]?(\d+)', text)
            if match:
                entities["order_id"] = int(match.group(1))
                # basic date resolution
                date_str = self._resolve_date(text)
                if date_str:
                    entities["delivery_date"] = date_str
                return IntentParseResult(intent=IntentType.UPDATE_DELIVERY_DATE, entities=entities)

        # Search order
        if "search" in text or "find" in text:
            match = re.search(r'(?i)ord[ -]?(\d+)', text)
            if match:
                entities["order_id"] = int(match.group(1))
                return IntentParseResult(intent=IntentType.SEARCH_ORDER, entities=entities)
            # Or by customer name (crude extraction)
            customer_match = re.search(r'(?i)for (.+)', text)
            if customer_match:
                entities["customer"] = customer_match.group(1).strip()
                return IntentParseResult(intent=IntentType.SEARCH_ORDER, entities=entities)

        # List orders
        if text in ["list orders", "show orders", "/orders"]:
            return IntentParseResult(intent=IntentType.LIST_ORDERS)
            
        if "pending" in text or text == "/pending":
            return IntentParseResult(intent=IntentType.VIEW_PENDING)
            
        if "today" in text and "delivery" in text or text == "/today":
            return IntentParseResult(intent=IntentType.VIEW_TODAY)
            
        if "overdue" in text or text == "/overdue":
            return IntentParseResult(intent=IntentType.VIEW_OVERDUE)

        # Create Order (catch all basic pattern for creation)
        if "create order" in text or "add order" in text:
            return IntentParseResult(intent=IntentType.CREATE_ORDER, entities={"raw_text": text})

        return IntentParseResult(intent=IntentType.UNKNOWN)

    def _resolve_date(self, text: str) -> Optional[str]:
        today = datetime.date.today()
        if "tomorrow" in text:
            return (today + datetime.timedelta(days=1)).isoformat()
        if "today" in text:
            return today.isoformat()
        if "monday" in text:
            # find next monday
            days_ahead = 0 - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return (today + datetime.timedelta(days=days_ahead)).isoformat()
        
        # Simple date extract
        date_match = re.search(r'(\d{1,2}\s+[a-zA-Z]+)', text)
        if date_match:
            return date_match.group(1)
        return None

class GeminiIntentParser(IntentParser):
    def parse(self, text: str) -> IntentParseResult:
        # Phase 2 implementation placeholder
        return IntentParseResult(intent=IntentType.UNKNOWN)

def get_intent_parser() -> IntentParser:
    settings = get_settings()
    # For now, default to Regex as per requirements
    return RegexIntentParser()
