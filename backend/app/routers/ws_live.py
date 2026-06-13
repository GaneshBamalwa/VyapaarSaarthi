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

CRITICAL ORDER RULE: If a user places an order but DOES NOT mention the price per product, YOU MUST NOT call the create_order tool. Instead, ask them: "Aur iska price kya lagana hai?" (Or similar followup). Make sure you know the price for every single product before creating the order."""



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
                else:
                    response_text = f"Mock Response: I received your text '{user_text}'."

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
                            if not sc:
                                continue
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
                            
                            # Handle tool calls dynamically
                            tool_call = getattr(sc, "tool_call", None)
                            if tool_call:
                                function_responses = []
                                for fc in tool_call.function_calls:
                                    if fc.name == "create_order":
                                        args = fc.args
                                        text = args.get("order_text")
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
                                        
                                        function_responses.append(types.Part.from_function_response(
                                            name=fc.name,
                                            response=response_data
                                        ))
                                    elif fc.name == "fulfill_order":
                                        args = fc.args
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
                                            
                                        function_responses.append(types.Part.from_function_response(
                                            name=fc.name,
                                            response=response_data
                                        ))
                                
                                await session.send_client_content(
                                    turns=types.Content(
                                        parts=function_responses
                                    ),
                                    turn_complete=True
                                )
                except asyncio.CancelledError:
                    raise
                except Exception as e:
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
                            turns=types.Content(role="user", parts=[types.Part(text=msg["data"])]),
                            turn_complete=True,
                        )

                    elif msg["type"] == "end_turn":
                        await session.send_client_content(
                            turns=types.Content(role="user", parts=[types.Part.from_text(text=" ")]),
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
