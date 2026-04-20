from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ─── Modificadores ─────────────────────────────────────────────────────


class ModifierBase(BaseModel):
    name: str = Field(..., example="Extra queso")
    extra_price: float = Field(default=0.0, example=1500.0)
    group_name: Optional[str] = Field(None, example="Extras")


class ModifierCreate(ModifierBase):
    pass


class ModifierResponse(ModifierBase):
    id: int
    product_id: int

    class Config:
        from_attributes = True


# ─── Productos ─────────────────────────────────────────────────────────


class ProductBase(BaseModel):
    name: str = Field(..., example="Hamburguesa clásica")
    description: Optional[str] = Field(None, example="Carne, lechuga, tomate")
    price: float = Field(..., example=12000.0)
    category: Optional[str] = Field(None, example="Hamburguesas")
    is_available: bool = Field(default=True)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    is_available: Optional[bool] = None


class ProductResponse(ProductBase):
    id: int
    created_at: Optional[datetime] = None
    modifiers: list[ModifierResponse] = []

    class Config:
        from_attributes = True


# ─── Factura ───────────────────────────────────────────────────────────


class InvoiceItemModifier(BaseModel):
    modifier_name: str
    extra_price: float

    class Config:
        from_attributes = True


class InvoiceItem(BaseModel):
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float
    modifications: list[InvoiceItemModifier] = []

    class Config:
        from_attributes = True


class InvoiceResponse(BaseModel):
    order_id: int
    order_number: int
    customer_phone: str
    status: str
    service_type: Optional[str]
    delivery_address: Optional[str]
    items: list[InvoiceItem]
    subtotal_items: float  # suma sin modificadores
    subtotal_modifiers: float  # suma solo modificadores
    total: float
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
