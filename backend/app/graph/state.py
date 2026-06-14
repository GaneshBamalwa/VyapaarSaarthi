from typing import TypedDict, Optional, Any, Annotated
import operator


class GraphState(TypedDict):
    """Central state object for the LangGraph order processing pipeline."""

    # Input
    raw_input: str
    input_type: str  # text | voice | image

    # Processing state
    current_node: str
    error: Optional[str]

    # Agent outputs
    transcript: Optional[str]          # from SpeechAgent
    ocr_result: Optional[dict]         # from OCRAgent
    parsed_order: Optional[dict]       # from IntakeAgent
    clarification_result: Optional[dict]  # from ClarificationAgent

    # HITL
    requires_hitl: bool
    hitl_reason: Optional[str]
    hitl_approved: Optional[bool]
    hitl_edited_payload: Optional[dict]

    # Order
    order_id: Optional[int]
    order_status: Optional[str]

    # Metadata
    thread_id: str
    messages: Annotated[list[str], operator.add]
