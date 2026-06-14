import os
import time
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 1. SETUP
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Load .env from this folder first, then fall back to the backend .env.
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv(os.path.join(BASE_DIR, "..", "backend", ".env"))
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    # Fallback or error
    print("⚠️ GEMINI_API_KEY not found in env.")

client = genai.Client(api_key=API_KEY)

app = FastAPI()

# Enable CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Session Store
web_chat_sessions = {}
# Path to the reference PDF Contract. Configurable via env; defaults to a file
# placed next to this script. If absent, the bot still runs (general legal Q&A).
PDF_PATH = os.getenv("CONTRACT_PDF_PATH", os.path.join(BASE_DIR, "contract.pdf"))

def get_or_create_session(session_id: str):
    if session_id in web_chat_sessions:
        return web_chat_sessions[session_id]

    print(f"🆕 Creating new Hybrid Legal Session: {session_id}")
    files_to_upload = []

    # Upload Reference PDF
    if os.path.exists(PDF_PATH):
        try:
            print(f"📄 Uploading Reference PDF: {PDF_PATH}")
            uploaded_file = client.files.upload(file=PDF_PATH)
            files_to_upload.append(uploaded_file)
            print("✅ PDF Uploaded to Gemini Context")
        except Exception as e:
            print(f"⚠️ PDF Upload Failed: {e}")
    else:
        print(f"⚠️ PDF Not Found at {PDF_PATH}")

    # Create Chat Session
    chat_session = client.chats.create(
        model="gemini-2.5-flash-lite",
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are a comprehensive Legal AI Assistant. "
                "Knowledge Sources: "
                "1. The uploaded document (for specific contract/case facts). "
                "2. Your internal database (for general legal principles, definitions, and statutes). "
                "\n\nCapabilities: "
                "- Answer any legal question, even if not mentioned in the doc. "
                "- Compare the uploaded doc against general legal standards. "
                "- Provide summaries and timelines. "
                "\n\nFormatting: Use Markdown for clarity (bolding, headers, lists)."
            )
        ),
        history=[
            types.Content(
                role="user",
                parts=[
                    *[types.Part.from_uri(file_uri=f.uri, mime_type=f.mime_type) for f in files_to_upload],
                    types.Part.from_text(text="Analyze this document and be ready to answer questions.")
                ]
            ),
            types.Content(
                role="model",
                parts=[types.Part.from_text(text="Understood. I have performed the initial analysis of the document and am ready to assist.")]
            )
        ] if files_to_upload else []
    )
    
    web_chat_sessions[session_id] = chat_session
    return chat_session

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    """
    Endpoint for Web Chat Interface
    """
    try:
        data = await request.json()
        user_msg = data.get("message")
        session_id = data.get("sessionId", "guest")

        if not user_msg:
            return JSONResponse({"error": "Message required"}, status_code=400)

        chat_session = get_or_create_session(session_id)
        
        # Send message to Gemini
        response = chat_session.send_message(user_msg)
        return JSONResponse({"reply": response.text})

    except Exception as e:
        print(f"❌ Chat Error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    print(f"⚖️ Legal Bot Server running on http://localhost:8001")
    # Run on Port 8001 to avoid conflict with main.py (8000)
    uvicorn.run(app, host="0.0.0.0", port=8001)