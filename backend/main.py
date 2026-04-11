from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.config import get_settings
from backend.models.database import engine, Base, get_db
from backend.models import schemas
from backend.services.ai_service import extract_order_from_message
from backend.routers import menu
from backend.routers import whatsapp

settings = get_settings()

# ─── Crear tablas en la base de datos al arrancar ─────────────────────
Base.metadata.create_all(bind=engine)

# ─── Crear la aplicación ───────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    description="Sistema de gestión de pedidos con IA para Ghost Kitchen",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ───────────────────────────────────────────────────────────
app.include_router(menu.router)
app.include_router(whatsapp.router)


# ─── Ruta raíz ─────────────────────────────────────────────────────────
@app.get("/", tags=["Sistema"])
async def root():
    return {
        "sistema": settings.app_name,
        "estado": "activo",
        "entorno": settings.app_env,
        "version": "1.0.0",
    }


# ─── Health check ──────────────────────────────────────────────────────
@app.get("/health", tags=["Sistema"])
async def health_check():
    return {"status": "ok"}


# ─── Prueba del motor de IA ────────────────────────────────────────────
@app.post("/test/ai", tags=["Pruebas"])
async def test_ai(mensaje: str, db: Session = Depends(get_db)):
    """
    Prueba el motor de IA con un mensaje en lenguaje natural.
    """
    result = await extract_order_from_message(
        message=mensaje,
        db=db,
    )
    return result
