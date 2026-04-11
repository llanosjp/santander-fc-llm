"""
Configuración centralizada del agente.
Todos los valores configurables en un solo lugar.
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # API Santander (Power Automate)
    api_url: str = ""

    # LLM
    openai_api_key: str = ""
    model: str = "gpt-4o"
    temperature: float = 0.1
    timeout_llm: int = 30
    timeout_api: int = 15

    # WhatsApp Cloud API
    # PHONE_NUMBER_ID: en modo prueba es el ID del número de test de Meta.
    # Cuando llegue el número real, solo cambiás esta variable de entorno.
    whatsapp_phone_number_id: str = ""
    whatsapp_access_token: str = ""
    # Token secreto que inventás vos — Meta lo usa para verificar el webhook
    whatsapp_verify_token: str = ""
    # Versión de la Graph API — actualizá cuando Meta deprecate la actual
    whatsapp_api_version: str = "v19.0"

    @property
    def whatsapp_api_url(self) -> str:
        """URL base para enviar mensajes. Cambia sola cuando cambia phone_number_id."""
        return (
            f"https://graph.facebook.com/{self.whatsapp_api_version}"
            f"/{self.whatsapp_phone_number_id}/messages"
        )

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            api_url=os.environ["SANTANDER_API_URL"],
            openai_api_key=os.environ["OPENAI_API_KEY"],
            model=os.environ.get("MODEL", "gpt-4o"),
            whatsapp_phone_number_id=os.environ["WHATSAPP_PHONE_NUMBER_ID"],
            whatsapp_access_token=os.environ["WHATSAPP_ACCESS_TOKEN"],
            whatsapp_verify_token=os.environ["WHATSAPP_VERIFY_TOKEN"],
            whatsapp_api_version=os.environ.get("WHATSAPP_API_VERSION", "v19.0"),
        )
