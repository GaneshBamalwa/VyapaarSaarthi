from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.database.session import SessionLocal
from app.models.expense import ExpenseEntry, MonthlyReportMeta
from app.models.order import Order
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def close_previous_month():
    db = SessionLocal()
    try:
        today = datetime.utcnow()
        if today.month == 1:
            prev_month = f"{today.year - 1}-12"
        else:
            prev_month = f"{today.year}-{today.month - 1:02d}"
            
        meta = db.query(MonthlyReportMeta).filter_by(month=prev_month).first()
        if not meta:
            meta = MonthlyReportMeta(month=prev_month)
            db.add(meta)
            
        if meta.is_closed:
            return
            
        expenses = db.query(ExpenseEntry).filter(ExpenseEntry.month == prev_month, ExpenseEntry.is_deleted == False).all()
        expenses_total = sum(e.amount for e in expenses)
        
        orders = db.query(Order).filter(Order.delivery_date.between(f"{prev_month}-01", f"{prev_month}-31")).all()
        orders_total = 0
        for order in orders:
            if order.items:
                orders_total += sum(i.price * i.quantity for i in order.items if i.price and i.quantity)
                
        meta.orders_total = orders_total
        meta.expenses_total = expenses_total
        meta.net_position = orders_total - expenses_total
        meta.is_closed = True
        meta.report_generated_at = datetime.utcnow().isoformat()
        
        db.commit()
        logger.info(f"[CRON] Month {prev_month} closed and locked.")
    except Exception as e:
        db.rollback()
        logger.error(f"[CRON] Failed to close previous month: {e}")
    finally:
        db.close()

def create_expense_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        close_previous_month,
        trigger=CronTrigger(day=1, hour=0, minute=0),
        id="close_previous_month",
        name="Close Previous Month Expenses",
        replace_existing=True,
    )
    return scheduler
