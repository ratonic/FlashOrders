from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.config import get_settings

settings = get_settings()

# ─── Motor de conexión a PostgreSQL ────────────────────────────────────
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # verifica la conexión antes de usarla
    pool_size=5,  # máximo 5 conexiones simultáneas
    max_overflow=10,  # hasta 10 conexiones extra en picos
)

# ─── Sesión de base de datos ───────────────────────────────────────────
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ─── Clase base para todos los modelos ────────────────────────────────
Base = declarative_base()


# ─── Dependencia para inyectar la sesión en los endpoints ─────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
