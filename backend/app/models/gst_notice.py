from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from app.database.session import Base


class GSTNotice(Base):
    __tablename__ = "gst_notices"

    id = Column(Integer, primary_key=True, index=True)
    raw_text = Column(Text, nullable=False)
    translated_hindi = Column(Text, nullable=True)
    action_items = Column(JSON, nullable=True)
    status = Column(String(50), default="unreviewed")  # unreviewed, reviewed
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<GSTNotice id={self.id} status={self.status}>"
