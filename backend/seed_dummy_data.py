import sys
import os
from datetime import date, timedelta
from sqlalchemy.orm import Session

sys.path.append(os.path.join(os.path.dirname(__file__)))
from app.database.session import SessionLocal, engine, Base
from app.models.order import Order, OrderItem, OrderStatus
from app.models.buyer import Buyer
from app.models.collections import BuyerRiskProfile, CollectionReminder

def seed_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Clean out old data
    db.query(CollectionReminder).delete()
    db.query(BuyerRiskProfile).delete()
    db.query(OrderItem).delete()
    db.query(Order).delete()
    db.query(Buyer).delete()
    db.commit()
    
    phone = "+919674411734"
    today = date.today()
    
    # Create Buyers
    buyers = [
        {"name": "Suresh Enterprises", "phone": phone},
        {"name": "Kaveri Steel", "phone": phone},
        {"name": "Ramesh Traders", "phone": phone},
        {"name": "Ajay Cements", "phone": phone}
    ]
    for b in buyers:
        db.add(Buyer(name=b["name"], phone=b["phone"]))
    db.commit()
    
    # Create Orders
    # Some overdue, some pending, some completed
    orders_data = [
        {
            "customer": "Suresh Enterprises",
            "delivery_date": (today - timedelta(days=15)).strftime("%Y-%m-%d"),
            "status": OrderStatus.COMPLETED,
            "customer_phone": phone,
            "items": [
                {"name": "Steel Rods", "quantity": 100, "price": 85.0},
                {"name": "Cement Bags", "quantity": 50, "price": 450.0}
            ]
        },
        {
            "customer": "Kaveri Steel",
            "delivery_date": (today - timedelta(days=5)).strftime("%Y-%m-%d"),
            "status": OrderStatus.APPROVED,
            "customer_phone": phone,
            "items": [
                {"name": "Iron Sheets", "quantity": 20, "price": 1200.0}
            ]
        },
        {
            "customer": "Ramesh Traders",
            "delivery_date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
            "status": OrderStatus.COMPLETED,
            "customer_phone": phone,
            "items": [
                {"name": "PVC Pipes", "quantity": 200, "price": 45.0}
            ]
        },
        {
            "customer": "Ajay Cements",
            "delivery_date": (today + timedelta(days=3)).strftime("%Y-%m-%d"), # Not overdue
            "status": OrderStatus.PENDING,
            "customer_phone": phone,
            "items": [
                {"name": "White Cement", "quantity": 30, "price": 550.0}
            ]
        },
        # One missing phone number to demonstrate the UI feature
        {
            "customer": "Vikram Hardware",
            "delivery_date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
            "status": OrderStatus.COMPLETED,
            "customer_phone": None,
            "items": [
                {"name": "Nails Box", "quantity": 10, "price": 200.0}
            ]
        }
    ]
    
    for o_data in orders_data:
        order = Order(
            customer=o_data["customer"],
            customer_phone=o_data["customer_phone"],
            delivery_date=o_data["delivery_date"],
            status=o_data["status"],
            raw_input=f"Dummy order for {o_data['customer']}"
        )
        db.add(order)
        db.flush()
        
        for i_data in o_data["items"]:
            item = OrderItem(
                order_id=order.id,
                name=i_data["name"],
                quantity=i_data["quantity"],
                price=i_data["price"],
                unit="unit"
            )
            db.add(item)
            
    db.commit()
    
    # Run risk score update to populate the dashboard risk tiers
    from app.agents.collections.risk_engine import update_all_risk_scores
    update_all_risk_scores(db)
    
    print("Successfully seeded dummy orders and buyers.")
    db.close()

if __name__ == "__main__":
    seed_db()
