"""
Implementación de cada tool — llama a la API Santander via HTTP POST.
Solo funciones para ejecutivos.
"""

import io
import json

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


# Teléfono global para filtrar datos
_current_phone = None


def _call_api(periodo_from: int, periodo_to: int, phone: str = None) -> str:
    """Función base que llama a la API Santander y retorna JSON string.

    Args:
        periodo_from: Periodo inicial (YYYYMM)
        periodo_to: Periodo final (YYYYMM)
        phone: Número de WhatsApp del usuario (ej: 51902735404)
    """
    global _current_phone

    phone = phone or _current_phone

    config = _get_config()

    payload = {
        "PERIODOFROM": periodo_from,
        "PERIODOTO": periodo_to,
        "CELULAR": phone,
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


def get_kpi_creditos(periodo_from: int, periodo_to: int, phone: str = None) -> str:
    result = _call_api(periodo_from, periodo_to, phone)
    return _corregir_promedios(result)


def _corregir_promedios(json_str: str) -> str:
    """
    Corrige TEA_PROMEDIO, TCEA_PROMEDIO y PLAZO_PROMEDIO.
    Los valores que vienen son累加, hay que dividirlos por MONTO.
    """
    try:
        data = json.loads(json_str)

        if isinstance(data, dict) and 'data' in data:
            registros = data['data']
        elif isinstance(data, list):
            registros = data
        else:
            return json_str

        for reg in registros:
            monto = reg.get('MONTO', 0)
            if monto and monto != 0:
                tea = reg.get('TEA_PROMEDIO', 0)
                tcea = reg.get('TCEA_PROMEDIO', 0)
                plazo = reg.get('PLAZO_PROMEDIO', 0)

                reg['TEA_PROMEDIO'] = round(tea / monto, 2) if tea else 0
                reg['TCEA_PROMEDIO'] = round(tcea / monto, 2) if tcea else 0
                reg['PLAZO_PROMEDIO'] = round(plazo / monto, 2) if plazo else 0
            else:
                reg['TEA_PROMEDIO'] = 0
                reg['TCEA_PROMEDIO'] = 0
                reg['PLAZO_PROMEDIO'] = 0

        if isinstance(data, dict):
            data['data'] = registros
            return json.dumps(data, ensure_ascii=False)
        else:
            return json.dumps(registros, ensure_ascii=False)

    except Exception:
        return json_str


def _upload_media(png_bytes: bytes, config: Config) -> str:
    """Sube un PNG a Meta Media API y retorna el media_id."""
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


def generate_chart_personal(periodo_from: int, periodo_to: int, phone: str = None, metrica: str = "creditos") -> str:
    """
    Gráfica de líneas de colocaciones personales del ejecutivo.
    Muestra la evolución mes a mes con línea suave.

    Args:
        metrica: "creditos" | "monto" | "tea" | "tcea" | "plazo"
                 - "creditos" muestra NRO_CREDITOS + META (línea punteada)
                 - Las demás muestran la métrica sola
    """
    from scipy.interpolate import make_interp_spline
    import numpy as np

    global _current_phone
    phone = phone or _current_phone

    if not phone:
        return json.dumps({"error": "No se pudo identificar el usuario."})

    # Mapa de métrica → campo en el row
    metrica_campos = {
        "creditos": ("NRO_CREDITOS", "N° Créditos"),
        "monto":     ("MONTO",        "Soles (S/.)"),
        "tea":       ("TEA_PROMEDIO", "TEA (%)"),
        "tcea":      ("TCEA_PROMEDIO","TCEA (%)"),
        "plazo":     ("PLAZO_PROMEDIO","Meses"),
    }
    if metrica not in metrica_campos:
        return json.dumps({"error": f"Métrica '{metrica}' no válida. Use: creditoss, monto, tea, tcea, plazo."})

    campo, label_y = metrica_campos[metrica]

    raw = _call_api(periodo_from, periodo_to, phone=phone)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return json.dumps({"error": "No se pudo parsear la respuesta de la API."})

    if isinstance(data, dict) and "error" in data:
        return raw

    registros = data.get("data", []) if isinstance(data, dict) else data
    if not registros:
        return json.dumps({"error": "No hay datos para el período solicitado."})

    nombre_usuario = registros[0].get("ORI_DES_EJECUTIVO", "Ejecutivo")

    periodos = []
    valores = []
    metas = []

    for row in registros:
        periodo = int(row.get("PERIODO") or 0)
        valor = float(row.get(campo) or 0)
        meta = float(row.get("META") or 0) if metrica == "creditos" else None
        periodos.append(periodo)
        valores.append(valor)
        metas.append(meta)

    if not valores or sum(valores) == 0:
        return json.dumps({"error": "No hay datos para el período solicitado."})

    periodo_labels = [_periodo_label_es(p) for p in periodos]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    x = np.arange(len(valores))

    # Línea principal (suave)
    color_principal = '#DA291C'
    if len(valores) >= 3:
        try:
            x_smooth = np.linspace(0, len(valores) - 1, 100)
            spl = make_interp_spline(x, valores, k=min(3, len(valores) - 1))
            y_smooth = spl(x_smooth)
            ax.plot(x_smooth, y_smooth, linewidth=3, color=color_principal, zorder=2)
            ax.fill_between(x_smooth, y_smooth, alpha=0.15, color=color_principal, zorder=1)
        except Exception:
            ax.plot(x, valores, linewidth=3, color=color_principal, zorder=2)
    else:
        ax.plot(x, valores, linewidth=3, color=color_principal, zorder=2)

    ax.scatter(x, valores, s=120, color=color_principal, edgecolor='white',
               linewidth=2.5, zorder=3)

    # Meta (solo para créditos) — línea punteada
    if metrica == "creditos" and metas and sum(m for m in metas if m) > 0:
        ax.plot(x, metas, linewidth=2.5, color='#1A1A1A', linestyle='--',
                zorder=2, label='Meta')
        ax.scatter(x, metas, s=80, color='#1A1A1A', edgecolor='white',
                  linewidth=2, zorder=3, marker='D')

    # Títulos
    metric_labels = {"creditos": "Colocaciones", "monto": "Monto Desbursado",
                     "tea": "TEA Promedio", "tcea": "TCEA Promedio", "plazo": "Plazo Promedio"}
    ax.text(0.5, 1.06, f"{metric_labels.get(metrica, metrica)} de {nombre_usuario}",
            transform=ax.transAxes, fontsize=16, fontweight='bold', color='#2c3e50', ha='center')
    ax.text(0.5, 1.02, f"{_periodo_label_es(periodo_from)} – {_periodo_label_es(periodo_to)}",
            transform=ax.transAxes, fontsize=11, color='#7f8c8d', ha='center')

    ax.set_xlabel('Período', fontsize=12, color='#2c3e50')
    ax.set_ylabel(label_y, fontsize=12, color='#2c3e50')

    ax.grid(True, alpha=0.25, linestyle='-', linewidth=0.5, color='#ecf0f1', zorder=0)
    ax.set_axisbelow(True)
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')

    ax.set_xticks(x)
    ax.set_xticklabels(periodo_labels, fontsize=10, color='#2c3e50')
    ax.tick_params(axis='y', labelsize=10, colors='#2c3e50')

    if metrica == "monto":
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'S/. {int(y/1000)}K' if y >= 1000 else f'{int(y):,}'))
    else:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{int(y):,}'))

    if len(periodo_labels) > 8:
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    if metrica == "creditos" and metas and sum(m for m in metas if m) > 0:
        ax.legend(loc='upper left', fontsize=10, framealpha=0.9, facecolor='white', edgecolor='#bdc3c7')

    for spine in ax.spines.values():
        spine.set_color('#bdc3c7')
        spine.set_linewidth(0.5)

    plt.subplots_adjust(left=0.08, right=0.95, top=0.88, bottom=0.15)

    buf = io.BytesIO()
    try:
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        media_id = _upload_media(buf.read(), _get_config())
        return f"__IMAGE__:{media_id}"
    except Exception as e:
        plt.close(fig)
        return json.dumps({"error": f"No se pudo generar la imagen: {e}"})


