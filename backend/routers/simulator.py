"""
Simulator router — generates test data for demos without touching production flows.
"""
import random
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal

router = APIRouter(prefix="/api/simulator", tags=["simulator"])

SAMPLE_ORDERS = [
    "Ramesh bhai, 50 kg atta aur 20 kg chini chahiye kal tak",
    "Suresh Enterprises ko 100 units LED bulb bhejne hain next week",
    "Kaveri Steel Works ke liye 5 ton MS angle 40x40x5 ka order confirm karo",
    "Patel Hardware ko 200 pieces 6-inch nails aur 100 hinges chahiye",
    "Local Shop ke liye ek carton soap bars aur 2 carton shampoo",
]

AMBIGUOUS_ORDERS = [
    "Kuch material bhejdo jaldi",
    "Wahi wala order repeat karo",
    "Thoda aur chahiye",
    "Same as last time",
    "Urgent hai bhai, nikalo",
]

OVERDUE_INVOICES = [
    {"invoice_id": "VYP/2024/0001", "customer": "Ramesh Traders", "amount": 48300.0, "due_days": 45},
    {"invoice_id": "VYP/2024/0002", "customer": "Suresh Enterprises", "amount": 112400.0, "due_days": 22},
    {"invoice_id": "VYP/2024/0003", "customer": "Kaveri Steel Works", "amount": 87650.0, "due_days": 8},
]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/generate-order")
def generate_sample_order():
    return {"text": random.choice(SAMPLE_ORDERS), "input_type": "text"}


@router.post("/generate-ambiguous")
def generate_ambiguous_order():
    return {"text": random.choice(AMBIGUOUS_ORDERS), "input_type": "text"}


@router.post("/generate-overdue")
def generate_overdue_invoice():
    return random.choice(OVERDUE_INVOICES)
