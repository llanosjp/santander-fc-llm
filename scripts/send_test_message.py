"""
Script para enviar un mensaje de prueba via WhatsApp Cloud API.
Útil para verificar que las credenciales y el número están configurados correctamente.
"""

import asyncio
import sys
import os

# Agregar el directorio raíz al path para importar módulos del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from whatsapp.client import WhatsAppClient


async def main():
    """Envía mensaje de prueba al número especificado."""
    
    # Cargar configuración desde .env
    config = Config.from_env()
    
    # Número destino (formato E.164: código país + número sin +)
    # Para Perú: 51 + número de 9 dígitos
    to = "51902735404"
    
    # Mensaje de prueba
    message = """👋 ¡Hola! Soy tu asistente de Santander FC LLM.

Ahora estoy funcionando con el número real de producción.

Probá preguntarme:
• ¿Cómo vamos este mes?
• Dame una gráfica de los últimos 6 meses
• ¿Cuántos créditos se desembolsaron?

¡Estoy listo para ayudarte! 🚀"""
    
    print(f"📱 Enviando mensaje de prueba a +{to}...")
    print(f"📝 Mensaje: {message[:50]}...")
    print()
    
    # Enviar mensaje
    client = WhatsAppClient(config)
    await client.send_text(to, message)
    
    print("✅ Mensaje enviado exitosamente")
    print("👉 Verificá tu WhatsApp")


if __name__ == "__main__":
    asyncio.run(main())
