from groq import AsyncGroq
from backend.config import get_settings
from sqlalchemy.orm import Session
from backend.models.schemas import Product
import json

settings = get_settings()
client = AsyncGroq(api_key=settings.groq_api_key)

# Modelo gratuito de Groq — excelente para extracción de pedidos
GROQ_MODEL = "llama-3.3-70b-versatile"


def get_menu_context(db: Session) -> str:
    """
    Obtiene todos los productos disponibles de la BD
    y los formatea como contexto para el prompt de IA.
    """
    products = db.query(Product).filter(Product.is_available == True).all()

    if not products:
        return "[]"

    menu_items = []
    for p in products:
        item = {
            "id": p.id,
            "nombre": p.name,
            "precio": p.price,
            "categoria": p.category,
            "modificadores": [
                {
                    "nombre": m.name,
                    "precio_extra": m.extra_price,
                    "grupo": m.group_name,
                }
                for m in p.modifiers
            ],
        }
        menu_items.append(item)

    return json.dumps(menu_items, ensure_ascii=False, indent=2)


async def extract_order_from_message(
    message: str,
    db: Session,
    customer_phone: str = "",
) -> dict:
    """
    Recibe un mensaje de WhatsApp en lenguaje natural y
    devuelve un pedido estructurado en formato JSON.

    Retorna:
    - items: lista de productos pedidos con precios
    - service_type: 'domicilio' o 'recoger'
    - delivery_address: dirección si aplica
    - needs_clarification: True si el mensaje es ambiguo
    - clarification_message: pregunta para el cliente
    """
    menu_context = get_menu_context(db)

    system_prompt = f"""Eres el asistente de pedidos de Ghost Kitchen.
Tu única tarea es extraer la información del pedido del mensaje del cliente
y responder ÚNICAMENTE con un JSON válido, sin explicaciones adicionales.

MENÚ DISPONIBLE:
{menu_context}

REGLAS:
1. Solo acepta productos que existan en el menú.
2. Detecta cantidades en texto ('dos', 'tres') y números ('2', '3').
3. Detecta modificaciones: 'sin cebolla', 'extra queso', 'doble carne'.
4. Si el menú está vacío o el producto no existe, marca needs_clarification como true.
5. Determina si es domicilio o para recoger según el mensaje.

RESPONDE SOLO CON ESTE JSON:
{{
  "items": [
    {{
      "product_name": "nombre exacto del producto",
      "product_id": 1,
      "quantity": 1,
      "unit_price": 0.0,
      "modifications": ["sin cebolla"]
    }}
  ],
  "service_type": "domicilio",
  "delivery_address": null,
  "needs_clarification": false,
  "clarification_message": null
}}"""

    response = await client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        temperature=0.1,
        max_tokens=1000,
    )

    raw = response.choices[0].message.content.strip()

    # Limpiar posibles caracteres extra antes del JSON
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    result = json.loads(raw)
    return result


async def generate_clarification_response(question: str) -> str:
    """
    Genera un mensaje amigable para pedirle aclaración al cliente.
    """
    response = await client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un asistente amigable de una cocina virtual. "
                    "Redacta mensajes cortos y amables en español para "
                    "pedirle aclaración a un cliente sobre su pedido. "
                    "Máximo 2 oraciones."
                ),
            },
            {"role": "user", "content": question},
        ],
        temperature=0.7,
        max_tokens=150,
    )
    return response.choices[0].message.content
