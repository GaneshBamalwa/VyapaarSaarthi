import json
import base64
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core import gemini_client as _gc
from app.core.gemini_client import _parse_audio_rate, coerce_pcm, MockGenAIClient

router = APIRouter(tags=["WebSocket Live"])

LIVE_SYSTEM_PROMPT = """You are VyapaarOS, a female AI business assistant for Indian MSMEs.
Respond in Hinglish (Hindi-English mix) — match the language the user speaks.
Always use female pronouns for yourself (e.g. "Main kar rahi hoon", "Maine order place kar di hai").
Be concise, warm, and action-oriented. Use ₹ for currency.

CRITICAL INSTRUCTIONS:
1. ORDER RULE: If a user places an order but DOES NOT mention the price per product, YOU MUST NOT call the create_order tool. Instead, ask them: "Aur iska price kya lagana hai?". Make sure you know the price for every single product before creating the order.
2. FINANCIAL REPORTING: If the user asks for the expense of the month, order revenue, net position, or overall financial health, YOU MUST use the `get_monthly_report` or `get_expenses` tools. Read out the totals (expenses, revenue, net) and provide a concise summary.
3. PENDING ORDERS: If the user asks to see pending orders, use the `get_orders` tool, check the statuses, and read them out.
4. COLLECTIONS: If asked about overdue invoices, use `get_overdue_invoices`."""



async def _run_mock_live_loop(websocket: WebSocket):
    """Fallback interactive simulator for Gemini Live when in mock mode."""
    await websocket.send_json({"type": "status", "data": "connecting"})
    await asyncio.sleep(0.5)
    await websocket.send_json({"type": "status", "data": "connected"})
    await websocket.send_json({"type": "status", "data": "listening"})

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            if msg["type"] == "close":
                break

            elif msg["type"] == "audio":
                # Silent discard of live audio chunks during mock simulation
                pass

            elif msg["type"] == "text":
                user_text = msg["data"]
                await websocket.send_json({"type": "status", "data": "thinking"})
                
                from app.agents.voice.agent import VoiceAgent
                voice_agent = VoiceAgent()
                intent = voice_agent.detect_intent(user_text)
                
                if intent == "order":
                    from app.database.session import SessionLocal
                    from app.services.intake_service import IntakeService
                    db = SessionLocal()
                    try:
                        service = IntakeService(db)
                        res = await service.process_text_order(user_text)
                        if res.get("status") == "success":
                            response_text = f"Mock Response: Order created successfully for {res['parsed'].get('customer')} (Order #{res['order_id']})."
                        else:
                            response_text = f"Mock Response: Failed to create order. Error: {res.get('error')}"
                    except Exception as order_err:
                        response_text = f"Mock Response: Error placing order: {order_err}"
                    finally:
                        db.close()
                elif intent == "cash_flow" or "expense" in user_text.lower() or "revenue" in user_text.lower():
                    from app.database.session import SessionLocal
                    from app.routers.expenses import get_monthly_report
                    db = SessionLocal()
                    try:
                        import datetime
                        current_month = datetime.datetime.utcnow().strftime("%Y-%m")
                        report = await get_monthly_report(month=current_month, db=db)
                        response_text = f"Mock Response: Is mahine ki total revenue ₹{report.orders_total} aur total expense ₹{report.expenses_total} hai. Net position ₹{report.net_position} hai."
                    except Exception as err:
                        response_text = f"Mock Response: Error fetching report: {err}"
                    finally:
                        db.close()
                elif "pending order" in user_text.lower() or "orders" in user_text.lower():
                    from app.database.session import SessionLocal
                    from app.routers.intake import list_orders
                    db = SessionLocal()
                    try:
                        import datetime
                        current_month = datetime.datetime.utcnow().strftime("%Y-%m")
                        orders_res = await list_orders(month=current_month, db=db)
                        response_text = f"Mock Response: Total {orders_res.total} orders hain is mahine."
                    except Exception as err:
                        response_text = f"Mock Response: Error fetching orders: {err}"
                    finally:
                        db.close()
                else:
                    response_text = f"Mock Response: I received your text '{user_text}'. Intent recognized: {intent}."

                await websocket.send_json({"type": "status", "data": "speaking"})
                await websocket.send_json({"type": "text", "data": response_text})
                await websocket.send_json({"type": "status", "data": "listening"})

            elif msg["type"] == "end_turn":
                await websocket.send_json({"type": "status", "data": "thinking"})
                
                mock_speech = "Ramesh bhai ko 100 kg Steel Rods bhejo"
                from app.database.session import SessionLocal
                from app.services.intake_service import IntakeService
                db = SessionLocal()
                try:
                    service = IntakeService(db)
                    res = await service.process_text_order(mock_speech)
                    response_text = f"Mock Voice Response: Heard '{mock_speech}'. Order created successfully (Order #{res['order_id']})."
                except Exception as e:
                    response_text = f"Mock Voice Response: Heard '{mock_speech}'. Configured GEMINI_API_KEY for real live voice!"
                finally:
                    db.close()

                await websocket.send_json({"type": "status", "data": "speaking"})
                await websocket.send_json({
                    "type": "text",
                    "data": response_text
                })
                await websocket.send_json({"type": "status", "data": "listening"})

    except WebSocketDisconnect:
        pass


