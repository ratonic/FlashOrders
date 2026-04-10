from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.models.database import get_db
from backend.models.schemas import Product, Modifier
from backend.models.pydantic_schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ModifierCreate,
    ModifierResponse,
)

router = APIRouter(prefix="/menu", tags=["Menú"])


# ─── Obtener todos los productos ───────────────────────────────────────
@router.get("/products", response_model=list[ProductResponse])
def get_products(
    only_available: bool = False,
    db: Session = Depends(get_db),
):
    """
    Retorna todos los productos del menú.
    Usa only_available=true para ver solo los disponibles.
    """
    query = db.query(Product)
    if only_available:
        query = query.filter(Product.is_available == True)
    return query.order_by(Product.category, Product.name).all()


# ─── Obtener un producto por ID ────────────────────────────────────────
@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {product_id} no encontrado",
        )
    return product


# ─── Crear un producto ─────────────────────────────────────────────────
@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Crea un nuevo producto en el menú."""
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


# ─── Actualizar un producto ────────────────────────────────────────────
@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
):
    """Actualiza nombre, precio, disponibilidad u otros campos."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {product_id} no encontrado",
        )

    # Solo actualiza los campos que vienen en la petición
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


# ─── Marcar producto como no disponible ───────────────────────────────
@router.patch("/products/{product_id}/toggle", response_model=ProductResponse)
def toggle_availability(product_id: int, db: Session = Depends(get_db)):
    """Alterna la disponibilidad del producto (agotado / disponible)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {product_id} no encontrado",
        )
    product.is_available = not product.is_available
    db.commit()
    db.refresh(product)
    return product


# ─── Eliminar un producto ──────────────────────────────────────────────
@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Elimina un producto del menú permanentemente."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {product_id} no encontrado",
        )
    db.delete(product)
    db.commit()


# ─── Agregar modificador a un producto ────────────────────────────────
@router.post(
    "/products/{product_id}/modifiers",
    response_model=ModifierResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_modifier(
    product_id: int,
    modifier: ModifierCreate,
    db: Session = Depends(get_db),
):
    """Agrega un modificador a un producto (ej: extra queso, sin cebolla)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {product_id} no encontrado",
        )
    db_modifier = Modifier(product_id=product_id, **modifier.model_dump())
    db.add(db_modifier)
    db.commit()
    db.refresh(db_modifier)
    return db_modifier


# ─── Eliminar un modificador ───────────────────────────────────────────
@router.delete(
    "/products/{product_id}/modifiers/{modifier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_modifier(
    product_id: int,
    modifier_id: int,
    db: Session = Depends(get_db),
):
    modifier = (
        db.query(Modifier)
        .filter(
            Modifier.id == modifier_id,
            Modifier.product_id == product_id,
        )
        .first()
    )
    if not modifier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modificador no encontrado",
        )
    db.delete(modifier)
    db.commit()
