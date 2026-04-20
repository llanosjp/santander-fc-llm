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
from users import get_filtros_from_phone


# Singleton: Config se carga una sola vez al importar el módulo,
# no en cada tool call. Fix de performance/correctness.
_config: Config | None = None


def _get_config() -> Config:
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


# Teléfono global para filtrar datos
_current_phone = None


def _call_api(dimension: str, periodo_from: int, periodo_to: int, phone: str = None) -> str:
    """Función base que llama a la API Santander y retorna JSON string.
    
    Args:
        dimension: Tipo de consulta (TOTAL, CANAL, LIDER, JEFE)
        periodo_from: Periodo inicial (YYYYMM)
        periodo_to: Periodo final (YYYYMM)
        phone: Número de WhatsApp del usuario (ej: +51902735404)
    """
    global _current_phone
    
    # Usar teléfono proporcionado o el global
    phone = phone or _current_phone
    
    config = _get_config()
    
    # Si hay teléfono, usar filtros del usuario
    if phone:
        filtros = get_filtros_from_phone(phone)
    else:
        # Mapeo de dimensión a filtro por defecto
        filtro_mapping = {
            "TOTAL": {"FILTRO_EJECUTIVO": None, "FILTRO_JEFE": None},
            "CANAL": {"FILTRO_EJECUTIVO": None, "FILTRO_JEFE": None, "FILTRO_LIDER": None},
            "LIDER": {"FILTRO_JEFE": None, "FILTRO_LIDER": None},
            "JEFE": {"FILTRO_JEFE": None},
        }
        filtros = filtro_mapping.get(dimension, {})
    
    payload = {
        "PERIODOFROM":  periodo_from,
        "PERIODOTO":    periodo_to,
        "USUARIO": filtros.get("USUARIO"),
        "FILTRO_LIDER": filtros.get("FILTRO_LIDER"),
        "FILTRO_JEFE": filtros.get("FILTRO_JEFE"),
        "FILTRO_EJECUTIVO": filtros.get("FILTRO_EJECUTIVO"),
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


def get_kpi_total(periodo_from: int, periodo_to: int, phone: str = None) -> str:
    result = _call_api("TOTAL", periodo_from, periodo_to, phone)
    # Corregir promedios si hay datos
    return _corregir_promedios(result)


def get_kpi_por_canal(periodo_from: int, periodo_to: int, phone: str = None) -> str:
    result = _call_api("CANAL", periodo_from, periodo_to, phone)
    return _corregir_promedios(result)


def _corregir_promedios(json_str: str) -> str:
    """
    Corrige TEA_PROMEDIO, TCEA_PROMEDIO y PLAZO_PROMEDIO.
    Los valores que vienen son累加, hay que dividirlos por MONTO.
    """
    import json
    try:
        data = json.loads(json_str)
        
        # Si es un dict con clave 'data'
        if isinstance(data, dict) and 'data' in data:
            registros = data['data']
        elif isinstance(data, list):
            registros = data
        else:
            return json_str
        
        # Procesar cada registro
        for reg in registros:
            monto = reg.get('MONTO', 0)
            if monto and monto != 0:
                # Calcular promedios reales
                tea = reg.get('TEA_PROMEDIO', 0)
                tcea = reg.get('TCEA_PROMEDIO', 0)
                plazo = reg.get('PLAZO_PROMEDIO', 0)
                
                # Dividir por monto (quitar los decimales primero)
                reg['TEA_PROMEDIO'] = round(tea / monto, 2) if tea else 0
                reg['TCEA_PROMEDIO'] = round(tcea / monto, 2) if tcea else 0
                reg['PLAZO_PROMEDIO'] = round(plazo / monto, 2) if plazo else 0
            else:
                reg['TEA_PROMEDIO'] = 0
                reg['TCEA_PROMEDIO'] = 0
                reg['PLAZO_PROMEDIO'] = 0
        
        # Reconstruir respuesta
        if isinstance(data, dict):
            data['data'] = registros
            return json.dumps(data, ensure_ascii=False)
        else:
            return json.dumps(registros, ensure_ascii=False)
            
    except Exception:
        return json_str


def get_kpi_por_lider(periodo_from: int, periodo_to: int, phone: str = None) -> str:
    result = _call_api("LIDER", periodo_from, periodo_to, phone)
    return _corregir_promedios(result)


def get_kpi_por_jefe(periodo_from: int, periodo_to: int, phone: str = None) -> str:
    result = _call_api("JEFE", periodo_from, periodo_to, phone)
    return _corregir_promedios(result)


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
    """Función base para generar gráficas de líneas con Matplotlib."""
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

    # Colores profesionales (misma paleta que Plotly)
    colores = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
    ]

    periodo_labels = [_periodo_label_es(p) for p in periodos]
    x = np.arange(len(periodos))

    # Crear figura
    fig, ax = plt.subplots(figsize=(12, 6.67))

    for idx, (nombre, valores) in enumerate(entidades_data.items()):
        creditos = [valores.get(p, 0) for p in periodos]
        color = colores[idx % len(colores)]

        # Crear línea suave con spline
        if len(creditos) >= 3 and sum(creditos) > 0:
            try:
                x_smooth = np.linspace(0, len(creditos) - 1, 100)
                spl = make_interp_spline(x, creditos, k=min(3, len(creditos) - 1))
                y_smooth = spl(x_smooth)
                ax.plot(x_smooth, y_smooth, linewidth=3, color=color, zorder=2)
                ax.fill_between(x_smooth, y_smooth, alpha=0.1, color=color, zorder=1)
            except Exception:
                ax.plot(x, creditos, linewidth=3, color=color, zorder=2)
                ax.fill_between(x, creditos, alpha=0.1, color=color, zorder=1)
        else:
            ax.plot(x, creditos, linewidth=3, color=color, zorder=2)
            ax.fill_between(x, creditos, alpha=0.1, color=color, zorder=1)

        # Puntos marcadores
        ax.scatter(x, creditos, s=120, color=color, edgecolor='white', 
                  linewidth=2.5, zorder=3, label=nombre)

    # Títulos (estilo Plotly)
    ax.text(0.5, 1.05, titulo, transform=ax.transAxes, 
            fontsize=18, fontweight='bold', color='#2c3e50', ha='center')
    ax.text(0.5, 1.01, f"{_periodo_label_es(periodo_from)} – {_periodo_label_es(periodo_to)}", 
            transform=ax.transAxes, fontsize=12, color='#7f8c8d', ha='center')

    ax.set_xlabel('Período', fontsize=13, color='#2c3e50', fontweight='500')
    ax.set_ylabel('N° Créditos', fontsize=13, color='#2c3e50', fontweight='500')

    # Grid profesional
    ax.grid(True, alpha=0.25, linestyle='-', linewidth=0.5, color='#ecf0f1', zorder=0)
    ax.set_axisbelow(True)
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')

    # Ejes
    ax.set_xticks(x)
    ax.set_xticklabels(periodo_labels, fontsize=10, color='#2c3e50')
    ax.tick_params(axis='y', labelsize=10, colors='#2c3e50')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{int(y):,}'))

    if len(periodo_labels) > 8:
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # Leyenda
    ax.legend(loc='upper left', fontsize=10, framealpha=0.9, 
             facecolor='white', edgecolor='#bdc3c7')

    # Espinas
    for spine in ax.spines.values():
        spine.set_color('#bdc3c7')
        spine.set_linewidth(0.5)

    plt.subplots_adjust(left=0.08, right=0.95, top=0.88, bottom=0.10)

    # Exportar
    buf = io.BytesIO()
    try:
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                  facecolor='white', edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        media_id = _upload_media(buf.read(), config)
        return f"__IMAGE__:{media_id}"
    except Exception as e:
        plt.close(fig)
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
    Una línea por año, eje X = meses. Usa matplotlib.
    """
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
    colores_years = ["#DA291C", "#E31837", "#8B0000", "#FF6B6B", "#B71C1C"]  # Santander reds
    
    x = np.arange(12)  # 12 meses

    # Crear figura
    fig, ax = plt.subplots(figsize=(12, 6.67))

    for idx, anio in enumerate(sorted(yoy.keys())):
        valores = [yoy[anio].get(m, 0) for m in range(1, 13)]
        color = colores_years[idx % len(colores_years)]

        # Línea suave con spline
        if len(valores) >= 3 and sum(valores) > 0:
            try:
                x_smooth = np.linspace(0, 11, 100)
                spl = make_interp_spline(x, valores, k=3)
                y_smooth = spl(x_smooth)
                ax.plot(x_smooth, y_smooth, linewidth=3, color=color, zorder=2)
                ax.fill_between(x_smooth, y_smooth, alpha=0.1, color=color, zorder=1)
            except Exception:
                ax.plot(x, valores, linewidth=3, color=color, zorder=2)
                ax.fill_between(x, valores, alpha=0.1, color=color, zorder=1)
        else:
            ax.plot(x, valores, linewidth=3, color=color, zorder=2)
            ax.fill_between(x, valores, alpha=0.1, color=color, zorder=1)

        # Puntos marcadores
        ax.scatter(x, valores, s=120, color=color, edgecolor='white', 
                  linewidth=2.5, zorder=3, label=str(anio))

    años_label = " vs ".join(str(a) for a in sorted(yoy.keys()))

    # Títulos
    ax.text(0.5, 1.05, f"Comparativa Year-over-Year — {años_label}", transform=ax.transAxes, 
            fontsize=18, fontweight='bold', color='#2c3e50', ha='center')
    ax.text(0.5, 1.01, "N° Créditos por Mes", transform=ax.transAxes, 
            fontsize=12, color='#7f8c8d', ha='center')

    ax.set_xlabel('Mes', fontsize=13, color='#2c3e50', fontweight='500')
    ax.set_ylabel('N° Créditos', fontsize=13, color='#2c3e50', fontweight='500')

    # Grid profesional
    ax.grid(True, alpha=0.25, linestyle='-', linewidth=0.5, color='#ecf0f1', zorder=0)
    ax.set_axisbelow(True)
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')

    # Ejes
    ax.set_xticks(x)
    ax.set_xticklabels(meses_labels, fontsize=10, color='#2c3e50')
    ax.tick_params(axis='y', labelsize=10, colors='#2c3e50')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{int(y):,}'))

    # Leyenda
    ax.legend(title='Año', loc='upper left', fontsize=10, framealpha=0.9, 
             facecolor='white', edgecolor='#bdc3c7')

    # Espinas
    for spine in ax.spines.values():
        spine.set_color('#bdc3c7')
        spine.set_linewidth(0.5)

    plt.subplots_adjust(left=0.08, right=0.95, top=0.88, bottom=0.10)

    # Exportar
    buf = io.BytesIO()
    try:
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                  facecolor='white', edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        media_id = _upload_media(buf.read(), config)
        return f"__IMAGE__:{media_id}"
    except Exception as e:
        plt.close(fig)
        return json.dumps({"error": f"No se pudo generar la imagen: {e}"})


def _get_months_in_range(periodo_from: int, periodo_to: int) -> list[int]:
    """Retorna lista de meses en el rango [periodo_from, periodo_to]."""
    meses = []
    p = periodo_from
    while p <= periodo_to:
        meses.append(p)
        year, month = p // 100, p % 100
        month += 1
        if month > 12:
            month = 1
            year += 1
        p = year * 100 + month
    return meses


def generate_chart_personal(periodo_from: int, periodo_to: int, phone: str = None) -> str:
    """
    Gráfica de líneas de colocaciones personales del ejecutivo.
    Muestra la evolución mes a mes de SUS créditos desembolsados.
    Usa Plotly con estilo profesional original.
    
    Args:
        periodo_from: Período inicial (YYYYMM)
        periodo_to: Período final (YYYYMM)
        phone: Teléfono del usuario (opcional, también usa _current_phone global)
    """
    import plotly.graph_objects as go
    from scipy.interpolate import make_interp_spline
    import numpy as np

    global _current_phone
    
    # Usar teléfono proporcionado o el global
    phone = phone or _current_phone
    
    if not phone:
        return json.dumps({"error": "No se pudo identificar el usuario."})

    config = _get_config()

    # La API de Power Automate tiene un bug con rangos + filtro de usuario
    # Solución: llamar mes por mes y combinar resultados
    meses = _get_months_in_range(periodo_from, periodo_to)

    all_registros = []
    for mes in meses:
        # Pasar el teléfono explícitamente a cada llamada
        raw = _call_api("TOTAL", mes, mes, phone=phone)
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and "data" in data:
                all_registros.extend(data["data"])
            elif isinstance(data, list):
                all_registros.extend(data)
        except (json.JSONDecodeError, TypeError):
            continue

    if not all_registros:
        return json.dumps({"error": "No hay datos para el período solicitado."})

    nombre_usuario = all_registros[0].get("ORI_DES_EJECUTIVO", "Ejecutivo")

    periodos = []
    creditos = []
    montos = []  # Agregar para mostrar monto
    for row in all_registros:
        periodo = int(row.get("PERIODO") or 0)
        nro_creditos = int(row.get("DESEMBOLSADO") or row.get("NRO_CREDITOS") or 0)
        monto = float(row.get("MONTO") or 0)
        periodos.append(periodo)
        creditos.append(nro_creditos)
        montos.append(monto)

    if not creditos or sum(creditos) == 0:
        return json.dumps({"error": "No hay colocaciones registradas en el período."})

    periodo_labels = [_periodo_label_es(p) for p in periodos]

    # ============ PLOTLY con estilo profesional ============
    fig = go.Figure()
    x = np.arange(len(creditos))

    # Línea suave con spline
    if len(creditos) >= 3:
        try:
            x_smooth = np.linspace(0, len(creditos) - 1, 100)
            spl = make_interp_spline(x, creditos, k=min(3, len(creditos) - 1))
            y_smooth = spl(x_smooth)
            fig.add_trace(go.Scatter(
                x=periodo_labels,
                y=creditos,
                mode='lines',
                name=nombre_usuario,
                line=dict(shape='spline', smoothing=1.3, color='#DA291C', width=4),
                hovertemplate='%{x}<br>%{y:,.0f} créditos<extra></extra>',
            ))
        except Exception:
            fig.add_trace(go.Scatter(
                x=periodo_labels, y=creditos, mode='lines',
                name=nombre_usuario, line=dict(color='#DA291C', width=4),
                hovertemplate='%{x}<br>%{y:,.0f} créditos<extra></extra>',
            ))

    # Puntos marcadores - mostrar créditos y monto EN LA IMAGEN (no solo hover)
    texts = []
    for c, m in zip(creditos, montos):
        texts.append(f"{c:,}")
    
    # Agregar labels directamente en la gráfica (sin recuadro)
    for i, (label, credito, monto) in enumerate(zip(periodo_labels, creditos, montos)):
        fig.add_annotation(
            x=label,
            y=credito,
            text=f"{credito:,}<br>S/ {monto:,.0f}",
            showarrow=False,
            font=dict(size=10, color='#DA291C'),
            bgcolor='transparent',
            bordercolor='transparent',
            borderwidth=0,
            borderpad=3,
            yshift=15,  # arriba del punto
        )
    
    # Puntos marcadores (sin texto)
    fig.add_trace(go.Scatter(
        x=periodo_labels,
        y=creditos,
        mode='markers',
        name=nombre_usuario,
        marker=dict(size=12, color='#DA291C', symbol='circle', line=dict(width=2, color='white')),
    ))

    # Layout profesional (igual a las otras gráficas)
    fig.update_layout(
        template='plotly_white',
        title=dict(
            text=f"Mis Colocaciones — {nombre_usuario}<br><sup>{_periodo_label_es(periodo_from)} – {_periodo_label_es(periodo_to)}</sup>",
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
        hovermode='x unified',
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


def generate_chart_yoy_personal(anio_from: int, anio_to: int, phone: str = None) -> str:
    """
    Gráfica Year-over-Year PERSONAL: compara los créditos del MISMO usuario
    entre dos años (mismos meses).
    
    Args:
        anio_from: Año inicial (ej: 2025)
        anio_to: Año final (ej: 2026)
        phone: Teléfono del usuario (opcional, también usa _current_phone global)
    """
    import plotly.graph_objects as go
    from scipy.interpolate import make_interp_spline
    import numpy as np

    global _current_phone
    phone = phone or _current_phone
    
    if not phone:
        return json.dumps({"error": "No se pudo identificar el usuario."})

    config = _get_config()

    # Obtener meses 1-4 (Enero-Abril) de ambos años
    meses_consultar = []
    for anio in [anio_from, anio_to]:
        for mes in range(1, 5):  # Enero-Abril
            meses_consultar.append(anio * 100 + mes)

    # Llamar API mes por mes
    all_registros = []
    for periodo in meses_consultar:
        raw = _call_api("TOTAL", periodo, periodo, phone=phone)
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and "data" in data:
                all_registros.extend(data["data"])
            elif isinstance(data, list):
                all_registros.extend(data)
        except (json.JSONDecodeError, TypeError):
            continue

    if not all_registros:
        return json.dumps({"error": "No hay datos para los años solicitados."})

    nombre_usuario = all_registros[0].get("ORI_DES_EJECUTIVO", "Ejecutivo")

    # Agrupar por año y mes
    yoy: dict[int, dict[int, int]] = {}
    for row in all_registros:
        periodo = int(row.get("PERIODO") or 0)
        anio = periodo // 100
        mes = periodo % 100
        creditos = int(row.get("DESEMBOLSADO") or row.get("NRO_CREDITOS") or 0)
        
        if anio_from <= anio <= anio_to and 1 <= mes <= 4:
            yoy.setdefault(anio, {})[mes] = creditos

    if not yoy:
        return json.dumps({"error": "No hay datos para comparar."})

    meses_labels = ["Ene", "Feb", "Mar", "Abr"]
    colores_years = ["#DA291C", "#1A1A1A"]  # Santander: rojo 2025, negro 2026
    
    x = np.arange(4)  # 4 meses

    # Crear figura con Plotly
    fig = go.Figure()

    for idx, anio in enumerate(sorted(yoy.keys())):
        valores = [yoy[anio].get(m, 0) for m in range(1, 5)]
        color = colores_years[idx % len(colores_years)]

        # Línea suave
        if len(valores) >= 3 and sum(valores) > 0:
            try:
                x_smooth = np.linspace(0, 3, 50)
                spl = make_interp_spline(x, valores, k=2)
                y_smooth = spl(x_smooth)
                fig.add_trace(go.Scatter(
                    x=meses_labels,
                    y=valores,
                    mode='lines',
                    name=str(anio),
                    line=dict(shape='spline', smoothing=1.3, color=color, width=4),
                ))
            except Exception:
                pass

        # Puntos con valores
        texts = [f"{v:,}" for v in valores]
        
        # Agregar annotations con valores (sin recuadro)
        for i, (mes, valor) in enumerate(zip(meses_labels, valores)):
            fig.add_annotation(
                x=mes,
                y=valor,
                text=f"{valor:,}",
                showarrow=False,
                font=dict(size=11, color=color, weight='bold'),
                bgcolor='transparent',
                bordercolor='transparent',
                borderwidth=0,
                yshift=15,
            )

        # Puntos
        fig.add_trace(go.Scatter(
            x=meses_labels,
            y=valores,
            mode='markers',
            name=str(anio),
            marker=dict(size=14, color=color, symbol='circle', line=dict(width=2, color='white')),
        ))

    años_label = " vs ".join(str(a) for a in sorted(yoy.keys()))

    # Layout profesional
    fig.update_layout(
        template='plotly_white',
        title=dict(
            text=f"Mi Evolución — {nombre_usuario}<br><sup>{años_label} (Ene-Abr)</sup>",
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

    # Exportar
    buf = io.BytesIO()
    try:
        fig.write_image(buf, format="png", scale=2)
        buf.seek(0)
        media_id = _upload_media(buf.read(), config)
        return f"__IMAGE__:{media_id}"
    except Exception as e:
        return json.dumps({"error": f"No se pudo generar la imagen: {e}"})
            
