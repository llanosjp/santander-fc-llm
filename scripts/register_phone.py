"""
Script para registrar el número de WhatsApp real con Meta.
Se ejecuta UNA SOLA VEZ cuando cambias del número de prueba al real.

Flujo:
1. Ejecutar este script → Meta envía SMS con código de 6 dígitos
2. Recibir el SMS en el teléfono físico
3. Ejecutar verify_phone.py con el código recibido
"""

import requests

# Configuración
PHONE_NUMBER_ID = "1100744636449614"
ACCESS_TOKEN = "EAAS6e6b8ZCkABRcjTgjDHf3oTTlQVSUylACUIHeayBQBZCVZBbZCpHmgNUUvDjMOd7tQZCZCrmZBTmSRVftQZAERZAMdDmgbhxJ3mx9ZAeA9REs1OGo1XVeZA4BzbVihmEcrzCSoODI8jilBFfHfpdfpCSPiyChVj7IIKOpZAfCENafMG88OtWfyxGbs0jPcAgWRO6mpIZBZAAj0cwQVwcedcjXRn2q6nRtqEda0dZCW3XZAD6jAp7muOATeeX3O6tTJNXcigwpNRv9sjhfEeOmr4YOqtsy3"

url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/request_code"

payload = {
    "code_method": "SMS",  # También podés usar "VOICE" si preferís llamada
    "language": "es"
}

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

print("📱 Solicitando código de verificación a Meta...")
print(f"   Número ID: {PHONE_NUMBER_ID}")
print(f"   Método: SMS en español")
print()

response = requests.post(url, json=payload, headers=headers)

print("📨 Respuesta de Meta:")
print(response.json())
print()

if response.status_code == 200:
    print("✅ Código enviado correctamente")
    print("👉 Revisá el SMS en el teléfono registrado")
    print("👉 Luego ejecutá: python scripts/verify_phone.py")
else:
    print("❌ Error al solicitar código")
    print(f"   Status: {response.status_code}")
    print(f"   Respuesta: {response.text}")
