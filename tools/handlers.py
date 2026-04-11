"""
Implementación de cada tool — llama a la API Santander via HTTP POST.
"""

import io
import json
from calendar import month_abbr
from datetime import date

import matplotlib
matplotlib.use("Agg")  # Backend sin GUI — obligatorio en servidor
import matplotlib.pyplot as plt
import requests

from config import Config


# Singleton: Config se carga una sola vez al importar el módulo,
# no en cada tool call. Fix de performance/correctness.
_config: Config | None = None


def _get_config() -> Config:
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def _call_api(dimension: str, periodo_from: int, periodo_to: int) -> str:
    """Función base que llama a la API Santander y retorna JSON string."""
    config = _get_config()
    payload = {
        "DIMENSION":    dimension,
        "PERIODOFROM":  periodo_from,
        "PERIODOTO":    periodo_to,
    }
    try:
        response = requests.post(
            config.api_url,
            json=payload,
            timeout=config.timeout_api,
        )
        response.raise_for_status()
        return json.dumps(response.json(), ensure_ascii=False)
    except requests.Timeout:
        return json.dumps({"error": "La API de Santander no respondió a tiempo."})
    except requests.RequestException as e:
        return json.dumps({"error": str(e)})


def get_kpi_total(periodo_from: int, periodo_to: int) -> str:
    return _call_api("TOTAL", periodo_from, periodo_to)


def get_kpi_por_canal(periodo_from: int, periodo_to: int) -> str:
    return _call_api("CANAL", periodo_from, periodo_to)


def get_kpi_por_lider(periodo_from: int, periodo_to: int) -> str:
    return _call_api("LIDER", periodo_from, periodo_to)


def get_kpi_por_jefe(periodo_from: int, periodo_to: int) -> str:
    return _call_api("JEFE", periodo_from, periodo_to)


def _upload_media(png_bytes: bytes, config: Config) -> str:
    """
    Sube un PNG a Meta Media API y retorna el media_id.
    Usa el mismo ACCESS_TOKEN configurado para enviar mensajes.
    """
    url = (
        f"https://graph.facebook.com/{config.whatsapp_api_version}"
        f"/{config.whatsapp_phone_number_id}/media"
    )
    headers = {"Authorization": f"Bearer {config.whatsapp_access_token}"}
    files = {
        "file": ("chart.png", png_bytes, "image/png"),
        "messaging_product": (None, "whatsapp"),
        "type": (None, "image/png"),
    }
    response = requests.post(url, headers=headers, files=files, timeout=15)
    response.raise_for_status()
    return response.json()["id"]


def _periodo_label_es(periodo: int) -> str:
    """Convierte 202603 → 'Mar 2026' en español."""
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    year = periodo // 100
    month = periodo % 100
    return f"{meses[month - 1]} {year}"


def _smooth_line(values, smoothness=0.3):
    """Aplica suavizado tipo spline a una lista de valores."""
    if len(values) < 4:
        return values
    from scipy.interpolate import make_interp_spline
    import numpy as np
    x = np.arange(len(values))
    # Crear más puntos para la línea suave
    x_new = np.linspace(0, len(values) - 1, 50)
    spl = make_interp_spline(x, values, k=3)
    y_smooth = spl(x_new)
    return y_smooth


def _periodo_label(periodo: int) -> str:
    """Convierte 202603 → 'Mar 2026'."""
    year = periodo // 100
    month = periodo % 100
    return f"{month_abbr[month]} {year}"


