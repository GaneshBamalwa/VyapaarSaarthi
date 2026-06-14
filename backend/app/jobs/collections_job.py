from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import get_settings
from app.core.logging import get_logger
from app.database.session import SessionLocal
from app.agents.collections.agent import CollectionsAgent
from app.agents.collections.risk_engine import update_all_risk_scores

settings = get_settings()
logger = get_logger(__name__)


def create_collections_scheduler() -> AsyncIOScheduler:
    tz = settings.COLLECTIONS_TIMEZONE  # "Asia/Kolkata"
    scheduler = AsyncIOScheduler(timezone=tz)

    @scheduler.scheduled_job(
        "cron",
        hour=settings.COLLECTIONS_RISK_JOB_HOUR,  # 6 AM
        minute=0,
        id="risk_score_update",
    )
    async def job_update_risk_scores():
        logger.info("Collections: starting risk score update")
        try:
            db = SessionLocal()
            try:
                updated = update_all_risk_scores(db)
                logger.info(f"Collections: risk scores updated for {updated} buyers")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Risk score update failed: {e}")

    @scheduler.scheduled_job(
        "cron",
        hour=settings.COLLECTIONS_JOB_HOUR,  # 9 AM
        minute=0,
        id="collections_daily",
    )
    async def job_run_collections():
        logger.info("Collections: starting daily reminders job")
        try:
            agent = CollectionsAgent()
            db = SessionLocal()
            try:
                result = await agent.run_daily_job(db)
                logger.info(f"Collections job complete: {result}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Collections daily job failed: {e}")

    return scheduler
