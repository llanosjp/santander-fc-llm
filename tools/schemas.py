"""
JSON schemas que el LLM lee para decidir qué tool llamar.
Cada tool representa una dimensión de la API Santander.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_kpi_total",
            "description": (
                "Retorna los KPIs globales de colocación de créditos: "
                "número de créditos, monto total y monto promedio. "
                "Úsala cuando el usuario pregunte por el total general, "
                "resultado global o cifras consolidadas."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "periodo_from": {
                        "type": "integer",
                        "description": "Período de inicio en formato YYYYMM. Ejemplo: 202603 para marzo 2026.",
                    },
                    "periodo_to": {
                        "type": "integer",
                        "description": "Período de fin en formato YYYYMM. Ejemplo: 202603 para marzo 2026.",
                    },
                },
                "required": ["periodo_from", "periodo_to"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_chart_yoy_personal",
            "description": (
                "Genera una gráfica comparativa Year-over-Year (YoY) PERSONAL del usuario. "
                "Compara los créditos del MISMO usuario entre dos años (mismos meses). "
                "Úsala cuando el usuario pida comparar 'mi evolución', 'yo mismo', "
                "'mis mismos meses del año pasado', 'compararme con yo mismo'. "
                "Ejemplo: 'Enero-Abril 2025 vs Enero-Abril 2026'."
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
                },
                "required": ["anio_from", "anio_to"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_chart_personal",
            "description": (
                "Genera una gráfica de líneas (chart, imagen, visual) mostrando la evolución "
                "de MIS colocaciones personales de créditos en un rango de períodos. "
                "Muestra la trayectoria individual del ejecutivo mes a mes. "
                "Úsala cuando el usuario pida 'mi gráfica', 'mis colocaciones', "
                "'mi evolución', 'mi desempeño en el tiempo', 'últimos X meses', "
                "o cualquier referencia a SUS datos personales en formato visual."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "periodo_from": {
                        "type": "integer",
                        "description": "Período de inicio en formato YYYYMM. Ejemplo: 202311 para noviembre 2023.",
                    },
                    "periodo_to": {
                        "type": "integer",
                        "description": "Período de fin en formato YYYYMM. Ejemplo: 202604 para abril 2026.",
                    },
                    "phone": {
                        "type": "string",
                        "description": "Número de teléfono del usuario con código de país. Ejemplo: 51902735404",
                    },
                },
                "required": ["periodo_from", "periodo_to"],
            },
        },
    },
]
