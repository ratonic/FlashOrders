from sqlalchemy.orm import Session
from backend.models.schemas import Order


def get_invoice_data(db: Session, order_id: int) -> dict | None:
    """
    Construye los datos completos de la factura para un pedido.
    Retorna None si el pedido no existe.
    """
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        return None

    items = []
    subtotal_items = 0.0
    subtotal_modifiers = 0.0

    for item in order.items:
        # Calcular subtotal base sin modificadores
        item_base = item.unit_price * item.quantity
        subtotal_items += item_base

        # Recopilar modificadores del ítem
        modifications = []
        item_modifiers_total = 0.0

        for mod in item.item_modifiers:
            modifications.append(
                {
                    "modifier_name": mod.modifier_name,
                    "extra_price": mod.extra_price,
                }
            )
            item_modifiers_total += mod.extra_price * item.quantity

        subtotal_modifiers += item_modifiers_total

        items.append(
            {
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "subtotal": item.subtotal,
                "modifications": modifications,
            }
        )

    return {
        "order_id": order.id,
        "order_number": order.order_number,
        "customer_phone": order.customer_phone,
        "status": order.status.value
        if hasattr(order.status, "value")
        else order.status,
        "service_type": order.service_type.value
        if hasattr(order.service_type, "value")
        else order.service_type,
        "delivery_address": order.delivery_address,
        "items": items,
        "subtotal_items": subtotal_items,
        "subtotal_modifiers": subtotal_modifiers,
        "total": order.total,
        "created_at": order.created_at,
    }
