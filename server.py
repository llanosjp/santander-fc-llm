"""
FastAPI server — webhook de WhatsApp Cloud API.

Endpoints:
  GET  /health   → health check para DigitalOcean App Platform
  GET  /webhook  → verificación de webhook por Meta
  POST /webhook  → mensajes entrantes de WhatsApp
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Set

from fastapi import BackgroundTasks, FastAPI, Query, Request, Response
from fastapi.responses import PlainTextResponse

from config import Config
from session_store import SessionStore
from whatsapp.client import WhatsAppClient
from whatsapp.webhook import parse_incoming


# ── Estado compartido de la app ───────────────────────────────────────────────

_config: Config
_sessions: SessionStore
_wa_client: WhatsAppClient
_processing_messages: Set[str] = set()  # Deduplicación de mensajes en proceso


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Inicializa los recursos una sola vez al arrancar.
    Config, SessionStore y WhatsAppClient se crean aquí — no en cada request.
    """
    global _config, _sessions, _wa_client
    _config = Config.from_env()
    _sessions = SessionStore(_config)
    _wa_client = WhatsAppClient(_config)
    yield
    # Cleanup al apagar (extensible: cerrar conexiones DB, etc.)


app = FastAPI(
    title="Santander FC LLM — WhatsApp Webhook",
    lifespan=lifespan,
)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Health check para DigitalOcean App Platform."""
    return {"status": "ok", "sessions": _sessions.active_sessions}


@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(default="", alias="hub.mode"),
    hub_verify_token: str = Query(default="", alias="hub.verify_token"),
    hub_challenge: str = Query(default="", alias="hub.challenge"),
):
    """
    Verificación de webhook por Meta.
    Meta envía este GET cuando registrás o actualizás el webhook en el Developer Portal.
    Debés responder con hub.challenge para confirmar que controlás el servidor.
    """
    if (
        hub_mode == "subscribe"
        and hub_verify_token == _config.whatsapp_verify_token
    ):
        return PlainTextResponse(hub_challenge, status_code=200)

    return Response(status_code=403)


async def process_message_background(phone: str, text: str):
    """
    Procesa el mensaje en background sin bloquear el webhook.
    """
    message_id = f"{phone}:{text}"
    
    # Deduplicación: si ya estamos procesando este mensaje, ignorar
    if message_id in _processing_messages:
        return
    
    try:
        _processing_messages.add(message_id)
        
        agent = _sessions.get_or_create(phone, phone_number=phone)
        
        # agent.chat() es bloqueante (SDK de OpenAI es sync).
        # run_in_executor lo corre en un thread pool sin bloquear el event loop.
        loop = asyncio.get_event_loop()
        reply = await loop.run_in_executor(None, agent.chat, text)
        
        _sessions.save_history(phone, agent)
        
        # Enrutamiento: imagen vs texto
        IMAGE_PREFIX = "__IMAGE__:"
        if reply.startswith(IMAGE_PREFIX):
            media_id = reply[len(IMAGE_PREFIX):]
            await _wa_client.send_image(phone, media_id)
        else:
            await _wa_client.send_text(phone, reply)
    
    finally:
        # Limpiar después de procesar
        _processing_messages.discard(message_id)


@app.post("/webhook")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    """
    Mensajes entrantes de WhatsApp via Meta Cloud API.

    Meta SIEMPRE espera HTTP 200 RÁPIDO (<5s). Si tardamos más,
    Meta reintenta el envío causando mensajes duplicados.
    
    Solución: Respondemos 200 inmediatamente y procesamos en background.
    """
    payload = await request.json()
    result = parse_incoming(payload)

    if result is None:
        # Payload ignorado (no es texto, o está vacío) — igual 200 a Meta
        return Response(status_code=200)

    phone, text = result
    
    # Agregar tarea en background y responder inmediatamente
    background_tasks.add_task(process_message_background, phone, text)
    
    # Responder 200 a Meta INMEDIATAMENTE (antes de procesar el mensaje)
    return Response(status_code=200)
