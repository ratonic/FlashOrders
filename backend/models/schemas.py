from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Enum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from backend.models.database import Base


# ─── Enumeraciones ─────────────────────────────────────────────────────


class OrderStatus(str, enum.Enum):
    recibido = "recibido"
    confirmado = "confirmado"
    en_preparacion = "en_preparacion"
    listo = "listo"
    entregado = "entregado"
    cancelado = "cancelado"


class ServiceType(str, enum.Enum):
    domicilio = "domicilio"
    recoger = "recoger"


# ─── Tabla: productos del menú ─────────────────────────────────────────


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    category = Column(String(50), nullable=True)
    is_available = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relación con modificadores
    modifiers = relationship("Modifier", back_populates="product")


# ─── Tabla: modificadores de productos ────────────────────────────────


class Modifier(Base):
    __tablename__ = "modifiers"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    name = Column(String(100), nullable=False)
    extra_price = Column(Float, default=0.0, nullable=False)
    group_name = Column(String(50), nullable=True)

    product = relationship("Product", back_populates="modifiers")


# ─── Tabla: pedidos ────────────────────────────────────────────────────


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(Integer, nullable=False)
    customer_phone = Column(String(20), nullable=False, index=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.recibido, nullable=False)
    service_type = Column(Enum(ServiceType), nullable=True)
    delivery_address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    total = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    items = relationship("OrderItem", back_populates="order")


# ─── Tabla: ítems de cada pedido ──────────────────────────────────────


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(100), nullable=False)  # nombre congelado
    unit_price = Column(Float, nullable=False)  # precio congelado
    quantity = Column(Integer, nullable=False, default=1)
    subtotal = Column(Float, nullable=False)

    # Relaciones
    order = relationship("Order", back_populates="items")
    item_modifiers = relationship("OrderItemModifier", back_populates="order_item")


# ─── Tabla: modificadores aplicados a cada ítem ───────────────────────


class OrderItemModifier(Base):
    __tablename__ = "order_item_modifiers"

    id = Column(Integer, primary_key=True, index=True)
    order_item_id = Column(Integer, ForeignKey("order_items.id"), nullable=False)
    modifier_name = Column(String(100), nullable=False)  # nombre congelado
    extra_price = Column(Float, default=0.0, nullable=False)  # precio congelado

    order_item = relationship("OrderItem", back_populates="item_modifiers")
