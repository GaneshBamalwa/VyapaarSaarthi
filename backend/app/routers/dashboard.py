from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/kpis")
async def get_kpis(db: Session = Depends(get_db)):
    service = DashboardService(db)
    return service.get_kpis()
