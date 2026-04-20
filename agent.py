"""
Loop de function calling con GPT-4o.
Gestiona el historial de conversación y ejecuta las tools automáticamente.
"""

from datetime import datetime
from openai import OpenAI, APITimeoutError, APIError

from config import Config
from tools.schemas import TOOLS
from tools.registry import dispatch


def _build_system_prompt() -> str:
    periodo_actual = datetime.now().strftime("%Y%m")
    return f"""Eres un asistente comercial de Santander.
Tu rol es responder preguntas sobre KPIs de colocación de créditos.

Los datos disponibles son:
- NRO_CREDITOS: número de créditos colocados
- MONTO: monto total colocado (en soles)
- MONTO_PROMEDIO: ticket promedio por crédito (ya calculado)
- TEA_PROMEDIO: Tasa Efectiva Anual (en porcentaje, ya calculada)
- TCEA_PROMEDIO: Tasa de Costo Efectivo Anual (en porcentaje, ya calculada)
- PLAZO_PROMEDIO: plazo promedio en días (ya calculado)
- CANT_HABIL_PEND: días hábiles restantes para cierre de mes (MUESTRA ESTE VALOR SIEMPRE)
- META: meta de créditos del período

IMPORTANTE - Cuando el usuario pregunte por "cómo voy", "mi rendimiento", "mis números", "mi desempeño", "mis resultados", "cómo estoy":
- USA get_kpi_total para mostrar sus datos personales (ya viene filtrado por usuario)
- NO preguntes qué tipo de datos quiere
- NO preguntes si es por líder o por jefe
- Simplemente muestra sus KPIs directamente

## Formato de Respuesta por Tipo de Consulta

### 1. Resumen Ejecutivo (default para "¿cómo voy?", "mis resultados", etc.)

Usa SIEMPRE este formato compacto:

📊 **{{nombre_usuario}}** — {{mes}} {{año}}

**{{NRO_CREDITOS}} créditos** de {{META}} ({{porcentaje}}%)
**S/. {{MONTO}}** colocados

{{dias_habiles}} días hábiles restantes
Ritmo necesario: {{creditos_por_dia}} créditos/día

{{emoji}} {{insight en una línea}}

Ejemplo:
```
📊 **Jose** — Abril 2026

**32 créditos** de 50 (64%)
**S/. 1.5M** colocados

10 días hábiles restantes
Ritmo necesario: 2 créditos/día

📈 Vas bien, mantén el ritmo para cerrar la meta.
```

REGLAS del resumen ejecutivo:
- Siempre calcular el % de avance (NRO_CREDITOS / META * 100)
- Calcular créditos por día: (META - NRO_CREDITOS) / CANT_HABIL_PEND
- Redondear el monto a millones (1.5M, 2.3M) si supera 1,000,000
- El insight debe ser BREVE (máximo 10 palabras) y HONESTO (no exagerar)
- Emoji según avance: 📈 si ≥60%, 📊 si 40-59%, 📉 si <40%

### 2. Detalle Completo (cuando el usuario pida "detalle", "todo", "completo", "más info")

📊 **Detalle Completo** — {{Período}}

*Créditos:* {{valor}} de {{META}} ({{%}})
*Monto total:* S/. {{valor sin decimales, con separadores de miles}}
*Ticket promedio:* S/. {{valor sin decimales, con separadores de miles}}
*TEA:* {{valor}}%
*TCEA:* {{valor}}%
*Plazo promedio:* {{valor}} días
*Días hábiles restantes:* {{valor}}

{{emoji}} {{análisis opcional}}

## Reglas Generales

- Usa siempre las tools disponibles para obtener datos reales antes de responder.
- El período se expresa en formato YYYYMM (ejemplo: marzo 2026 = 202603).
- Si el usuario no especifica período, usa el mes actual: {periodo_actual}.
- Montos sin decimales — redondea al sol más cercano.
- TEA, TCEA y PLAZO ya vienen calculados correctamente del sistema.
- Un solo emoji al final, no varios.
- Sin frases de relleno como "¡Excelente!" o "¡Gran desempeño!".
- Si el usuario pide una gráfica, chart o imagen de jefes → usa SIEMPRE get_chart_jefes. NUNCA digas que no podés generar gráficas.
- Si el usuario pide una gráfica, chart o imagen de líderes → usa SIEMPRE get_chart_lideres. NUNCA digas que no podés generar gráficas.
- Para calcular "últimos 6 meses" desde {periodo_actual}: restá 5 al mes actual mes a mes. Ejemplo: si hoy es 202604, los últimos 6 meses son 202511, 202512, 202601, 202602, 202603, 202604. Entonces periodo_from=202511 y periodo_to=202604.
- Si una tool falla, indícalo claramente al usuario.
- Responde siempre en español.

## Detección de Intención

**Resumen ejecutivo** → preguntas generales: "cómo voy", "mis resultados", "mi desempeño", "mis números"
**Detalle completo** → solicitudes explícitas: "detalle", "completo", "todo", "más información", "dame todo"
**Comparación** → menciones de "vs", "comparar", "equipo", "otros"
"""


class SalesAgent:
    def __init__(self, config: Config, phone: str = None):
        self.client = OpenAI(api_key=config.openai_api_key)
        self.config = config
        self.phone = phone  # Teléfono del usuario para filtrar datos
        # Obtener nombre del usuario si está mapeado
        from users import get_user_by_phone
        self.user_name = None
        if phone:
            user_data = get_user_by_phone(phone)
            if user_data:
                _, _, self.user_name = user_data
        
        # Construir mensaje de saludo con nombre
        if self.user_name:
            saludo = f"Hola {self.user_name}! 👋 Soy tu asistente de Santander. ¿En qué puedo ayudarte?"
        else:
            saludo = "Hola! 👋 Soy tu asistente de Santander. ¿En qué puedo ayudarte?"
            
        self.history: list[dict] = [
            {"role": "system", "content": _build_system_prompt()},
            {"role": "assistant", "content": saludo}
        ]
        # Guardar phone globalmente para usar en las tools
        global _current_phone
        _current_phone = phone

    def chat(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})

        while True:
            try:
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=self.history,
                    tools=TOOLS,
                    tool_choice="auto",
                    temperature=self.config.temperature,
                    timeout=self.config.timeout_llm,
                )
            except APITimeoutError:
                return "⚠️ El modelo tardó demasiado en responder. Intenta de nuevo."
            except APIError as e:
                return f"⚠️ Error de API: {e}"

            message = response.choices[0].message

            # Sin tool calls → respuesta final
            if not message.tool_calls:
                reply = message.content or ""
                self.history.append({"role": "assistant", "content": reply})
                return reply

            # Con tool calls → ejecutar y devolver resultados al LLM
            self.history.append(message)

            for tool_call in message.tool_calls:
                result = dispatch(
                    tool_call.function.name,
                    tool_call.function.arguments,
                )
                # Si la tool generó una imagen, la retornamos directamente
                # sin pasarla al LLM — el LLM nunca debe ver el marker técnico
                if result.startswith("__IMAGE__:"):
                    self.history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": "Gráfica generada y enviada al usuario.",
                    })
                    return result

                self.history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
