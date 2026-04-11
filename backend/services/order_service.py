from sqlalchemy.orm import Session
from sqlalchemy import cast, Date
from backend.models.schemas import (
    Order,
    OrderItem,
    OrderItemModifier,
    Modifier,
    Product,
)
from datetime import date


def get_next_order_number(db: Session) -> int:
    today = date.today()
    last_order = (
        db.query(Order)
        .filter(cast(Order.created_at, Date) == today)
        .order_by(Order.order_number.desc())
        .first()
    )
    return 1 if last_order is None else last_order.order_number + 1


def get_modifier_price(
    db: Session,
    product_id: int,
    modifier_name: str,
) -> float:
    """
    Busca el precio real del modificador en la BD.
    Si no lo encuentra retorna 0.0.
    """
    modifier = (
        db.query(Modifier)
        .filter(
            Modifier.product_id == product_id,
            Modifier.name.ilike(modifier_name),  # ilike = sin importar mayúsculas
        )
        .first()
    )
    return modifier.extra_price if modifier else 0.0


def create_order(
    db: Session,
    customer_phone: str,
    ai_result: dict,
) -> Order:
    """
    Crea un pedido completo en la base de datos.
    Consulta y congela los precios reales de productos
    y modificadores en este momento.
    """
    order_number = get_next_order_number(db)

    order = Order(
        order_number=order_number,
        customer_phone=customer_phone,
        service_type=ai_result.get("service_type"),
        delivery_address=ai_result.get("delivery_address"),
        total=0.0,
    )
    db.add(order)
    db.flush()

    total = 0.0

    for item_data in ai_result.get("items", []):
        product_id = item_data.get("product_id")
        quantity = item_data.get("quantity", 1)

        # ── Consultar precio real del producto desde la BD ─────────────
        product = db.query(Product).filter(Product.id == product_id).first()
        unit_price = product.price if product else item_data.get("unit_price", 0.0)

        subtotal = unit_price * quantity

        order_item = OrderItem(
            order_id=order.id,
            product_id=product_id,
            product_name=item_data.get("product_name"),
            unit_price=unit_price,  # precio congelado
            quantity=quantity,
            subtotal=subtotal,
        )
        db.add(order_item)
        db.flush()

        # ── Consultar precio real de cada modificador desde la BD ──────
        for mod_name in item_data.get("modifications", []):
            extra_price = get_modifier_price(
                db=db,
                product_id=product_id,
                modifier_name=mod_name,
            )

            modifier = OrderItemModifier(
                order_item_id=order_item.id,
                modifier_name=mod_name,
                extra_price=extra_price,  # precio congelado
            )
            db.add(modifier)

            subtotal += extra_price * quantity  # suma el extra al subtotal

        # Actualizar subtotal del ítem con los modificadores incluidos
        order_item.subtotal = subtotal
        total += subtotal

    order.total = total
    db.commit()
    db.refresh(order)

    return order


def get_order_by_id(db: Session, order_id: int) -> Order | None:
    return db.query(Order).filter(Order.id == order_id).first()


def get_active_orders(db: Session) -> list[Order]:
    return (
        db.query(Order)
        .filter(Order.status.notin_(["entregado", "cancelado"]))
        .order_by(Order.created_at.desc())
        .all()
    )
