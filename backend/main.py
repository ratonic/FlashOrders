from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import get_settings
from backend.models.database import engine, Base
from backend.models import schemas

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
