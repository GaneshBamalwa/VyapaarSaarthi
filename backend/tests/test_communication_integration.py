import pytest
import datetime
from app.communication.schemas import CommunicationRequest
from app.services.communication_service import CommunicationService
from app.database.session import SessionLocal
from app.models.order import Order, OrderStatus
from app.models.buyer import Buyer
from sqlalchemy.orm import Session

# Helper fixture for tests (assuming setup of testing DB)
@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.mark.asyncio
async def test_communication_service_integration(db_session: Session):
    service = CommunicationService(db_session)
    
    # 1. Create a dummy buyer manually or expect the Intake agent to do it
    # We will test the basic routing mechanisms using SEARCH and LIST since CREATE uses IntakeService which invokes Gemini
    # We'll just test that LIST_ORDERS works without crashing.
    
    req_list = CommunicationRequest(message_text="list orders", user_id="123")
    res_list = await service.process_message(req_list)
    
    assert res_list.success is True
    assert "orders" in res_list.data
    
    # Add a mock order directly to DB
    new_order = Order(
        customer="Integration Test Customer",
        items=[{"product": "Cement", "quantity": 10, "price": 100}],
        total_amount=1000,
        status=OrderStatus.PENDING,
        delivery_date=datetime.date.today().isoformat()
    )
    db_session.add(new_order)
    db_session.commit()
    db_session.refresh(new_order)
    
    order_id = new_order.id
    
    # 2. Search for the order
    req_search = CommunicationRequest(message_text=f"search ORD-{order_id}", user_id="123")
    res_search = await service.process_message(req_search)
    assert res_search.success is True
    assert len(res_search.data["orders"]) == 1
    
    # 3. Update delivery date
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    req_update = CommunicationRequest(message_text=f"change ORD-{order_id} delivery to tomorrow", user_id="123")
    res_update = await service.process_message(req_update)
    
    assert res_update.success is True
    assert res_update.data["delivery_date"] == tomorrow
    
    # Verify in DB
    updated_order = db_session.query(Order).filter(Order.id == order_id).first()
    assert updated_order.delivery_date == tomorrow
    
    # 4. Mark complete
    req_complete = CommunicationRequest(message_text=f"mark ORD-{order_id} complete", user_id="123")
    res_complete = await service.process_message(req_complete)
    
    assert res_complete.success is True
    assert res_complete.data["order_id"] == order_id
    
    # Verify in DB
    completed_order = db_session.query(Order).filter(Order.id == order_id).first()
    assert completed_order.status == OrderStatus.COMPLETED
