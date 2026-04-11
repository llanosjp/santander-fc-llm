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
            "name": "get_kpi_por_canal",
            "description": (
                "Retorna los KPIs de colocación de créditos desglosados por canal de venta "
                "(Patios, Konecta, Vertice, etc.). "
                "Úsala cuando el usuario pregunte por canal, por tipo de venta "
                "o quiera comparar canales entre sí."
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
            "name": "get_kpi_por_lider",
            "description": (
                "Retorna los KPIs de colocación de créditos desglosados por líder de equipo. "
                "Úsala cuando el usuario pregunte por líder, ejecutivo, "
                "ranking de líderes o performance individual."
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
            "name": "get_kpi_por_jefe",
            "description": (
                "Retorna los KPIs de colocación de créditos desglosados por jefe comercial. "
                "Úsala cuando el usuario pregunte por jefe, gerente, "
                "ranking de jefes o resultados por zona comercial."
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
            "name": "get_chart_yoy",
            "description": (
                "Genera una gráfica comparativa Year-over-Year (YoY) del total de créditos "
                "por mes, comparando múltiples años entre sí. Una línea por año, eje X = meses. "
                "Úsala cuando el usuario pida comparar años, ver crecimiento anual, "
                "evolución año a año, o comparativa del mismo mes entre distintos años. "
                "Para 3 años: anio_from=2024, anio_to=2026 mostrará 2024, 2025 y 2026."
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
                },
                "required": ["anio_from", "anio_to"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_chart_lideres",
            "description": (
                "Genera una gráfica de líneas (chart, imagen, visual) comparando el monto "
                "de colocaciones de créditos por líder de equipo en un rango de períodos. "
                "Úsala cuando el usuario pida una gráfica, chart, imagen, comparativa visual "
                "o evolución de líderes de equipo en el tiempo."
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
                },
                "required": ["periodo_from", "periodo_to"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_chart_jefes",
            "description": (
                "Genera una gráfica de líneas (chart, imagen, visual) comparando el monto "
                "de colocaciones de créditos por jefe comercial en un rango de períodos. "
                "Úsala cuando el usuario pida una gráfica, chart, imagen, comparativa visual "
                "o evolución de jefes comerciales en el tiempo."
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
                },
                "required": ["periodo_from", "periodo_to"],
            },
        },
    },
]
