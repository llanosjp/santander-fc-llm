"""
Script para registrar el número de WhatsApp con la cuenta de negocio (WABA).
Este es DIFERENTE al registro de verificación de propiedad.

Documentación: https://developers.facebook.com/docs/whatsapp/cloud-api/phone-numbers
"""

import requests
import json

# Configuración
PHONE_NUMBER_ID = "1100744636449614"
ACCESS_TOKEN = "EAAS6e6b8ZCkABRTSPcOLzrRyPy69BnNyar3RLM4s4QzN3ps0EYTouIj6ATkrrKENeB6Ez1FuO8a6MF1lQrFCzLVWk0odwXnyZBIZCTX5fSlbSN6SwMBmu8vLDl1sA2cpc3Yg6mGAmEHkqrxruA6C6c5VQJjLZCBru4ZCvZAfMxBH3CgGEdpxjZCw2uuSiyoCkxs55jbJrY6vFLsSaLwOutNhhFkQ1wSMQRG4kGihNOPT69B9PmxtZCnL0ZAhgSwa62euSydJRxskhJT2PeTAZAZA3DQ"

# Endpoint para registrar el número con WABA
url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/register"

payload = {
    "messaging_product": "whatsapp",
    "pin": "123456"  # PIN de 6 dígitos para proteger el número (inventá uno seguro)
}

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

print("📱 Registrando número con WhatsApp Business Account...")
print(f"   Phone Number ID: {PHONE_NUMBER_ID}")
print()

response = requests.post(url, json=payload, headers=headers)

print("📨 Respuesta de Meta:")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
print()

if response.status_code == 200 and response.json().get("success"):
    print("✅ Número registrado exitosamente con WABA")
    print()
    print("📋 Próximos pasos:")
    print("   1. El número ya está listo para enviar y recibir mensajes")
    print("   2. Probá enviando un mensaje de prueba")
    print()
    print("⚠️  IMPORTANTE: Guardá el PIN 123456 en un lugar seguro")
    print("    Lo vas a necesitar si querés migrar el número a otra WABA")
else:
    print("❌ Error al registrar número")
    print(f"   Status: {response.status_code}")
    print()
    
    error = response.json().get("error", {})
    error_code = error.get("code")
    error_subcode = error.get("error_subcode")
    error_msg = error.get("message")
    
    print(f"   Error code: {error_code}")
    print(f"   Error subcode: {error_subcode}")
    print(f"   Mensaje: {error_msg}")
    print()
    
    # Diagnóstico de errores comunes
    if error_code == 190:
        print("💡 El token es inválido o expiró. Generá uno nuevo en Meta Business Manager.")
    elif error_code == 100:
        print("💡 Parámetro inválido. Verificá que el PHONE_NUMBER_ID sea correcto.")
    elif error_subcode == 2388107:
        print("💡 El número ya está registrado en otra WABA. Necesitás migrarlo primero.")
    elif error_subcode == 33:
        print("💡 El número requiere verificación adicional. Contactá a Meta Support.")
    else:
        print("💡 Revisá la documentación: https://developers.facebook.com/docs/whatsapp/cloud-api/phone-numbers")
