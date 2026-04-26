"""
JSON schemas que el LLM lee para decidir qué tool llamar.
Cada tool representa una dimensión de la API Santander.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_kpi_creditos",
            "description": (
                "Retorna los KPIs de colocación de créditos del ejecutivo: "
                "número de créditos, monto total, TEA, TCEA, plazo promedio, solicitudes, "
                "aprobados, documentados, desembolados y meta. "
                "Úsala cuando el usuario pregunte por sus KPIs, números, resultados, "
                "cómo va, mi rendimiento, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "periodo_from": {
                        "type": "integer",
                        "description": "Período de inicio en formato YYYYMM. Ejemplo: 202511 para noviembre 2025 (calcula 6 meses atrás desde hoy).",
                    },
                    "periodo_to": {
                        "type": "integer",
                        "description": "Período de fin en formato YYYYMM. Ejemplo: 202604 para abril 2026 (mes actual).",
                    },
                },
                "required": ["periodo_from", "periodo_to"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_grafica_creditos",
            "description": (
                "Genera una gráfica de líneas mostrando la evolución "
                "de las colocaciones del ejecutivo en un rango de períodos. "
                "Muestra la trayectoria individual mes a mes. "
                "Úsala cuando el usuario pida 'mi gráfica', 'mis colocaciones', "
                "'mi evolución', 'mi desempeño en el tiempo', 'últimos X meses', "
                "o cualquier referencia a SUS datos en formato visual. "
                "Para 'créditos' muestra además la META como línea punteada. "
                "Métricas disponibles: creditos (default), monto, tea, tcea, plazo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "periodo_from": {
                        "type": "integer",
                        "description": "Período de inicio en formato YYYYMM. Ignorado si ultimos_meses está presente.",
                    },
                    "periodo_to": {
                        "type": "integer",
                        "description": "Período de fin en formato YYYYMM. Ignorado si ultimos_meses está presente.",
                    },
                    "phone": {
                        "type": "string",
                        "description": "Número de teléfono del usuario con código de país. Ejemplo: 51902735404",
                    },
                    "metrica": {
                        "type": "string",
                        "enum": ["creditos", "monto", "tea", "tcea", "plazo"],
                        "description": "Qué métrica graficar. Default: 'creditos'. 'creditos' incluye línea de META.",
                    },
                    "ultimos_meses": {
                        "type": "integer",
                        "description": "Si está presente, calcula periodo_from/to automáticamente desde hoy. Ejemplo: 6 para últimos 6 meses.",
                    },
                },
                "required": ["periodo_from", "periodo_to"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_grafica_yoy",
            "description": (
                "Genera una gráfica comparativa Year-over-Year (YoY) del ejecutivo. "
                "Compara la misma métrica del MISMO usuario entre dos años (mismos meses). "
                "Úsala cuando el usuario pida comparar 'mi evolución', 'yo mismo', "
                "'mis mismos meses del año pasado', 'compararme con yo mismo'. "
                "Métricas disponibles: creditos (default), monto, tea, tcea, plazo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "anio_from": {
                        "type": "integer",
                        "description": "Año inicial. Ejemplo: 2025",
                    },
                    "anio_to": {
                        "type": "integer",
                        "description": "Año final. Ejemplo: 2026",
                    },
                    "phone": {
                        "type": "string",
                        "description": "Número de teléfono del usuario con código de país. Ejemplo: 51902735404",
                    },
                    "metrica": {
                        "type": "string",
                        "enum": ["creditos", "monto", "tea", "tcea", "plazo"],
                        "description": "Qué métrica graficar. Default: 'creditos'.",
                    },
                },
                "required": ["anio_from", "anio_to"],
            },
        },
    },
]
