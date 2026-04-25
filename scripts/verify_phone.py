"""
Script para verificar el número de WhatsApp con el código recibido por SMS.
Se ejecuta DESPUÉS de register_phone.py.

Uso:
    python scripts/verify_phone.py
    (Te va a pedir el código de 6 dígitos)
"""

import requests

# Configuración (debe ser la MISMA que en register_phone.py)
PHONE_NUMBER_ID = "1100744636449614"
ACCESS_TOKEN = "EAAS6e6b8ZCkABRcjTgjDHf3oTTlQVSUylACUIHeayBQBZCVZBbZCpHmgNUUvDjMOd7tQZCZCrmZBTmSRVftQZAERZAMdDmgbhxJ3mx9ZAeA9REs1OGo1XVeZA4BzbVihmEcrzCSoODI8jilBFfHfpdfpCSPiyChVj7IIKOpZAfCENafMG88OtWfyxGbs0jPcAgWRO6mpIZBZAAj0cwQVwcedcjXRn2q6nRtqEda0dZCW3XZAD6jAp7muOATeeX3O6tTJNXcigwpNRv9sjhfEeOmr4YOqtsy3"

# Pedir código al usuario
print("🔐 Ingresá el código de 6 dígitos que recibiste por SMS:")
code = input("Código: ").strip()

if not code or len(code) != 6 or not code.isdigit():
    print("❌ Error: el código debe tener exactamente 6 dígitos numéricos")
    exit(1)

url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/verify_code"

payload = {
    "code": code
}

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

print()
print(f"✅ Verificando código {code} con Meta...")
print()

response = requests.post(url, json=payload, headers=headers)

print("📨 Respuesta de Meta:")
print(response.json())
print()

if response.status_code == 200 and response.json().get("success"):
    print("🎉 ¡Número registrado exitosamente!")
    print()
    print("📋 Próximos pasos:")
    print("   1. Actualizá las variables en el servidor:")
    print(f"      WHATSAPP_PHONE_NUMBER_ID={PHONE_NUMBER_ID}")
    print(f"      WHATSAPP_ACCESS_TOKEN={ACCESS_TOKEN}")
    print("   2. Reiniciá el servicio: sudo systemctl restart santander-llm")
    print("   3. Probá enviando un mensaje al número real")
else:
    print("❌ Error al verificar código")
    print(f"   Status: {response.status_code}")
    print(f"   Respuesta: {response.text}")
    print()
    print("💡 Posibles causas:")
    print("   - Código incorrecto o expirado (pedí uno nuevo)")
    print("   - El código ya fue usado")
    print("   - El token no tiene permisos suficientes")
