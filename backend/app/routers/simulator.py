import random
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.intake_service import IntakeService
from app.agents.collections import CollectionsAgent

router = APIRouter(prefix="/api/simulator", tags=["Simulator"])

_collections_agent = CollectionsAgent()

SAMPLE_ORDERS = [
    "Bhai kal 20 cement bags bhej dena Ramesh ke liye, 300 rupye per bag",
    "50 steel rods Friday tak chahiye, 10mm wale, rate 85 rupaye rod",
    "Sharma ji ke liye 100 bricks aur 5 bags plaster of paris Monday tak. Brick 10 rupye piece, POP 200 per bag",
    "Gupta construction ke liye 200 floor tiles aur 10 bags adhesive, tile 50 rupye each aur adhesive 150 per bag",
    "Kal tak 30 PVC pipes 4 inch diameter chahiye, urgent hai, rate 120 per pipe",
]

AMBIGUOUS_ORDERS = [
    "Wahi maal bhej dena",
    "Same as last time",
    "Thoda aur chahiye",
    "Pehle wali cheez zyada kar dena",
    "Bas wahi order repeat kar do",
]

OVERDUE_INVOICES = [
    {"invoice_id": "INV-2024-001", "customer": "Sharma Constructions", "amount": 45000, "due_days": 5},
    {"invoice_id": "INV-2024-002", "customer": "Gupta Hardware", "amount": 128000, "due_days": 15},
    {"invoice_id": "INV-2024-003", "customer": "Patel Builders", "amount": 250000, "due_days": 30},
]


@router.post("/generate-order")
async def generate_sample_order(db: Session = Depends(get_db)):
    """Generate and process a realistic sample order."""
    text = random.choice(SAMPLE_ORDERS)
    service = IntakeService(db)
    result = await service.process_text_order(text)
    return {"input": text, "result": result}


@router.post("/generate-ambiguous")
async def generate_ambiguous_order(db: Session = Depends(get_db)):
    """Generate an ambiguous order to trigger clarification and HITL."""
    text = random.choice(AMBIGUOUS_ORDERS)
    service = IntakeService(db)
    result = await service.process_text_order(text)
    return {"input": text, "result": result}


@router.post("/generate-overdue")
async def generate_overdue_invoice():
    """Generate a collections reminder for a sample overdue invoice."""
    invoice = random.choice(OVERDUE_INVOICES)
    result = await _collections_agent.invoke(invoice)
    return {"input": invoice, "result": result}
