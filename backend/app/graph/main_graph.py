from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import GraphState
from app.graph.nodes import (
    input_router_node,
    speech_node,
    ocr_node,
    intake_node,
    validation_node,
    clarification_node,
    hitl_node,
    order_created_node,
    route_by_input_type,
    route_after_intake,
    route_after_validation,
    route_after_clarification,
    route_after_hitl,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

# In-memory checkpointer for HITL state persistence
_checkpointer = MemorySaver()


def build_graph() -> StateGraph:
    """Build and compile the main LangGraph order processing pipeline."""
    graph = StateGraph(GraphState)

    # Add nodes
    graph.add_node("input_router", input_router_node)
    graph.add_node("speech", speech_node)
    graph.add_node("ocr", ocr_node)
    graph.add_node("intake", intake_node)
    graph.add_node("validation", validation_node)
    graph.add_node("clarification", clarification_node)
    graph.add_node("hitl", hitl_node)
    graph.add_node("order_created", order_created_node)

    # Entry point
    graph.add_edge(START, "input_router")

    # Route from input_router based on input type
    graph.add_conditional_edges("input_router", route_by_input_type, {
        "speech": "speech",
        "ocr": "ocr",
        "intake": "intake",
    })

    # Speech and OCR feed into intake
    graph.add_edge("speech", "intake")
    graph.add_edge("ocr", "intake")

    # After intake, validation
    graph.add_conditional_edges("intake", route_after_intake, {
        "validation": "validation",
        "__end__": END,
    })

    # After validation, clarification
    graph.add_conditional_edges("validation", route_after_validation, {
        "clarification": "clarification",
    })

    # After clarification, HITL or order creation
    graph.add_conditional_edges("clarification", route_after_clarification, {
        "hitl": "hitl",
        "order_created": "order_created",
    })

    # After HITL decision
    graph.add_conditional_edges("hitl", route_after_hitl, {
        "order_created": "order_created",
        "__end__": END,
    })

    # Final node
    graph.add_edge("order_created", END)

    return graph


# Compiled graph singleton with checkpointing for HITL
compiled_graph = build_graph().compile(checkpointer=_checkpointer, interrupt_before=["hitl"])

logger.info("LangGraph main graph compiled successfully")
