import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from . import models
from .database import engine
from .routes import router

# Configuración básica de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_logger")

# Crear tablas en BD (En producción se usan migraciones como Alembic, pero esto sirve para el MVP)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Logística Humanitaria API",
    description="Backend para gestión de insumos hospitalarios en Venezuela",
    version="1.0.0"
)

# Configurar CORS (Permitir que el frontend web/móvil se conecte)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Ajustar en producción a la URL de tu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para Logs de Peticiones
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Extraer el usuario del header (hasta que implementes JWT)
    user_id = request.headers.get("x-user-id", "anonymous")
    
    # Procesar la petición
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"Method: {request.method} | Path: {request.url.path} | "
        f"Status: {response.status_code} | User: {user_id} | Time: {process_time:.4f}s"
    )
    
    return response

# Incluir las rutas
app.include_router(router)

@app.get("/")
def root():
    return {"message": "API de Logística Humanitaria Operativa"}