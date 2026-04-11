"""
Cliente HTTP async para enviar mensajes via Meta WhatsApp Cloud API.
Usa httpx para no bloquear el event loop de FastAPI.
"""

import httpx

from config import Config


class WhatsAppClient:
    MAX_CHUNK_SIZE = 4096  # Límite de WhatsApp por mensaje

    def __init__(self, config: Config):
        self.config = config

    async def send_text(self, to: str, text: str) -> None:
        """
        Envía un mensaje de texto al número de destino (formato E.164).
        Divide automáticamente en chunks si supera los 4096 caracteres.
        """
        chunks = self._split(text)
        async with httpx.AsyncClient(timeout=10.0) as client:
            for chunk in chunks:
                await self._send_chunk(client, to, chunk)

    def _split(self, text: str) -> list[str]:
        """Divide el texto en chunks de MAX_CHUNK_SIZE caracteres."""
        if len(text) <= self.MAX_CHUNK_SIZE:
            return [text]
        return [
            text[i : i + self.MAX_CHUNK_SIZE]
            for i in range(0, len(text), self.MAX_CHUNK_SIZE)
        ]

    async def send_image(self, to: str, media_id: str) -> None:
        """Envía una imagen ya subida a Meta usando su media_id."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "image",
            "image": {"id": media_id},
        }
        headers = {
            "Authorization": f"Bearer {self.config.whatsapp_access_token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(
                    self.config.whatsapp_api_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                print(
                    f"⚠️ WhatsApp image error {e.response.status_code}: {e.response.text}"
                )
            except httpx.RequestError as e:
                print(f"⚠️ WhatsApp image request error: {e}")

    async def _send_chunk(
        self, client: httpx.AsyncClient, to: str, text: str
    ) -> None:
        """Envía un único chunk a la Graph API."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
        headers = {
            "Authorization": f"Bearer {self.config.whatsapp_access_token}",
            "Content-Type": "application/json",
        }
        try:
            response = await client.post(
                self.config.whatsapp_api_url,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            # Logueamos el error pero no rompemos el flujo principal
            print(
                f"⚠️ WhatsApp API error {e.response.status_code}: {e.response.text}"
            )
        except httpx.RequestError as e:
            print(f"⚠️ WhatsApp request error: {e}")
