from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import re

from app.database.session import get_db
from app.models.company import CompanyProfile

router = APIRouter(prefix="/api/company", tags=["Company Profile"])

class CompanyProfileSchema(BaseModel):
    company_name: str
    gstin: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]):
        if v:
            # Strip spaces, hyphens, plus signs
            cleaned = re.sub(r'[\s\-\+]', '', v)
            if not cleaned.isdigit() or len(cleaned) < 10 or len(cleaned) > 15:
                raise ValueError("Phone number must contain between 10 and 15 digits.")
        return v
        
    @field_validator('gstin')
    @classmethod
    def validate_gstin(cls, v: Optional[str]):
        if v:
            # Standard GSTIN regex pattern (15 chars)
            pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
            if not re.match(pattern, v.upper()):
                raise ValueError("Invalid GSTIN format. Expected 15-character format (e.g. 29GGGGG1314R9Z6).")
        return v.upper() if v else v

@router.get("/profile", response_model=CompanyProfileSchema)
def get_company_profile(db: Session = Depends(get_db)):
    profile = db.query(CompanyProfile).first()
    if not profile:
        # Return empty default profile instead of 404
        return CompanyProfileSchema(company_name="")
    return profile

@router.post("/profile", response_model=CompanyProfileSchema)
def update_company_profile(profile_data: CompanyProfileSchema, db: Session = Depends(get_db)):
    profile = db.query(CompanyProfile).first()
    if not profile:
        profile = CompanyProfile(**profile_data.model_dump())
        db.add(profile)
    else:
        for key, value in profile_data.model_dump().items():
            setattr(profile, key, value)
    db.commit()
    return profile
