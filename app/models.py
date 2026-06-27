from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    state = Column(String, nullable=False, index=True)  # Estado (entidad federal) de Venezuela
    city = Column(String, nullable=True, index=True)
    address = Column(String, nullable=True)
    phone = Column(String, nullable=False)  # Teléfono general del centro
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    needs = relationship("Need", back_populates="hospital", cascade="all, delete-orphan")


class Need(Base):
    __tablename__ = "needs"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    supply_name = Column(String, nullable=False)
    quantity_needed = Column(Integer, default=1, nullable=False)
    urgency = Column(String, default="media", nullable=False)  # alta | media | baja
    contact_name = Column(String, nullable=True)
    contact_phone = Column(String, nullable=False)  # Teléfono de quien reporta la necesidad
    status = Column(String, default="abierta", nullable=False)  # abierta | cubierta
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    hospital = relationship("Hospital", back_populates="needs")
