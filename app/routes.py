from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, database

router = APIRouter(prefix="/inventory", tags=["Inventory"])

@router.get("/", response_model=List[schemas.InventoryResponse])
def get_inventory(
    hospital_id: Optional[int] = None,
    only_urgent: bool = False,
    db: Session = Depends(database.get_db)
):
    """Obtiene el inventario con filtros dinámicos para la web."""
    query = db.query(models.Inventory)
    
    # Filtrar por un hospital específico
    if hospital_id:
        query = query.filter(models.Inventory.hospital_id == hospital_id)
    
    # Mostrar solo los insumos donde la necesidad es mayor al stock (Urgencias)
    if only_urgent:
        query = query.filter(models.Inventory.required_quantity > 0)
        
    return query.all()

@router.put("/{inventory_id}", response_model=schemas.InventoryResponse)
def update_inventory(
    inventory_id: int, 
    payload: schemas.InventoryUpdate, 
    db: Session = Depends(database.get_db),
    x_user_id: str = Header(default="unknown", description="ID del usuario simulado por Header")
):
    """Actualiza los niveles de stock y necesidades de un insumo."""
    db_item = db.query(models.Inventory).filter(models.Inventory.id == inventory_id).first()
    
    if not db_item:
        raise HTTPException(status_code=404, detail="Registro de inventario no encontrado")

    # Guardar estado anterior para el historial (Auditoría)
    history_log = models.NeedsHistory(
        inventory_id=db_item.id,
        user_id=int(x_user_id) if x_user_id.isdigit() else None,
        old_stock=db_item.current_stock,
        new_stock=payload.current_stock
    )
    db.add(history_log)

    # Actualizar valores
    db_item.current_stock = payload.current_stock
    db_item.required_quantity = payload.required_quantity

    db.commit()
    db.refresh(db_item)
    return db_item

@router.post("/{inventory_id}/receive", response_model=schemas.InventoryResponse)
def mark_as_received(
    inventory_id: int, 
    payload: schemas.ReceiveSupply, 
    db: Session = Depends(database.get_db),
    x_user_id: str = Header(default="unknown")
):
    """Suma la cantidad recibida al stock actual y resta de la necesidad."""
    db_item = db.query(models.Inventory).filter(models.Inventory.id == inventory_id).first()
    
    if not db_item:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    new_stock = db_item.current_stock + payload.quantity_received
    new_required = max(0, db_item.required_quantity - payload.quantity_received)

    # Auditoría
    history_log = models.NeedsHistory(
        inventory_id=db_item.id,
        user_id=int(x_user_id) if x_user_id.isdigit() else None,
        old_stock=db_item.current_stock,
        new_stock=new_stock
    )
    db.add(history_log)

    db_item.current_stock = new_stock
    db_item.required_quantity = new_required

    db.commit()
    db.refresh(db_item)
    return db_item