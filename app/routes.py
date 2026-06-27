from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import distinct, func
from typing import List, Optional
from math import ceil
import logging
from . import models, schemas, database

logger = logging.getLogger("audit_logger")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - AUDIT - %(message)s')
ch.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(ch)

hospitals_router = APIRouter(prefix="/hospitals", tags=["Hospitals"])
needs_router = APIRouter(prefix="/needs", tags=["Needs"])
stats_router = APIRouter(prefix="/stats", tags=["Stats"])


@stats_router.get("/")
def get_stats(db: Session = Depends(database.get_db)):
    """Métricas públicas para la portada: centros activos y necesidades."""
    open_needs = db.query(func.count(models.Need.id)).filter(models.Need.status == "abierta").scalar()
    fulfilled_needs = db.query(func.count(models.Need.id)).filter(models.Need.status == "cubierta").scalar()
    active_hospitals = (
        db.query(func.count(distinct(models.Need.hospital_id)))
        .filter(models.Need.status == "abierta")
        .scalar()
    )
    return {
        "active_hospitals": active_hospitals or 0,
        "open_needs": open_needs or 0,
        "fulfilled_needs": fulfilled_needs or 0,
    }


@hospitals_router.get("/", response_model=schemas.PaginatedHospitals)
def list_hospitals(
    state: Optional[str] = None,
    city: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    db: Session = Depends(database.get_db),
):
    """
    Lista hospitales/clínicas que tienen al menos una necesidad abierta, con paginación.
    Filtrable por estado (entidad federal) y ciudad. Solo se incluyen las necesidades
    abiertas en cada hospital para no abarrotar la respuesta.
    """
    # Solo hospitales con necesidades abiertas (evita listar centros ya cubiertos)
    open_need_exists = (
        db.query(models.Need.id)
        .filter(
            models.Need.hospital_id == models.Hospital.id,
            models.Need.status == "abierta",
        )
        .exists()
    )

    query = db.query(models.Hospital).filter(open_need_exists)

    if state:
        query = query.filter(models.Hospital.state == state)
    if city:
        query = query.filter(models.Hospital.city.ilike(f"%{city}%"))

    total = query.count()
    total_pages = ceil(total / page_size) if total else 0

    hospitals = (
        query.options(selectinload(models.Hospital.needs))
        .order_by(models.Hospital.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Dejar en cada hospital solo las necesidades abiertas, priorizando urgencia
    urgency_order = {"alta": 0, "media": 1, "baja": 2}
    for hospital in hospitals:
        hospital.needs = sorted(
            [n for n in hospital.needs if n.status == "abierta"],
            key=lambda n: (urgency_order.get(n.urgency, 99), n.created_at),
        )

    return {
        "items": hospitals,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@hospitals_router.post("/", response_model=schemas.HospitalResponse)
def create_hospital(payload: schemas.HospitalCreate, db: Session = Depends(database.get_db)):
    """Registra un hospital o clínica."""
    hospital = models.Hospital(**payload.model_dump())
    db.add(hospital)
    db.commit()
    db.refresh(hospital)
    return hospital


@needs_router.get("/", response_model=List[schemas.NeedResponse])
def list_needs(
    state: Optional[str] = None,
    city: Optional[str] = None,
    hospital_id: Optional[int] = None,
    urgency: Optional[str] = None,
    status: Optional[str] = "abierta",
    db: Session = Depends(database.get_db),
):
    """Lista las necesidades reportadas, filtrables por estado, ciudad, hospital, urgencia y estado."""
    query = db.query(models.Need).join(models.Hospital)

    if hospital_id:
        query = query.filter(models.Need.hospital_id == hospital_id)
    if state:
        query = query.filter(models.Hospital.state == state)
    if city:
        query = query.filter(models.Hospital.city.ilike(f"%{city}%"))
    if urgency:
        query = query.filter(models.Need.urgency == urgency)
    if status:
        query = query.filter(models.Need.status == status)

    return query.order_by(models.Need.urgency.desc(), models.Need.created_at.desc()).all()


@needs_router.post("/", response_model=schemas.NeedResponse)
def report_need(payload: schemas.NeedCreate, db: Session = Depends(database.get_db)):
    """
    Reporta una necesidad puntual de un hospital. Permite indicar un hospital ya
    registrado (hospital_id) o registrar uno nuevo en el mismo paso si quien reporta
    está en el sitio y el hospital aún no existe en el sistema.
    """
    hospital_id = payload.hospital_id

    if not hospital_id:
        if not (payload.hospital_name and payload.hospital_state and payload.hospital_phone):
            raise HTTPException(
                status_code=400,
                detail="Debe indicar hospital_id existente o los datos del hospital (nombre, estado, teléfono) para registrarlo.",
            )
        hospital = models.Hospital(
            name=payload.hospital_name,
            state=payload.hospital_state,
            city=payload.hospital_city,
            address=payload.hospital_address,
            phone=payload.hospital_phone,
        )
        db.add(hospital)
        db.commit()
        db.refresh(hospital)
        hospital_id = hospital.id
    else:
        hospital = db.query(models.Hospital).filter(models.Hospital.id == hospital_id).first()
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital no encontrado")

    need = models.Need(
        hospital_id=hospital_id,
        supply_name=payload.supply_name,
        quantity_needed=payload.quantity_needed,
        urgency=payload.urgency,
        contact_name=payload.contact_name,
        contact_phone=payload.contact_phone,
    )
    db.add(need)
    db.commit()
    db.refresh(need)
    logger.info(f"Nueva necesidad reportada: hospital={hospital_id} insumo={payload.supply_name}")
    return need


@needs_router.put("/{need_id}", response_model=schemas.NeedResponse)
def update_need(need_id: int, payload: schemas.NeedUpdate, db: Session = Depends(database.get_db)):
    """
    Actualiza una necesidad: cantidad requerida (p. ej. recibieron una entrega parcial),
    urgencia, o marcarla como cubierta cuando ya se entregó por completo.
    """
    need = db.query(models.Need).filter(models.Need.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail="Necesidad no encontrada")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(need, field, value)

    db.commit()
    db.refresh(need)
    logger.info(f"Necesidad {need_id} actualizada -> cantidad={need.quantity_needed} status={need.status}")
    return need
