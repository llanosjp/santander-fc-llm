"""
Script para ver un resumen de todas las conversaciones de hoy.
"""

import json
import os
from datetime import datetime

HISTORY_DIR = "/opt/santander-fc-llm/chat_history"

def view_all_conversations():
    """Muestra resumen de todas las conversaciones."""
    
    if not os.path.exists(HISTORY_DIR):
        print(f"❌ Directorio no encontrado: {HISTORY_DIR}")
        return
    
    files = [f for f in os.listdir(HISTORY_DIR) if f.endswith('.json')]
    
    if not files:
        print("❌ No hay conversaciones guardadas")
        return
    
    print(f"📊 CONVERSACIONES DE HOY ({datetime.now().strftime('%d/%m/%Y')})")
    print("=" * 80)
    print()
    
    for filename in sorted(files):
        phone = filename.replace('.json', '')
        filepath = os.path.join(HISTORY_DIR, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Contar mensajes
        user_messages = [m for m in data if m.get('role') == 'user']
        assistant_messages = [m for m in data if m.get('role') == 'assistant' and m.get('content')]
        
        # Obtener nombre del usuario si está en el primer mensaje del asistente
        user_name = "Desconocido"
        for msg in data:
            if msg.get('role') == 'assistant' and msg.get('content'):
                content = msg['content']
                if 'Hola' in content and '!' in content:
                    # Extraer nombre del saludo
                    parts = content.split('!')
                    if len(parts) > 0:
                        name_part = parts[0].replace('Hola', '').strip()
                        if name_part:
                            user_name = name_part
                break
        
        print(f"👤 Usuario: +{phone}")
        print(f"   Nombre: {user_name}")
        print(f"   Mensajes: {len(user_messages)} pregunta(s)")
        print()
        
        # Mostrar conversación
        for i, msg in enumerate(data):
            role = msg.get('role')
            content = msg.get('content', '')
            
            if role == 'user':
                print(f"   👤 Usuario: {content}")
            elif role == 'assistant' and content and not content.startswith('Hola'):
                # Limitar a 200 caracteres
                preview = content[:200] + "..." if len(content) > 200 else content
                print(f"   🤖 Bot: {preview}")
            elif role == 'assistant' and msg.get('tool_calls'):
                tools = [tc['function']['name'] for tc in msg['tool_calls']]
                print(f"   🔧 Llamó a: {', '.join(tools)}")
        
        print()
        print("-" * 80)
        print()

if __name__ == "__main__":
    view_all_conversations()
