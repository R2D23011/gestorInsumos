from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class HospitalCreate(BaseModel):
    name: str = Field(..., min_length=2)
    state: str = Field(..., min_length=2)
    city: Optional[str] = None
    address: Optional[str] = None
    phone: str = Field(..., min_length=6)


class HospitalResponse(BaseModel):
    id: int
    name: str
    state: str
    city: Optional[str]
    address: Optional[str]
    phone: str
    created_at: datetime

    class Config:
        from_attributes = True


class NeedCreate(BaseModel):
    hospital_id: Optional[int] = None  # Si ya existe el hospital registrado
    # Si no existe, se puede crear en el mismo paso indicando estos datos:
    hospital_name: Optional[str] = None
    hospital_state: Optional[str] = None
    hospital_city: Optional[str] = None
    hospital_address: Optional[str] = None
    hospital_phone: Optional[str] = None

    supply_name: str = Field(..., min_length=2)
    quantity_needed: int = Field(..., gt=0)
    urgency: str = Field(default="media", pattern="^(alta|media|baja)$")
    contact_name: Optional[str] = None
    contact_phone: str = Field(..., min_length=6)


class NeedUpdate(BaseModel):
    quantity_needed: Optional[int] = Field(None, gt=0)
    urgency: Optional[str] = Field(None, pattern="^(alta|media|baja)$")
    status: Optional[str] = Field(None, pattern="^(abierta|cubierta)$")


class NeedResponse(BaseModel):
    id: int
    hospital_id: int
    supply_name: str
    quantity_needed: int
    urgency: str
    contact_name: Optional[str]
    contact_phone: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HospitalWithNeeds(HospitalResponse):
    needs: List[NeedResponse] = []


class PaginatedHospitals(BaseModel):
    items: List[HospitalWithNeeds]
    total: int
    page: int
    page_size: int
    total_pages: int
