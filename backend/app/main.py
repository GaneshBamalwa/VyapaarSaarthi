from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.database.session import init_db
from app.database.seed import seed_database
from app.websocket.manager import manager
from app.routers import (
    dashboard, intake, ocr, speech, collections, hitl, simulator, agents,
    gst, compliance, voice, ws_live, whatsapp, communication, expenses, company
)
from app.jobs.collections_job import create_collections_scheduler
from app.jobs.expense_job import create_expense_scheduler

configure_logging()
settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    init_db()
    logger.info("Database initialized")
    try:
        seed_database()
        logger.info("Database seeded successfully")
    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
    # Start collections scheduler
    scheduler = create_collections_scheduler()
    scheduler.start()
    app.state.collections_scheduler = scheduler
    logger.info("Collections scheduler started")
    
    expense_scheduler = create_expense_scheduler()
    expense_scheduler.start()
    app.state.expense_scheduler = expense_scheduler
    logger.info("Expense scheduler started")
    
    yield
    app.state.collections_scheduler.shutdown(wait=False)
    app.state.expense_scheduler.shutdown(wait=False)
    logger.info("Shutting down")



app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-native operating system for Indian MSMEs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static/audio", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Register routers
app.include_router(dashboard.router)
app.include_router(intake.router)
app.include_router(ocr.router)
app.include_router(speech.router)
app.include_router(collections.router)
app.include_router(hitl.router)
app.include_router(simulator.router)
app.include_router(agents.router)
app.include_router(gst.router)
app.include_router(compliance.router)
app.include_router(voice.router)
app.include_router(ws_live.router)
app.include_router(whatsapp.router)
app.include_router(communication.router)
app.include_router(expenses.router)
app.include_router(company.router)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "ws_connections": manager.connection_count,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for ping/pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
