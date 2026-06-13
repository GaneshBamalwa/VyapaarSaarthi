from sqlalchemy import Column, Integer, String, Text
from app.database.session import Base


class NoticeType(Base):
    __tablename__ = "notice_types"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<NoticeType id={self.id} code={self.code}>"
