from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database.session import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True, nullable=False)
    role = Column(String(50), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    audio_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<ChatMessage id={self.id} session_id={self.session_id} role={self.role}>"