@router.websocket("/ws/live")
async def gemini_live_endpoint(websocket: WebSocket):
    """
    Gemini Live bidirectional voice WebSocket.

    Protocol (JSON messages both ways):
      Browser → Backend:
        {"type": "audio", "data": "<base64 PCM 16kHz mono>"}
        {"type": "text",  "data": "typed message"}
        {"type": "end_turn"}
        {"type": "close"}

      Backend → Browser:
        {"type": "audio",   "data": "<base64 MP3/PCM>"}
        {"type": "text",    "data": "transcript or response text"}
        {"type": "status",  "data": "connected|listening|thinking|speaking"}
        {"type": "error",   "data": "error message"}
    """
    await websocket.accept()

    from app.core.config import get_settings
    settings = get_settings()
    
    client = _gc.get_gemini_client()
    # Force API key client with v1alpha for Live API because live streaming models require the alpha endpoint
    if settings.GEMINI_API_KEY:
        from google import genai
        client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options={'api_version': 'v1alpha'}
        )

    if client is None or isinstance(client, MockGenAIClient):
        # Fallback to simulated live chat
        await _run_mock_live_loop(websocket)
        return

    await websocket.send_json({"type": "status", "data": "connecting"})

    try:
        from google.genai import types
        import datetime

        current_time = datetime.datetime.now().strftime("%A, %Y-%m-%d %I:%M %p")
        dynamic_prompt = f"{LIVE_SYSTEM_PROMPT}\n\nThe current date and time is: {current_time}."

        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            system_instruction=types.Content(parts=[types.Part.from_text(text=dynamic_prompt)]),
            tools=[{"function_declarations": [
                types.FunctionDeclaration(
                    name="create_order",
                    description="Create a new business order from a user's spoken request. Use this when the user places an order.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "order_text": types.Schema(type="STRING", description="The exact spoken text or summary of the order to process.")
                        },
                        required=["order_text"]
                    )
                ),
                types.FunctionDeclaration(
                    name="fulfill_order",
                    description="Mark an existing order as COMPLETED or fulfilled.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "order_id": types.Schema(type="INTEGER", description="The numeric ID of the order to fulfill.")
                        },
                        required=["order_id"]
                    )
                ),
                types.FunctionDeclaration(
                    name="get_monthly_report",
                    description="Get the financial report for a specific month, including total revenue from orders, total expenses, net position, and category breakdown. This tells you the overall financial health.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "month": types.Schema(type="STRING", description="The month in YYYY-MM format. If omitted, returns current month.")
                        }
                    )
                ),
                types.FunctionDeclaration(
                    name="get_orders",
                    description="Get a list of all orders, their statuses, and details for a specific month.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "month": types.Schema(type="STRING", description="The month in YYYY-MM format. If omitted, returns current month.")
                        }
                    )
                ),
                types.FunctionDeclaration(
                    name="get_expenses",
                    description="Get a list of all expenses and their details for a specific month.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "month": types.Schema(type="STRING", description="The month in YYYY-MM format. If omitted, returns current month.")
                        }
                    )
                ),
                types.FunctionDeclaration(
                    name="get_overdue_invoices",
                    description="Get a list of all overdue payments/invoices along with their risk tiers.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "min_days": types.Schema(type="INTEGER", description="Minimum days overdue (default 1).")
                        }
                    )
                ),
                types.FunctionDeclaration(
                    name="get_reminder_history",
                    description="Check if any follow-ups or reminders were sent to buyers, and see their statuses.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "buyer_name": types.Schema(type="STRING", description="Optional buyer name to filter history.")
                        }
                    )
                ),
                types.FunctionDeclaration(
                    name="get_collections_stats",
                    description="Get aggregate statistics about the collections system (total overdue amount, reminders sent today, etc).",
                )
            ]}],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Aoede"  # Aoede is a female voice
                    )
                )
            ),
        )

        async with client.aio.live.connect(model=_gc.LIVE_MODEL, config=config) as session:
            await websocket.send_json({"type": "status", "data": "connected"})
            await websocket.send_json({"type": "status", "data": "listening"})

            async def _recv_from_gemini():
                """Forward Gemini Live responses to the browser."""
                try:
                    while True:
                        async for response in session.receive():
                            sc = getattr(response, "server_content", None)
                            if sc:
                                model_turn = getattr(sc, "model_turn", None)
                                if model_turn:
                                    for part in getattr(model_turn, "parts", []):
                                        inline = getattr(part, "inline_data", None)
                                        if inline and inline.data:
                                            rate = _parse_audio_rate(getattr(inline, 'mime_type', ''))
                                            pcm = coerce_pcm(inline.data)
                                            await websocket.send_json({
                                                "type": "audio",
                                                "data": base64.b64encode(pcm).decode(),
                                                "rate": rate,
                                            })
                                        if getattr(part, "text", None):
                                            await websocket.send_json({
                                                "type": "text",
                                                "data": part.text,
                                            })
                                if getattr(sc, "interrupted", False):
                                    await websocket.send_json({"type": "interrupted"})
                                if getattr(sc, "turn_complete", False):
                                    await websocket.send_json({"type": "status", "data": "listening"})
                                    await websocket.send_json({"type": "turn_complete"})
                            
                            # Handle tool calls dynamically from the response root
                            tool_call = getattr(response, "tool_call", None)
                            if tool_call:
                                function_responses = []
                                for fc in tool_call.function_calls:
                                    if fc.name == "create_order":
                                        args = fc.args or {}
                                        text = args.get("order_text", "")
                                        from app.database.session import SessionLocal
                                        from app.services.intake_service import IntakeService
                                        db = SessionLocal()
                                        try:
                                            service = IntakeService(db)
                                            res = await service.process_text_order(text)
                                            response_data = {"status": "success", "order_id": res.get("order_id")}
                                        except Exception as e:
                                            response_data = {"status": "error", "message": str(e)}
                                        finally:
                                            db.close()
                                        
                                        function_responses.append(types.FunctionResponse(
                                            name=fc.name,
                                            id=fc.id,
                                            response=response_data
                                        ))
                                    elif fc.name == "fulfill_order":
                                        args = fc.args or {}
                                        order_id = args.get("order_id")
                                        from app.database.session import SessionLocal
                                        from app.repositories.order_repository import OrderRepository
                                        from app.models.order import OrderStatus
                                        from app.websocket.manager import manager
                                        db = SessionLocal()
                                        try:
                                            repo = OrderRepository(db)
                                            order = repo.update_status(int(order_id), OrderStatus.COMPLETED)
                                            response_data = {"status": "success", "order_id": order_id} if order else {"status": "not_found"}
                                            if order:
                                                await manager.emit_order_event(order.id, order.status.value, {"customer": order.customer})
                                        except Exception as e:
                                            response_data = {"status": "error", "message": str(e)}
                                        finally:
                                            db.close()
                                            
                                        function_responses.append(types.FunctionResponse(
                                            name=fc.name,
                                            id=fc.id,
                                            response=response_data
                                        ))
                                    elif fc.name == "get_monthly_report":
                                        args = fc.args or {}
                                        target_month = args.get("month")
                                        from app.database.session import SessionLocal
                                        from app.routers.expenses import get_monthly_report
                                        db = SessionLocal()
                                        try:
                                            report = await get_monthly_report(month=target_month, db=db)
                                            response_data = report.model_dump(mode="json")
                                        except Exception as e:
                                            response_data = {"status": "error", "message": str(e)}
                                        finally:
                                            db.close()
                                        function_responses.append(types.FunctionResponse(
                                            name=fc.name,
                                            id=fc.id,
                                            response=response_data
                                        ))
                                    elif fc.name == "get_orders":
                                        args = fc.args or {}
                                        target_month = args.get("month")
                                        from app.database.session import SessionLocal
                                        from app.routers.intake import list_orders
                                        db = SessionLocal()
                                        try:
                                            orders_res = await list_orders(month=target_month, db=db)
                                            response_data = {"orders": [o.model_dump(mode="json") for o in orders_res.orders], "total": orders_res.total}
                                        except Exception as e:
                                            response_data = {"status": "error", "message": str(e)}
                                        finally:
                                            db.close()
                                        function_responses.append(types.FunctionResponse(
                                            name=fc.name,
                                            id=fc.id,
                                            response=response_data
                                        ))
                                    elif fc.name == "get_expenses":
                                        args = fc.args or {}
                                        target_month = args.get("month")
                                        from app.database.session import SessionLocal
                                        from app.routers.expenses import list_expenses
                                        db = SessionLocal()
                                        try:
                                            expenses_res = await list_expenses(month=target_month, db=db)
                                            response_data = {"expenses": [{k: str(v) if k in ["due_date", "paid_on"] else v for k, v in e.__dict__.items() if not k.startswith('_')} for e in expenses_res]}
                                        except Exception as e:
                                            response_data = {"status": "error", "message": str(e)}
                                        finally:
                                            db.close()
                                        function_responses.append(types.FunctionResponse(
                                            name=fc.name,
                                            id=fc.id,
                                            response=response_data
                                        ))
                                    elif fc.name == "get_overdue_invoices":
                                        args = fc.args or {}
                                        min_days = args.get("min_days", 1)
                                        from app.database.session import SessionLocal
                                        from app.routers.collections import get_overdue_invoices
                                        db = SessionLocal()
                                        try:
                                            res = await get_overdue_invoices(min_days=min_days, db=db)
                                            response_data = {"overdue_invoices": [o.model_dump(mode="json") for o in res]}
                                        except Exception as e:
                                            response_data = {"status": "error", "message": str(e)}
                                        finally:
                                            db.close()
                                        function_responses.append(types.FunctionResponse(
                                            name=fc.name,
                                            id=fc.id,
                                            response=response_data
                                        ))
                                    elif fc.name == "get_reminder_history":
                                        args = fc.args or {}
                                        buyer_name = args.get("buyer_name", None)
                                        from app.database.session import SessionLocal
                                        from app.routers.collections import get_reminder_history
                                        db = SessionLocal()
                                        try:
                                            res = await get_reminder_history(buyer_name=buyer_name, limit=10, db=db)
                                            response_data = {"reminders": [{k: str(v) if k in ["sent_at"] else v for k, v in r.__dict__.items() if not k.startswith('_')} for r in res]}
                                        except Exception as e:
                                            response_data = {"status": "error", "message": str(e)}
                                        finally:
                                            db.close()
                                        function_responses.append(types.FunctionResponse(
                                            name=fc.name,
                                            id=fc.id,
                                            response=response_data
                                        ))
                                    elif fc.name == "get_collections_stats":
                                        args = fc.args or {}
                                        from app.database.session import SessionLocal
                                        from app.routers.collections import get_collections_stats
                                        db = SessionLocal()
                                        try:
                                            res = await get_collections_stats(db=db)
                                            response_data = res.model_dump(mode="json")
                                        except Exception as e:
                                            response_data = {"status": "error", "message": str(e)}
                                        finally:
                                            db.close()
                                        function_responses.append(types.FunctionResponse(
                                            name=fc.name,
                                            id=fc.id,
                                            response=response_data
                                        ))
                                
                                await session.send_tool_response(
                                    function_responses=function_responses
                                )
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    import traceback
                    print(f"Error in _recv_from_gemini: {e}")
                    traceback.print_exc()
                    await websocket.send_json({"type": "error", "data": str(e)})

            recv_task = asyncio.create_task(_recv_from_gemini())

            try:
                while True:
                    raw = await websocket.receive_text()
                    msg = json.loads(raw)

                    if msg["type"] == "close":
                        break

                    elif msg["type"] == "audio":
                        audio_bytes = base64.b64decode(msg["data"])
                        rate = msg.get("rate", 16000)
                        try:
                            await session.send_realtime_input(
                                audio=types.Blob(data=audio_bytes, mime_type=f"audio/pcm;rate={rate}")
                            )
                        except Exception as audio_err:
                            await websocket.send_json({"type": "error", "data": str(audio_err)})

                    elif msg["type"] == "text":
                        await websocket.send_json({"type": "status", "data": "thinking"})
                        await session.send_client_content(
                            turns=types.Content(role="user", parts=[types.Part.from_text(text=msg["data"])]),
                            turn_complete=True,
                        )

                    elif msg["type"] == "end_turn":
                        await session.send_client_content(
                            turn_complete=True,
                        )

            finally:
                recv_task.cancel()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "data": str(e)})
        except Exception:
            pass