def _generate_chart(dimension: str, label_key: str, titulo: str, periodo_from: int, periodo_to: int) -> str:
    """Función base para generar gráficas de líneas onduladas con Plotly."""
    import plotly.graph_objects as go
    from scipy.interpolate import make_interp_spline
    import numpy as np

    config = _get_config()

    raw = _call_api(dimension, periodo_from, periodo_to)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return json.dumps({"error": "No se pudo parsear la respuesta de la API."})

    if isinstance(data, dict) and "error" in data:
        return raw

    # Generar lista de períodos
    periodos = []
    p = periodo_from
    while p <= periodo_to:
        periodos.append(p)
        year, month = p // 100, p % 100
        month += 1
        if month > 12:
            month = 1
            year += 1
        p = year * 100 + month

    entidades_data: dict[str, dict[int, float]] = {}
    registros = data.get("data", []) if isinstance(data, dict) else data

    for row in registros:
        nombre = row.get("DIMENSION") or "Sin nombre"
        periodo = int(row.get("PERIODO") or 0)
        creditos = float(row.get("NRO_CREDITOS") or 0)

        if periodo < periodo_from or periodo > periodo_to:
            continue
        if nombre not in entidades_data:
            entidades_data[nombre] = {}
        entidades_data[nombre][periodo] = creditos

    if not entidades_data:
        return json.dumps({"error": f"No hay datos para el período solicitado."})

    # Colores profesionales
    colores = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
        "#393b79", "#637521", "#8c6d31", "#843c39", "#7b4173"
    ]

    fig = go.Figure()

    for idx, (nombre, valores) in enumerate(entidades_data.items()):
        creditos = [valores.get(p, 0) for p in periodos]
        labels = [_periodo_label_es(p) for p in periodos]

        # Crear línea suave con spline
        x = np.arange(len(creditos))
        x_smooth = np.linspace(0, len(creditos) - 1, 50)
        
        if sum(creditos) > 0 and len(creditos) >= 3:
            try:
                spl = make_interp_spline(x, creditos, k=3)
                y_smooth = spl(x_smooth)
                labels_smooth = [labels[int(i)] for i in x_smooth]
                # Redondear las etiquetas smooth
                labels_smooth = [labels[min(int(round(i)), len(labels)-1)] for i in x_smooth]
            except Exception:
                x_smooth = x
                y_smooth = creditos
                labels_smooth = labels
        else:
            x_smooth = x
            y_smooth = creditos
            labels_smooth = labels

        color = colores[idx % len(colores)]

        # Línea ondeada principal
        fig.add_trace(go.Scatter(
            x=labels_smooth,
            y=y_smooth,
            mode='lines',
            name=nombre,
            line=dict(shape='spline', smoothing=1.3, color=color, width=3),
            hoverinfo='skip',
        ))

        # Puntos reales (más visibles)
        fig.add_trace(go.Scatter(
            x=labels,
            y=creditos,
            mode='markers',
            name=nombre,
            marker=dict(size=12, color=color, line=dict(width=2, color='white')),
            hovertemplate=f'{nombre}<br>%{{y}}: %{text}<extra></extra>',
            text=[f"{int(c):,}" for c in creditos],
        ))

    fig.update_layout(
        template='plotly_white',
        title=dict(
            text=f"{titulo}<br><sup>{_periodo_label_es(periodo_from)} – {_periodo_label_es(periodo_to)}</sup>",
            font=dict(size=20, color='#2c3e50'),
        ),
        xaxis=dict(
            title=dict(text="Período", font=dict(size=14, color='#2c3e50')),
            tickfont=dict(size=11, color='#2c3e50'),
            showgrid=True,
            gridcolor='#ecf0f1',
        ),
        yaxis=dict(
            title=dict(text="N° Créditos", font=dict(size=14, color='#2c3e50')),
            tickfont=dict(size=11, color='#2c3e50'),
            showgrid=True,
            gridcolor='#ecf0f1',
            tickformat=",d",
        ),
        legend=dict(
            font=dict(size=12, color='#2c3e50'),
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#bdc3c7',
            borderwidth=1,
        ),
        margin=dict(l=60, r=40, t=80, b=60),
        width=900,
        height=500,
        hovermode='closest',
    )

    # Exportar a PNG
    buf = io.BytesIO()
    try:
        fig.write_image(buf, format="png", scale=2)
        buf.seek(0)
        media_id = _upload_media(buf.read(), config)
        return f"__IMAGE__:{media_id}"
    except Exception as e:
        return json.dumps({"error": f"No se pudo generar la imagen: {e}"})


def generate_chart_jefes(periodo_from: int, periodo_to: int) -> str:
    """Gráfica de líneas por jefe comercial."""
    return _generate_chart("JEFE", "JEFE", "Colocaciones por Jefe Comercial", periodo_from, periodo_to)


def generate_chart_lideres(periodo_from: int, periodo_to: int) -> str:
    """Gráfica de líneas por líder de equipo."""
    return _generate_chart("LIDER", "LIDER", "Colocaciones por Líder de Equipo", periodo_from, periodo_to)


