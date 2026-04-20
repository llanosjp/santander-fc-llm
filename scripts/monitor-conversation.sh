#!/bin/bash
# Script para monitorear conversaciones en tiempo real
# Uso: ./monitor-conversation.sh [phone_number]

set -euo pipefail

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PHONE="${1:-51934055206}"
HISTORY_FILE="/opt/santander-fc-llm/chat_history/${PHONE}.json"

echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}  PulsoAI - Monitor de Conversación${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "Número: ${GREEN}+${PHONE}${NC}"
echo -e "Archivo: ${HISTORY_FILE}"
echo -e "${BLUE}════════════════════════════════════════${NC}\n"

if [ ! -f "$HISTORY_FILE" ]; then
    echo -e "${YELLOW}⏳ Esperando primera interacción...${NC}\n"
fi

# Función para formatear mensajes
format_message() {
    python3 - <<'EOF'
import json
import sys
from datetime import datetime

try:
    data = json.load(sys.stdin)
    
    for i, msg in enumerate(data):
        role = msg.get('role', '?')
        content = msg.get('content') or ''
        tool_calls = msg.get('tool_calls', [])
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        if role == 'user':
            print(f"\033[0;32m[{timestamp}] 👤 Usuario:\033[0m {content}")
        elif role == 'assistant':
            if tool_calls:
                tool_name = tool_calls[0]['function']['name']
                args = tool_calls[0]['function']['arguments']
                print(f"\033[1;33m[{timestamp}] 🤖 Bot:\033[0m TOOL CALL → {tool_name}")
                print(f"         Args: {args}")
            elif content:
                # Truncar si es muy largo
                display = content[:200] + "..." if len(content) > 200 else content
                print(f"\033[0;34m[{timestamp}] 🤖 Bot:\033[0m {display}")
        elif role == 'tool':
            # Truncar resultado
            display = content[:150] + "..." if len(content) > 150 else content
            print(f"\033[0;35m[{timestamp}] ⚙️  Tool result:\033[0m {display}")
        
        print()  # Línea en blanco entre mensajes

except json.JSONDecodeError:
    print("⏳ Esperando datos...", file=sys.stderr)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
EOF
}

# Mostrar historial existente si hay
if [ -f "$HISTORY_FILE" ]; then
    echo -e "${BLUE}📜 Historial previo:${NC}\n"
    cat "$HISTORY_FILE" | format_message
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ Modo seguimiento activado${NC}\n"
fi

# Monitorear cambios en tiempo real
tail -f "$HISTORY_FILE" 2>/dev/null | while read -r line; do
    # Cuando se actualiza el archivo, leerlo completo y mostrar solo el último mensaje
    sleep 0.5
    cat "$HISTORY_FILE" | python3 - <<'EOF'
import json
import sys
from datetime import datetime

try:
    data = json.load(sys.stdin)
    if not data:
        sys.exit(0)
    
    # Mostrar solo el último mensaje
    msg = data[-1]
    role = msg.get('role', '?')
    content = msg.get('content') or ''
    tool_calls = msg.get('tool_calls', [])
    
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    if role == 'user':
        print(f"\033[0;32m[{timestamp}] 👤 Usuario:\033[0m {content}\n")
    elif role == 'assistant':
        if tool_calls:
            tool_name = tool_calls[0]['function']['name']
            args = tool_calls[0]['function']['arguments']
            print(f"\033[1;33m[{timestamp}] 🤖 Bot:\033[0m TOOL CALL → {tool_name}")
            print(f"         Args: {args}\n")
        elif content:
            display = content[:300] + "..." if len(content) > 300 else content
            print(f"\033[0;34m[{timestamp}] 🤖 Bot:\033[0m {display}\n")
    elif role == 'tool':
        display = content[:200] + "..." if len(content) > 200 else content
        print(f"\033[0;35m[{timestamp}] ⚙️  Tool result:\033[0m {display}\n")

except:
    pass
EOF
done
