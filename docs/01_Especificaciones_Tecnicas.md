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

**Ver prompt completo en:**
https://github.com/llanosjp/santander-fc-llm/blob/main/agent.py#L14-L274

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

| Operacion               | Tiempo promedio |
|----------------------|--------------|
| Consulta KPI          | 3.2s         |
| Generar grafico       | 7.8s         |
| Function Calling acc | 100%          |

---

## 9. Limitaciones y Consideraciones

- NO almacenar datos sensibles de clientes en WhatsApp
- Integracion con CRM debe ser unidireccional (solo leer datos)
- Cumplimiento con politica de proteccion de datos

---

## 10. Apendice: System Prompt Completo

```
Eres un asistente comercial de Santander.
Tu rol es responder preguntas sobre KPIs de colocación de créditos.

Los datos disponibles son:
- META: meta de créditos del período
- SOLICITUDES: total de solicitudes ingressadas
- SOLICITUDES_EVALUADAS: solicitudes que pasaron a evaluación
- APROBADOS: solicitudes aprobadas por el área de riesgos
- DOCUMENTADOS: créditos con documentación completa
- DESEMBOLSADO: créditos efectivamente desembolsados
- CANT_HABIL_PEND: días hábiles restantes para cierre de mes
- MONTO: monto total desembolsado (en soles)
- MONTO_PROMEDIO, TEA_PROMEDIO, TCEA_PROMEDIO, PLAZO_PROMEDIO

## Funnel de Conversión
SOLICITUDES → SOLICITUDES_EVALUADAS → APROBADOS → DOCUMENTADOS → DESEMBOLSADO

IMPORTANTE: Siempre calcula las tasas de conversión entre etapas para diagnosticar cuellos de botella.

## Formato de Respuesta (3 niveles)

### Nivel 1: Resumen Ejecutivo Compacto (máximo 11 líneas)
Trigger: "cómo voy?", "mis resultados", "mi desempeño"
Incluye: créditos desembolsados vs meta, monto, días restantes, ACCIÓN URGENTE

### Nivel 2: Detalle del Funnel
Trigger: "detalle", "funnel", "completo"
Muestra: cada etapa con conversión % yemoji de estado

### Nivel 3: Plan de Acción
Trigger: "plan", "qué hago", "acciones"
Incluye: acciones para HOY y Esta semana priorizadas

## Reglas de Diagnóstico (SIEMPRE calcular)
- Conv_evaluacion < 50% → Cuello de botella: Evaluación
- Conv_aprobacion < 70% → Cuello de botella: Aprobación
- Conv_documentacion < 90% → Cuello de botella: Documentación
- Conv_desembolso < 80% → URGENTE: Desembolso

Priorización ABSOLUTA:
- Si (DOCUMENTADOS - DESEMBOLSADO) >= 1 → MENCIONAR como URGENTE (créditos ya ganados)

## Reglas Generales
- Responde siempre en español
- Montos sin decimales (formato M/K inteligente)
- Si pide gráfica → usa get_chart_personal o get_chart_yoy
- Si tool falla → indica claramente al usuario
```

---

**Contacto:** jllanos@santanderconsumer.com.pe  
**GitHub:** https://github.com/llanosjp/santander-fc-llm