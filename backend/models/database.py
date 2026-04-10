from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.config import get_settings

settings = get_settings()

# ─── Motor de conexión — compatible con Supabase Pooler ───────────────
# El pooler de Supabase usa PgBouncer en modo transaction.
# Esto requiere desactivar prepared statements con
# prepare_threshold=None y pool_pre_ping=True para detectar
# conexiones caídas automáticamente.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={
        "prepare_threshold": None,  # requerido por PgBouncer
        "options": "-c timezone=America/Bogota",  # zona horaria Colombia
    },
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
