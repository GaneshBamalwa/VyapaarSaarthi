"""
Orchestrates the order-intake pipeline (no LangGraph — plain async state machine).

Flow:
  1. Create Order row (PENDING)
  2. Run clarification_agent
     - AMBIGUOUS → save to OrderHITLQueue, return awaiting_approval
     - CLEAR     → run intake_agent, persist items, return completed
  3. resume_after_hitl: human approves → run intake_agent on saved input
"""
from sqlalchemy.orm import Session
from database import Order, OrderItem, OrderHITLQueue, OrderStatus
from graph.main_graph import run_pipeline
from utils.ws_manager import ws_manager


async def process_order(raw_input: str, input_type: str, db: Session) -> dict:
    order = Order(
        raw_input=raw_input,
        input_type=input_type,
        status=OrderStatus.PENDING,
        customer="Unknown",
        confidence=0.0,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    state = await run_pipeline(raw_input, order.id)
    interrupted = state["hitl_needed"]

    if interrupted:
        order.status = OrderStatus.AWAITING_APPROVAL
        clarification = state.get("clarification_result", {})
        hitl_entry = OrderHITLQueue(
            order_id=order.id,
            graph_thread_id=None,
            status="pending",
            reason=clarification.get("data", {}).get("clarification_question", "Ambiguous order"),
            payload={"clarification": clarification},
        )
        db.add(hitl_entry)
        db.commit()
        db.refresh(hitl_entry)
        await ws_manager.emit_hitl_event(hitl_entry.id, "pending", hitl_entry.payload)
    else:
        intake = state.get("intake_result", {}).get("data", {})
        order.customer = intake.get("customer", "Unknown")
        order.confidence = intake.get("confidence", 0.0)
        order.delivery_date = intake.get("delivery_date")
        order.notes = str(intake.get("notes", ""))
        order.status = (
            OrderStatus.COMPLETED
            if state.get("final_status") == "completed"
            else OrderStatus.PENDING
        )
        for item in intake.get("items", []):
            db.add(OrderItem(
                order_id=order.id,
                name=item.get("name", ""),
                quantity=item.get("quantity", 1),
                unit=item.get("unit", "units"),
                price=item.get("price", 0.0),
            ))
        db.commit()

    await ws_manager.emit_order_event(order.id, order.status, {"interrupted": interrupted})

    return {
        "order_id": order.id,
        "status": order.status,
        "interrupted": interrupted,
        "state": state,
    }


async def resume_after_hitl(hitl_id: int, approved: bool,
                             edited_payload: dict, reviewer_notes: str, db: Session) -> dict:
    hitl = db.query(OrderHITLQueue).filter(OrderHITLQueue.id == hitl_id).first()
    if not hitl:
        return {"error": "HITL entry not found"}

    hitl.status = "approved" if approved else "rejected"
    hitl.edited_payload = edited_payload
    hitl.reviewer_notes = reviewer_notes

    order = db.query(Order).filter(Order.id == hitl.order_id).first()

    if not approved:
        order.status = OrderStatus.REJECTED
        db.commit()
        return {"order_id": order.id, "status": "rejected"}

    # Run intake directly on the saved raw input
    from agents import intake_agent
    result = await intake_agent.run(order.raw_input, order.id)

    if result.get("status") == "success":
        intake = result.get("data", {})
        order.customer = intake.get("customer", order.customer)
        order.confidence = intake.get("confidence", order.confidence)
        order.status = OrderStatus.COMPLETED
        for item in intake.get("items", []):
            db.add(OrderItem(
                order_id=order.id,
                name=item.get("name", ""),
                quantity=item.get("quantity", 1),
                unit=item.get("unit", "units"),
                price=item.get("price", 0.0),
            ))
    else:
        order.status = OrderStatus.APPROVED

    db.commit()
    return {"order_id": order.id, "status": order.status}
