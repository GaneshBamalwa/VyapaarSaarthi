from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import Optional
from app.models.hitl_queue import HITLQueue, HITLStatus


class HITLRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        payload: dict,
        order_id: Optional[int] = None,
        graph_thread_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> HITLQueue:
        item = HITLQueue(
            order_id=order_id,
            graph_thread_id=graph_thread_id,
            status=HITLStatus.PENDING,
            reason=reason,
            payload=payload,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_by_id(self, hitl_id: int) -> Optional[HITLQueue]:
        return self.db.query(HITLQueue).filter(HITLQueue.id == hitl_id).first()

    def list_pending(self) -> list[HITLQueue]:
        return (
            self.db.query(HITLQueue)
            .filter(HITLQueue.status == HITLStatus.PENDING)
            .order_by(desc(HITLQueue.created_at))
            .all()
        )

    def list_all(self, limit: int = 50) -> tuple[list[HITLQueue], int]:
        total = self.db.query(HITLQueue).count()
        items = (
            self.db.query(HITLQueue)
            .order_by(desc(HITLQueue.created_at))
            .limit(limit)
            .all()
        )
        return items, total

    def resolve(
        self,
        hitl_id: int,
        status: HITLStatus,
        edited_payload: Optional[dict] = None,
        reviewer_notes: Optional[str] = None,
    ) -> Optional[HITLQueue]:
        item = self.get_by_id(hitl_id)
        if item:
            item.status = status
            item.edited_payload = edited_payload
            item.reviewer_notes = reviewer_notes
            item.resolved_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(item)
        return item

    def count_pending(self) -> int:
        return (
            self.db.query(HITLQueue)
            .filter(HITLQueue.status == HITLStatus.PENDING)
            .count()
        )
