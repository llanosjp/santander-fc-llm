"""
Mapea el nombre de tool (string del LLM) → función real en handlers.
"""

import json
from tools.handlers import (
    get_kpi_total,
    get_kpi_por_canal,
    get_kpi_por_lider,
    get_kpi_por_jefe,
    generate_chart_jefes,
    generate_chart_lideres,
    generate_chart_yoy,
    generate_chart_personal,
)

FUNCTION_MAP = {
    "get_kpi_total":        get_kpi_total,
    "get_kpi_por_canal":    get_kpi_por_canal,
    "get_kpi_por_lider":    get_kpi_por_lider,
    "get_kpi_por_jefe":     get_kpi_por_jefe,
    "get_chart_jefes":      generate_chart_jefes,
    "get_chart_lideres":    generate_chart_lideres,
    "get_chart_yoy":        generate_chart_yoy,
    "get_chart_personal":   generate_chart_personal,
}


def dispatch(name: str, arguments: str) -> str:
    """
    Ejecuta la tool indicada por el LLM.
    Retorna el resultado como JSON string.
    """
    if name not in FUNCTION_MAP:
        return json.dumps({"error": f"Tool '{name}' no encontrada."})

    try:
        args = json.loads(arguments) if arguments.strip() else {}
        return FUNCTION_MAP[name](**args)
    except Exception as e:
        return json.dumps({"error": str(e)})
