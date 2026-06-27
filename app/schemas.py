from pydantic import BaseModel, Field
from datetime import datetime

# Esquema base para validar entrada de datos
class InventoryUpdate(BaseModel):
    current_stock: int = Field(..., ge=0, description="Stock actual en el hospital")
    required_quantity: int = Field(..., ge=0, description="Cantidad que se necesita urgentemente")

class ReceiveSupply(BaseModel):
    quantity_received: int = Field(..., gt=0, description="Cantidad recibida de donaciones")

# Esquema para responder al cliente (serialización)
class InventoryResponse(BaseModel):
    id: int
    hospital_id: int
    supply_id: int
    current_stock: int
    required_quantity: int
    updated_at: datetime

    class Config:
        from_attributes = True # Permite leer modelos de SQLAlchemy