from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from .database import Base

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, nullable=False)
    supply_id = Column(Integer, nullable=False)
    current_stock = Column(Integer, default=0, nullable=False)
    required_quantity = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class NeedsHistory(Base):
    __tablename__ = "needs_history"

    id = Column(Integer, primary_key=True, index=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id"))
    user_id = Column(Integer, nullable=True) # Quién hizo el cambio
    old_stock = Column(Integer)
    new_stock = Column(Integer)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())