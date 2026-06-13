from sqlalchemy import Column, Integer, String, Float, Text
from app.database.session import Base


class MSMEScheme(Base):
    __tablename__ = "msme_schemes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    min_turnover = Column(Float, default=0.0)
    max_turnover = Column(Float, default=0.0)
    benefit = Column(Text, nullable=True)
    eligibility = Column(Text, nullable=True)
    apply_url = Column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<MSMEScheme id={self.id} name={self.name}>"
