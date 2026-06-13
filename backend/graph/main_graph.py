"""
Order intake pipeline — plain async state machine (no LangGraph dependency).

Flow:
  clarify → [ambiguous? → save HITL to DB, stop] → intake → finalize

HITL resume is handled by intake_service.resume_after_hitl which directly
calls intake_agent after the human approves.
"""
from agents import clarification_agent, intake_agent


async def run_pipeline(raw_input: str, order_id: int) -> dict:
    """
    Returns a state dict with keys:
      clarification_result, hitl_needed, intake_result, final_status
    """
    state = {
        "order_id": order_id,
        "raw_input": raw_input,
        "clarification_result": None,
        "hitl_needed": False,
        "intake_result": None,
        "final_status": None,
    }

    # Step 1: clarify
    clarification = await clarification_agent.run(raw_input, order_id)
    state["clarification_result"] = clarification
    state["hitl_needed"] = clarification.get("data", {}).get("status") == "AMBIGUOUS"

    if state["hitl_needed"]:
        state["final_status"] = "awaiting_approval"
        return state

    # Step 2: intake
    intake = await intake_agent.run(raw_input, order_id)
    state["intake_result"] = intake
    state["final_status"] = "completed" if intake.get("status") == "success" else "failed"

    return state