def generate_chart_yoy(anio_from: int, anio_to: int) -> str:
    """
    Gráfica Year-over-Year: compara N° créditos por mes entre dos años.
    Una línea por año, eje X = meses (Ene–Dic) con líneas onduladas.
    """
    import plotly.graph_objects as go
    from scipy.interpolate import make_interp_spline
    import numpy as np

    config = _get_config()

    periodo_from = anio_from * 100 + 1   # Enero del año inicial
    periodo_to   = anio_to  * 100 + 12  # Diciembre del año final

    raw = _call_api("TOTAL", periodo_from, periodo_to)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return json.dumps({"error": "No se pudo parsear la respuesta de la API."})

    if isinstance(data, dict) and "error" in data:
        return raw

    registros = data.get("data", []) if isinstance(data, dict) else data

    # Agrupar por año → mes → NRO_CREDITOS
    yoy: dict[int, dict[int, int]] = {}
    for row in registros:
        periodo = int(row.get("PERIODO") or 0)
        anio  = periodo // 100
        mes   = periodo % 100
        creditos = int(row.get("NRO_CREDITOS") or 0)
        if anio_from <= anio <= anio_to:
            yoy.setdefault(anio, {})[mes] = creditos

    if not yoy:
        return json.dumps({"error": "No hay datos para los años solicitados."})

    meses_labels = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    colores_years = ["#3498db", "#e74c3c", "#2ecc71", "#9b59b6", "#f39c12"]
    
    fig = go.Figure()

    for idx, anio in enumerate(sorted(yoy.keys())):
        valores = [yoy[anio].get(m, 0) for m in range(1, 13)]
        
        # Línea suave
        x = np.arange(len(valores))
        x_smooth = np.linspace(0, len(valores) - 1, 50)
        
        if sum(valores) > 0 and len(valores) >= 3:
            try:
                spl = make_interp_spline(x, valores, k=3)
                y_smooth = spl(x_smooth)
            except Exception:
                x_smooth = x
                y_smooth = valores
        else:
            x_smooth = x
            y_smooth = valores

        color = colores_years[idx % len(colores_years)]

        # Línea ondeada
        fig.add_trace(go.Scatter(
            x=meses_labels,
            y=valores,
            mode='lines',
            name=str(anio),
            line=dict(shape='spline', smoothing=1.3, color=color, width=3),
            hovertemplate=f'{anio}<br>%{{x}}: %{{y:,.0f}}<extra></extra>',
        ))

        # Puntos
        fig.add_trace(go.Scatter(
            x=meses_labels,
            y=valores,
            mode='markers',
            name=str(anio),
            marker=dict(size=14, color=color, symbol='circle', line=dict(width=2, color='white')),
            hovertemplate=f'{anio}<br>%{{x}}: %{{y:,.0f}}<extra></extra>',
        ))

    años_label = " vs ".join(str(a) for a in sorted(yoy.keys()))

    fig.update_layout(
        template='plotly_white',
        title=dict(
            text=f"Comparativa Year-over-Year — {años_label}<br><sup>N° Créditos por Mes</sup>",
            font=dict(size=20, color='#2c3e50'),
        ),
        xaxis=dict(
            title=dict(text="Mes", font=dict(size=14, color='#2c3e50')),
            tickfont=dict(size=12, color='#2c3e50'),
            showgrid=True,
            gridcolor='#ecf0f1',
        ),
        yaxis=dict(
            title=dict(text="N° Créditos", font=dict(size=14, color='#2c3e50')),
            tickfont=dict(size=12, color='#2c3e50'),
            showgrid=True,
            gridcolor='#ecf0f1',
            tickformat=",d",
        ),
        legend=dict(
            title=dict(text="Año"),
            font=dict(size=13, color='#2c3e50'),
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#bdc3c7',
            borderwidth=1,
        ),
        margin=dict(l=60, r=40, t=80, b=60),
        width=900,
        height=500,
        hovermode='x unified',
    )

    buf = io.BytesIO()
    try:
        fig.write_image(buf, format="png", scale=2)
        buf.seek(0)
        media_id = _upload_media(buf.read(), config)
        return f"__IMAGE__:{media_id}"
    except Exception as e:
        return json.dumps({"error": f"No se pudo generar la imagen: {e}"})
