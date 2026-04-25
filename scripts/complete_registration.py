"""
Script para completar el registro del número en estado PENDING.
Intenta diferentes métodos según la documentación de Meta.
"""

import requests
import json

# Configuración
PHONE_NUMBER_ID = "1100744636449614"
ACCESS_TOKEN = "EAAS6e6b8ZCkABRTSPcOLzrRyPy69BnNyar3RLM4s4QzN3ps0EYTouIj6ATkrrKENeB6Ez1FuO8a6MF1lQrFCzLVWk0odwXnyZBIZCTX5fSlbSN6SwMBmu8vLDl1sA2cpc3Yg6mGAmEHkqrxruA6C6c5VQJjLZCBru4ZCvZAfMxBH3CgGEdpxjZCw2uuSiyoCkxs55jbJrY6vFLsSaLwOutNhhFkQ1wSMQRG4kGihNOPT69B9PmxtZCnL0ZAhgSwa62euSydJRxskhJT2PeTAZAZA3DQ"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

print("🔄 Intentando completar registro del número...")
print(f"   Phone: +51 960 666 442")
print(f"   ID: {PHONE_NUMBER_ID}")
print()

# Método 1: Register endpoint simplificado
print("📍 Método 1: Register endpoint...")
url1 = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/register"
payload1 = {
    "messaging_product": "whatsapp"
}

response1 = requests.post(url1, json=payload1, headers=headers)
print(f"   Status: {response1.status_code}")
result1 = response1.json()
print(f"   Respuesta: {json.dumps(result1, indent=2, ensure_ascii=False)}")
print()

if response1.status_code == 200 and result1.get("success"):
    print("✅ ¡Registro completado exitosamente!")
    print()
    print("📋 Próximos pasos:")
    print("   1. Probá enviar un mensaje de prueba")
    print("   2. Verificá que el webhook esté recibiendo mensajes")
else:
    # Método 2: Verificar si solo necesita activación
    print("📍 Método 2: Verificando límites de mensajería...")
    url2 = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}"
    params2 = {
        "fields": "messaging_limit_tier"
    }
    
    response2 = requests.get(url2, params=params2, headers=headers)
    result2 = response2.json()
    print(f"   Límite actual: {result2.get('messaging_limit_tier', 'N/A')}")
    print()
    
    if result2.get('messaging_limit_tier'):
        print("✅ El número ya tiene límites asignados - puede estar LISTO")
        print("💡 Intentá enviar un mensaje de prueba directamente")
    else:
        print("❌ El número aún no tiene límites de mensajería")
        print()
        print("🔍 Posibles causas del estado PENDING:")
        print("   1. Meta requiere revisión manual (24-48 horas)")
        print("   2. Falta completar el perfil de negocio")
        print("   3. El número requiere migración desde otra WABA")
        print()
        print("📞 Contactá a Meta Support:")
        print("   https://business.facebook.com/direct-support")
