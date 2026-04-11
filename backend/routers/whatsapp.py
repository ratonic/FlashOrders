import hmac
import hashlib
import json
from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any
from backend.config import get_settings
from backend.models.database import get_db
from backend.services.ai_service import extract_order_from_message
from backend.services.order_service import create_order

router = APIRouter(prefix="/webhook", tags=["WhatsApp"])
settings = get_settings()


# ─── Modelo para pruebas desde Swagger ────────────────────────────────
class WhatsAppPayload(BaseModel):
    entry: list[Any]

    class Config:
        json_schema_extra = {
            "example": {
                "entry": [
                    {
                        "changes": [
                            {
                                "value": {
                                    "messages": [
                                        {
                                            "from": "573001234567",
                                            "type": "text",
                                            "text": {
                                                "body": "quiero 2 hamburguesas clásicas con extra queso para llevar"
                                            },
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
        }


async def process_whatsapp_message(
    phone: str,
    message: str,
    db: Session,
):
    """
    Procesa un mensaje de WhatsApp en segundo plano:
    1. Extrae el pedido con IA
    2. Crea el pedido en la base de datos
    """
    try:
        # Paso 1 — Extraer pedido con IA
        ai_result = await extract_order_from_message(
            message=message,
            db=db,
            customer_phone=phone,
        )

        # Paso 2 — Si el pedido es válido, crearlo en BD
        if not ai_result.get("needs_clarification") and ai_result.get("items"):
            order = create_order(
                db=db,
                customer_phone=phone,
                ai_result=ai_result,
            )
            print(f"✅ Pedido #{order.order_number} creado — {phone}")
        else:
            print(
                f"⚠️ Mensaje ambiguo de {phone}: "
                f"{ai_result.get('clarification_message')}"
            )

    except Exception as e:
        print(f"❌ Error procesando mensaje de {phone}: {e}")


# ─── GET — verificación del webhook con Meta ───────────────────────────
@router.get("/whatsapp")
async def verify_webhook(request: Request):
    """
    Meta llama a este endpoint para verificar que el webhook
    es válido antes de empezar a enviar mensajes.
    """
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.whatsapp_verify_token:
        print("✅ Webhook de WhatsApp verificado correctamente")
        return int(challenge)

    raise HTTPException(status_code=403, detail="Token de verificación inválido")


# ─── POST — recepción de mensajes ──────────────────────────────────────
@router.post("/whatsapp")
async def receive_message(
    payload: WhatsAppPayload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Meta envía cada mensaje nuevo a este endpoint.
    Procesamos en segundo plano para responder a Meta
    en menos de 5 segundos (requisito de la API).
    """
    try:
        data = payload.model_dump()
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        # Ignorar eventos que no son mensajes
        if "messages" not in value:
            return {"status": "ignored"}

        message_data = value["messages"][0]

        # Solo procesamos mensajes de texto por ahora
        if message_data["type"] != "text":
            return {"status": "ignored", "reason": "not text"}

        phone = message_data["from"]
        message_text = message_data["text"]["body"]

        print(f"📱 Mensaje de {phone}: {message_text}")

        # Procesar en segundo plano
        background_tasks.add_task(
            process_whatsapp_message,
            phone=phone,
            message=message_text,
            db=db,
        )

        return {"status": "received"}

    except (KeyError, IndexError):
        return {"status": "ignored"}
