"""
Script para verificar el estado actual del número de WhatsApp.
Muestra información sobre el registro, calidad, límites, etc.
"""

import requests
import json

# Configuración
PHONE_NUMBER_ID = "1100744636449614"
ACCESS_TOKEN = "EAAS6e6b8ZCkABRTSPcOLzrRyPy69BnNyar3RLM4s4QzN3ps0EYTouIj6ATkrrKENeB6Ez1FuO8a6MF1lQrFCzLVWk0odwXnyZBIZCTX5fSlbSN6SwMBmu8vLDl1sA2cpc3Yg6mGAmEHkqrxruA6C6c5VQJjLZCBru4ZCvZAfMxBH3CgGEdpxjZCw2uuSiyoCkxs55jbJrY6vFLsSaLwOutNhhFkQ1wSMQRG4kGihNOPT69B9PmxtZCnL0ZAhgSwa62euSydJRxskhJT2PeTAZAZA3DQ"

# Endpoint para obtener información del número
url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}"

params = {
    "fields": "verified_name,code_verification_status,display_phone_number,quality_rating,messaging_limit_tier,account_mode,certificate,is_pin_enabled,name_status,new_name_status,status"
}

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

print("📱 Consultando estado del número...")
print(f"   Phone Number ID: {PHONE_NUMBER_ID}")
print()

response = requests.get(url, params=params, headers=headers)

print("📨 Respuesta de Meta:")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
print()

if response.status_code == 200:
    data = response.json()
    
    print("=" * 60)
    print("INFORMACIÓN DEL NÚMERO")
    print("=" * 60)
    
    print(f"Número mostrado: {data.get('display_phone_number', 'N/A')}")
    print(f"Nombre verificado: {data.get('verified_name', 'N/A')}")
    print(f"Estado: {data.get('status', 'N/A')}")
    print(f"Modo de cuenta: {data.get('account_mode', 'N/A')}")
    print(f"Estado de verificación: {data.get('code_verification_status', 'N/A')}")
    print(f"Estado del nombre: {data.get('name_status', 'N/A')}")
    print(f"Calificación de calidad: {data.get('quality_rating', 'N/A')}")
    print(f"Límite de mensajería: {data.get('messaging_limit_tier', 'N/A')}")
    print(f"PIN habilitado: {data.get('is_pin_enabled', 'N/A')}")
    print()
    
    # Diagnóstico
    account_mode = data.get('account_mode', '')
    status = data.get('status', '')
    
    if account_mode == 'SANDBOX':
        print("⚠️  El número está en modo SANDBOX (prueba)")
        print("    Necesitás aprobación de Meta para producción")
    elif status == 'UNVERIFIED':
        print("⚠️  El número NO está verificado")
        print("    Ejecutá register_phone.py para verificarlo")
    elif status == 'CONNECTED':
        print("✅ El número está CONECTADO y listo para usar")
    elif status == 'DISCONNECTED':
        print("❌ El número está DESCONECTADO")
        print("    Puede estar registrado en otra WABA")
    else:
        print(f"ℹ️  Estado: {status}")
        
else:
    print("❌ Error al consultar estado")
    print(f"   Status: {response.status_code}")
    
    error = response.json().get("error", {})
    print(f"   Código: {error.get('code')}")
    print(f"   Mensaje: {error.get('message')}")
