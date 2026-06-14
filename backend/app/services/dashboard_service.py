from sqlalchemy.orm import Session
from app.repositories.order_repository import OrderRepository
from app.repositories.hitl_repository import HITLRepository
from app.repositories.agent_trace_repository import AgentTraceRepository
from app.models.order import OrderStatus


class DashboardService:
    def __init__(self, db: Session):
        self.order_repo = OrderRepository(db)
        self.hitl_repo = HITLRepository(db)
        self.trace_repo = AgentTraceRepository(db)

    def get_kpis(self) -> dict:
        status_counts = self.order_repo.count_by_status()
        total_orders = sum(status_counts.values())
        pending_approvals = self.hitl_repo.count_pending()
        agent_runs = self.trace_repo.count_total()

        return {
            "orders_processed": total_orders,
            "pending_approvals": pending_approvals,
            "agent_runs": agent_runs,
            "approved_orders": status_counts.get(OrderStatus.APPROVED.value, 0),
            "rejected_orders": status_counts.get(OrderStatus.REJECTED.value, 0),
            "status_breakdown": status_counts,
        }
