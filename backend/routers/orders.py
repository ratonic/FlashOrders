from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.models.database import get_db
from backend.models.schemas import Order, OrderStatus
from backend.models.pydantic_schemas import InvoiceResponse
from backend.services.invoice_service import get_invoice_data
from backend.services.order_service import get_active_orders, get_order_by_id

router = APIRouter(prefix="/orders", tags=["Pedidos"])


# ─── Obtener todos los pedidos activos ────────────────────────────────
@router.get("/active")
def list_active_orders(db: Session = Depends(get_db)):
    """
    Retorna todos los pedidos que no están entregados ni cancelados.
    El panel kanban consume este endpoint.
    """
    orders = get_active_orders(db)

    result = []
    for order in orders:
        result.append(
            {
                "id": order.id,
                "order_number": order.order_number,
                "customer_phone": order.customer_phone,
                "status": order.status.value
                if hasattr(order.status, "value")
                else order.status,
                "service_type": order.service_type.value
                if hasattr(order.service_type, "value")
                else order.service_type,
                "delivery_address": order.delivery_address,
                "total": order.total,
                "created_at": order.created_at.isoformat()
                if order.created_at
                else None,
                "items_count": len(order.items),
                "items_summary": ", ".join(
                    [f"{item.quantity}x {item.product_name}" for item in order.items]
                ),
            }
        )

    return result


# ─── Cambiar estado de un pedido ──────────────────────────────────────
@router.patch("/{order_id}/status")
def update_order_status(
    order_id: int,
    new_status: OrderStatus,
    db: Session = Depends(get_db),
):
    """
    Cambia el estado del pedido en el kanban.
    Estados: recibido → confirmado → en_preparacion → listo → entregado
    También permite: cancelado
    """
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido {order_id} no encontrado",
        )

    order.status = new_status
    db.commit()
    db.refresh(order)

    return {
        "id": order.id,
        "order_number": order.order_number,
        "status": order.status.value,
        "message": f"Pedido #{order.order_number} actualizado a '{new_status.value}'",
    }


# ─── Obtener factura de un pedido ─────────────────────────────────────
@router.get("/{order_id}/invoice", response_model=InvoiceResponse)
def get_invoice(order_id: int, db: Session = Depends(get_db)):
    """
    Retorna los datos completos de la factura para un pedido.
    El frontend usa estos datos para imprimir via Bluetooth.
    """
    invoice = get_invoice_data(db, order_id)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido {order_id} no encontrado",
        )

    return invoice


# ─── Cancelar un pedido ───────────────────────────────────────────────
@router.patch("/{order_id}/cancel")
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    """Cancela un pedido activo."""
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido {order_id} no encontrado",
        )

    if order.status.value == "entregado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede cancelar un pedido ya entregado",
        )

    order.status = OrderStatus.cancelado
    db.commit()

    return {
        "message": f"Pedido #{order.order_number} cancelado",
        "order_id": order_id,
    }
