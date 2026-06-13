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
        if "create order" in text or "add order" in text or "place order" in text or "book order" in text:
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
        
        # Numeric date extract like DD-MM-YYYY or YYYY-MM-DD
        numeric_date_match = re.search(r'(\d{2,4}[-/]\d{1,2}[-/]\d{2,4})', text)
        if numeric_date_match:
            return numeric_date_match.group(1)
            
        # Simple date extract for explicit formats like "15 June" or "15th June"
        # Using a list of valid months to avoid matching things like "7 delivery" from "ORD-7 delivery"
        months = r'(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)'
        date_match = re.search(fr'(\d{{1,2}}(?:st|nd|rd|th)?\s+{months})', text, re.IGNORECASE)
        if date_match:
            return date_match.group(1)
            
        # Also support "June 15" format
        date_match_rev = re.search(fr'({months}\s+\d{{1,2}}(?:st|nd|rd|th)?)', text, re.IGNORECASE)
        if date_match_rev:
            return date_match_rev.group(1)
            
        return None

class GeminiIntentParser(IntentParser):
    def parse(self, text: str) -> IntentParseResult:
        from app.core.gemini_client import get_gemini_client
        import json
        
        client = get_gemini_client()
        settings = get_settings()
        
        system_prompt = f"""You are an intent router for a business application.
Available intents: {[i.value for i in IntentType]}
Parse the user's message (which could be in Hindi, English, Hinglish, etc) and map it to an intent.
Extract entities like 'order_id' (integer), 'delivery_date' (ISO format YYYY-MM-DD), 'customer' (string).
Always return valid JSON."""

        from google.genai import types
        import logging
        logger = logging.getLogger(__name__)

        try:
            response = client.models.generate_content(
                model=settings.GEMINI_FLASH_MODEL,
                contents=text,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            data = json.loads(response.text)
            intent_str = data.get("intent", "UNKNOWN")
            
            try:
                intent = IntentType(intent_str)
            except ValueError:
                intent = IntentType.UNKNOWN
                
            # For CREATE_ORDER, we need the raw text so IntakeAgent can parse it
            entities = data.get("entities", {})
            if intent == IntentType.CREATE_ORDER:
                entities["raw_text"] = text
                
            return IntentParseResult(intent=intent, entities=entities)
        except Exception as e:
            logger.error(f"GeminiIntentParser Error: {e}")
            return IntentParseResult(intent=IntentType.UNKNOWN)

def get_intent_parser() -> IntentParser:
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    if os.getenv("TELEGRAM_USE_GEMINI", "false").lower() == "true":
        return GeminiIntentParser()
    return RegexIntentParser()