def generate_chart_yoy_personal(anio_from: int, anio_to: int, phone: str = None, metrica: str = "creditos") -> str:
    """
    Gráfica Year-over-Year PERSONAL: compara los créditos (u otra métrica)
    del MISMO usuario entre dos años (mismos meses).

    Args:
        metrica: "creditos" | "monto" | "tea" | "tcea" | "plazo"
    """
    from scipy.interpolate import make_interp_spline
    import numpy as np

    global _current_phone
    phone = phone or _current_phone

    if not phone:
        return json.dumps({"error": "No se pudo identificar el usuario."})

    metrica_campos = {
        "creditos": ("NRO_CREDITOS", "N° Créditos"),
        "monto":     ("MONTO",        "Soles (S/.)"),
        "tea":       ("TEA_PROMEDIO", "TEA (%)"),
        "tcea":      ("TCEA_PROMEDIO","TCEA (%)"),
        "plazo":     ("PLAZO_PROMEDIO","Meses"),
    }
    if metrica not in metrica_campos:
        return json.dumps({"error": f"Métrica '{metrica}' no válida."})

    campo, label_y = metrica_campos[metrica]

    # Rango: Enero-Abril de ambos años
    periodo_from = anio_from * 100 + 1
    periodo_to = anio_to * 100 + 4

    raw = _call_api(periodo_from, periodo_to, phone=phone)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return json.dumps({"error": "No se pudo parsear la respuesta de la API."})

    if isinstance(data, dict) and "error" in data:
        return raw

    registros = data.get("data", []) if isinstance(data, dict) else data
    if not registros:
        return json.dumps({"error": "No hay datos para los años solicitados."})

    # Agrupar por año y mes
    yoy: dict[int, dict[int, float]] = {}
    for row in registros:
        periodo = int(row.get("PERIODO") or 0)
        anio = periodo // 100
        mes = periodo % 100
        valor = float(row.get(campo) or 0)

        if anio_from <= anio <= anio_to and 1 <= mes <= 4:
            yoy.setdefault(anio, {})[mes] = valor

    if not yoy:
        return json.dumps({"error": "No hay datos para comparar."})

    meses_labels = ["Ene", "Feb", "Mar", "Abr"]
    colores_years = ["#DA291C", "#1A1A1A"]

    x = np.arange(4)

    fig, ax = plt.subplots(figsize=(10, 5.5))

    for idx, anio in enumerate(sorted(yoy.keys())):
        valores = [yoy[anio].get(m, 0) for m in range(1, 5)]
        color = colores_years[idx % len(colores_years)]

        if len(valores) >= 3 and sum(valores) > 0:
            try:
                x_smooth = np.linspace(0, 3, 50)
                spl = make_interp_spline(x, valores, k=2)
                y_smooth = spl(x_smooth)
                ax.plot(x_smooth, y_smooth, linewidth=3, color=color, zorder=2)
                ax.fill_between(x_smooth, y_smooth, alpha=0.15, color=color, zorder=1)
            except Exception:
                pass

        ax.scatter(x, valores, s=120, color=color, edgecolor='white',
                   linewidth=2.5, zorder=3, label=str(anio))

    años_label = " vs ".join(str(a) for a in sorted(yoy.keys()))
    metric_labels = {"creditos": "Colocaciones", "monto": "Monto Desbursado",
                     "tea": "TEA Promedio", "tcea": "TCEA Promedio", "plazo": "Plazo Promedio"}

    ax.text(0.5, 1.06, f"Comparativa YoY — {años_label}", transform=ax.transAxes,
            fontsize=16, fontweight='bold', color='#2c3e50', ha='center')
    ax.text(0.5, 1.02, metric_labels.get(metrica, metrica), transform=ax.transAxes,
            fontsize=11, color='#7f8c8d', ha='center')

    ax.set_xlabel('Mes', fontsize=12, color='#2c3e50')
    ax.set_ylabel(label_y, fontsize=12, color='#2c3e50')

    ax.grid(True, alpha=0.25, linestyle='-', linewidth=0.5, color='#ecf0f1', zorder=0)
    ax.set_axisbelow(True)
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')

    ax.set_xticks(x)
    ax.set_xticklabels(meses_labels, fontsize=10, color='#2c3e50')
    ax.tick_params(axis='y', labelsize=10, colors='#2c3e50')

    if metrica == "monto":
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'S/. {int(y/1000)}K' if y >= 1000 else f'{int(y):,}'))
    else:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{int(y):,}'))

    ax.legend(loc='upper left', fontsize=10, framealpha=0.9,
              facecolor='white', edgecolor='#bdc3c7')

    for spine in ax.spines.values():
        spine.set_color('#bdc3c7')
        spine.set_linewidth(0.5)

    plt.subplots_adjust(left=0.08, right=0.95, top=0.88, bottom=0.15)

    buf = io.BytesIO()
    try:
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                  facecolor='white', edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        media_id = _upload_media(buf.read(), _get_config())
        return f"__IMAGE__:{media_id}"
    except Exception as e:
        plt.close(fig)
        return json.dumps({"error": f"No se pudo generar la imagen: {e}"})