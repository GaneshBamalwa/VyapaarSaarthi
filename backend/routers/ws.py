import json
import base64
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from utils.ws_manager import ws_manager
from utils import gemini_client as _gc
from utils.gemini_client import _parse_audio_rate, coerce_pcm

router = APIRouter(tags=["WebSocket"])

LIVE_SYSTEM_PROMPT = """You are VyapaarOS, an AI business assistant for Indian MSME owners.
Respond in Hinglish (Hindi-English mix) — match the language the user speaks.
Be concise, warm, and action-oriented. Use ₹ for currency."""


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Agent event feed — broadcasts agent reasoning traces to the UI."""
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep-alive ping
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


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

    client = _gc.get_client()
    if client is None:
        await websocket.send_json({
            "type": "error",
            "data": "Gemini Live requires GEMINI_API_KEY or Vertex AI credentials. Set USE_MOCK_GCP=false."
        })
        await websocket.close()
        return

    await websocket.send_json({"type": "status", "data": "connecting"})

    try:
        from google.genai import types

        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            system_instruction=LIVE_SYSTEM_PROMPT,
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Aoede"  # Options: Puck, Charon, Kore, Fenrir, Aoede
                    )
                )
            ),
        )

        async with client.aio.live.connect(model=_gc.LIVE_MODEL, config=config) as session:
            await websocket.send_json({"type": "status", "data": "connected"})
            await websocket.send_json({"type": "status", "data": "listening"})

            async def _recv_from_gemini():
                """Forward Gemini Live responses to the browser.

                NOTE: session.receive() ends its async iterator after every
                turn_complete (see SDK AsyncSession.receive — it `break`s on
                turn_complete). We must re-subscribe in an outer loop, otherwise
                the model replies exactly once and then goes silent forever.
                """
                try:
                    while True:
                        async for response in session.receive():
                            sc = getattr(response, "server_content", None)
                            if not sc:
                                continue
                            # Audio + text parts
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
                            # Interrupted — model was cut off mid-stream
                            if getattr(sc, "interrupted", False):
                                await websocket.send_json({"type": "interrupted"})
                            # Turn complete → back to listening (iterator ends here;
                            # outer while re-subscribes for the next turn)
                            if getattr(sc, "turn_complete", False):
                                await websocket.send_json({"type": "status", "data": "listening"})
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
                            print(f"[Live] send_realtime_input error: {audio_err}")
                            await websocket.send_json({"type": "error", "data": str(audio_err)})

                    elif msg["type"] == "text":
                        await websocket.send_json({"type": "status", "data": "thinking"})
                        await session.send_client_content(
                            turns=types.Content(role="user", parts=[types.Part(text=msg["data"])]),
                            turn_complete=True,
                        )

                    elif msg["type"] == "end_turn":
                        await session.send_client_content(
                            turns=types.Content(role="user", parts=[types.Part(text=" ")]),
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
