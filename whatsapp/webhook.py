"""
Parser de payloads entrantes de Meta WhatsApp Cloud API.
Solo extrae mensajes de texto — ignora imágenes, audio, stickers, etc.
"""


def parse_incoming(payload: dict) -> tuple[str, str] | None:
    """
    Extrae (phone_e164, text) del payload POST de Meta.

    Retorna None si:
    - El payload no contiene mensajes
    - El mensaje no es de tipo texto
    - Faltan campos obligatorios

    Meta siempre espera HTTP 200, así que el caller debe responder 200
    independientemente de lo que retorne esta función.
    """
    try:
        entry = payload.get("entry", [])
        if not entry:
            return None

        changes = entry[0].get("changes", [])
        if not changes:
            return None

        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return None

        message = messages[0]

        # Solo procesamos texto — ignoramos silenciosamente el resto
        if message.get("type") != "text":
            return None

        phone = message.get("from")
        text = message.get("text", {}).get("body", "").strip()

        if not phone or not text:
            return None

        return phone, text

    except Exception:
        # Nunca explotar ante un payload inesperado de Meta
        return None
