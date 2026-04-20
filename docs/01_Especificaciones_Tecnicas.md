# Documento 1: Especificaciones Tecnicas

**Proyecto:** PulsoAI - Hackathon GPT Santander Peru  
**Equipo:** Jean Pierre Llanos, Juan Diaz, Lisbeth Huaman  
**Fecha:** 20 abril 2026

---

## 1. Resumen

PulsoAI es un asistente WhatsApp con GPT-4o que permite a ejecutivos comerciales consultar KPIs de creditos en lenguaje natural. El sistema esta en produccion en 137.184.90.198.

---

## 2. Arquitectura

```
Ejecutivo -> WhatsApp -> FastAPI -> GPT-4o Function Calling -> API Santander -> BD Santander
```

**Componentes:**
- WhatsApp Cloud API (Meta)
- FastAPI + BackgroundTasks (cumplir timeout Meta <5s)
- GPT-4o con 9 tools
- API Santander como proxy a BD
- Plotly + Kaleido para graficos
- nginx + Let's Encrypt

---

## 3. Modelo GPT-4o

**Configuracion:**
- model: gpt-4o
- temperature: 0.1 (precision, no creatividad)

**System Prompt (274 lineas):**
- Define datos disponibles (META, SOLICITUDES, APROBADOS, etc.)
- Funnel: SOLICITUDES -> EVALUADAS -> APROBADOS -> DOCUMENTADOS -> DESEMBOLSADO
- 3 niveles de respuesta: Resumen / Detalle / Plan
- diagnostico automatico con umbrales

---

## 4. Tools (9 funciones)

**KPIs:**
- get_kpi_total, get_kpi_por_canal, get_kpi_por_lider, get_kpi_por_jefe

**Graficos:**
- get_chart_personal, get_chart_yoy, get_chart_yoy_personal, get_chart_lideres, get_chart_jefes

---

## 5. Graficos

**Colores Santander:**
- Rojo #DA291C (montos)
- Navy #1A237E (creditos)

**Formato montos:** 2.15M / 850K / 12.3K (inteligente)

---

## 6. Seguridad

- GPT-4o NO tiene acceso SQL directo
- Solo llama a funciones predefinidas
- Webhook verificado con token
- HTTPS obligatorio
- Filtrado por telefono (usuario)

---

## 7. Deploy

- DigitalOcean: 137.184.90.198
- Ubuntu 22.04, 2vCPU, 2GB RAM
- systemd con auto-restart
- CI/CD: GitHub Actions (push -> deploy)

---

## 8. Performance

| Operacion | Tiempo promedio |
|----------|----------------|
| Consulta KPI | 3.2s |
| Generar grafico | 7.8s |
| Function Calling accuracy | 100% |

---

**Repo:** https://github.com/llanosjp/santander-fc-llm