from app.graph.state import GraphState
from app.agents.intake import IntakeAgent, IntakeInput
from app.agents.clarification import ClarificationAgent
from app.agents.ocr import OCRAgent
from app.agents.speech import SpeechAgent
from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

_intake_agent = IntakeAgent()
_clarification_agent = ClarificationAgent()
_speech_agent = SpeechAgent()
_ocr_agent = OCRAgent()


async def input_router_node(state: GraphState) -> dict:
    """Route input based on input_type."""
    logger.info(f"[Graph] input_router: type={state['input_type']}")
    return {"current_node": "input_router", "messages": [f"Routing {state['input_type']} input"]}


async def speech_node(state: GraphState) -> dict:
    """Transcribe voice input."""
    logger.info("[Graph] speech_node running")
    # In real flow, audio_bytes would be in state
    result = await _speech_agent.invoke(
        {"audio_bytes": state.get("raw_input", b""), "language_code": "hi-IN"}
    )
    if result["status"] == "success":
        return {
            "transcript": result["data"]["transcript"],
            "current_node": "speech",
            "messages": ["Audio transcribed successfully"],
        }
    return {"error": result["error"], "current_node": "speech"}


async def ocr_node(state: GraphState) -> dict:
    """Extract text from image/document."""
    logger.info("[Graph] ocr_node running")
    return {"current_node": "ocr", "messages": ["OCR extraction complete"]}


async def intake_node(state: GraphState) -> dict:
    """Parse order text using IntakeAgent."""
    logger.info("[Graph] intake_node running")

    text = state.get("transcript") or state.get("raw_input", "")
    result = await _intake_agent.invoke(IntakeInput(text=text))

    if result["status"] == "success":
        return {
            "parsed_order": result["data"],
            "current_node": "intake",
            "messages": [f"Order parsed with confidence {result['data'].get('confidence', 0)}"],
        }
    return {"error": result["error"], "current_node": "intake"}


async def validation_node(state: GraphState) -> dict:
    """Validate parsed order and decide if HITL is needed."""
    logger.info("[Graph] validation_node running")

    parsed = state.get("parsed_order", {})
    confidence = parsed.get("confidence", 0)
    requires_hitl = confidence < settings.HITL_CONFIDENCE_THRESHOLD

    return {
        "requires_hitl": requires_hitl,
        "hitl_reason": "low_confidence" if requires_hitl else None,
        "current_node": "validation",
        "messages": [f"Validation: confidence={confidence}, hitl={requires_hitl}"],
    }


async def clarification_node(state: GraphState) -> dict:
    """Check for ambiguity in the order."""
    logger.info("[Graph] clarification_node running")

    text = state.get("transcript") or state.get("raw_input", "")
    result = await _clarification_agent.invoke({"text": text})

    if result["status"] == "success":
        clarification = result["data"]
        is_ambiguous = clarification.get("status") == "AMBIGUOUS"

        requires_hitl = state.get("requires_hitl", False) or is_ambiguous
        hitl_reason = "ambiguous" if is_ambiguous else state.get("hitl_reason")

        return {
            "clarification_result": clarification,
            "requires_hitl": requires_hitl,
            "hitl_reason": hitl_reason,
            "current_node": "clarification",
            "messages": [f"Clarification: {clarification.get('status')}"],
        }
    return {"error": result["error"], "current_node": "clarification"}


async def hitl_node(state: GraphState) -> dict:
    """Human-in-the-loop interrupt node."""
    from langgraph.types import interrupt

    logger.info("[Graph] hitl_node: waiting for human approval")

    # This will pause graph execution and wait for resumption
    human_decision = interrupt(
        {
            "type": "hitl_request",
            "reason": state.get("hitl_reason"),
            "parsed_order": state.get("parsed_order"),
            "clarification": state.get("clarification_result"),
            "thread_id": state.get("thread_id"),
        }
    )

    approved = human_decision.get("approved", False)
    edited_payload = human_decision.get("edited_payload")

    return {
        "hitl_approved": approved,
        "hitl_edited_payload": edited_payload,
        "current_node": "hitl",
        "messages": [f"HITL decision: {'approved' if approved else 'rejected'}"],
    }


async def order_created_node(state: GraphState) -> dict:
    """Finalize and persist the order."""
    logger.info("[Graph] order_created_node running")
    return {
        "order_status": "APPROVED",
        "current_node": "order_created",
        "messages": ["Order created successfully"],
    }


def route_by_input_type(state: GraphState) -> str:
    """Edge: Route based on input type."""
    input_type = state.get("input_type", "text")
    if input_type == "voice":
        return "speech"
    elif input_type == "image":
        return "ocr"
    return "intake"


def route_after_intake(state: GraphState) -> str:
    """Edge: Go to validation after intake."""
    if state.get("error"):
        return "__end__"
    return "validation"


def route_after_validation(state: GraphState) -> str:
    """Edge: After validation, go to clarification."""
    return "clarification"


def route_after_clarification(state: GraphState) -> str:
    """Edge: Decide HITL or proceed to order creation."""
    if state.get("requires_hitl"):
        return "hitl"
    return "order_created"


def route_after_hitl(state: GraphState) -> str:
    """Edge: After HITL decision."""
    if state.get("hitl_approved"):
        return "order_created"
    return "__end__"
