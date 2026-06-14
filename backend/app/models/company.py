from sqlalchemy import Column, Integer, String, Text
from app.database.session import Base

class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False)
    gstin = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
