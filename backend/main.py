import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import init_db
from data.seed import seed_database
from routers import voice, gst, compliance, hitl, ws
from routers.dashboard import router as dashboard_router
from routers.intake import router as intake_router
from routers.ocr import router as ocr_router
from routers.speech_new import router as speech_new_router
from routers.order_collections import router as collections_router
from routers.simulator import router as simulator_router
from routers.agents_traces import router as traces_router

app = FastAPI(
    title="VyapaarOS API",
    description="AI-powered MSME business management — voice, GST, compliance agents",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static/audio", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(voice.router)
app.include_router(gst.router)
app.include_router(dashboard_router)
app.include_router(compliance.router)
app.include_router(hitl.router)
app.include_router(ws.router)
app.include_router(intake_router)
app.include_router(ocr_router)
app.include_router(speech_new_router)
app.include_router(collections_router)
app.include_router(simulator_router)
app.include_router(traces_router)


@app.on_event("startup")
async def startup():
    init_db()
    seed_database()
    print("[VyapaarOS] API ready at http://localhost:8000")
    print("[VyapaarOS] Docs at http://localhost:8000/docs")
    print(f"[VyapaarOS] GCP mock mode: {os.getenv('USE_MOCK_GCP', 'true')}")


@app.get("/")
async def root():
    return {"status": "ok", "app": "VyapaarOS", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy", "mock_gcp": os.getenv("USE_MOCK_GCP", "true") == "true"}
