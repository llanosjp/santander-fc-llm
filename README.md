# Santander Function Calling LLM

Asistente comercial con IA para consultas de KPIs en tiempo real por WhatsApp.

---

## 🎯 ¿Qué es esto?

Un agente conversacional que responde preguntas sobre KPIs de colocación de créditos en lenguaje natural, usando **GPT-4o** con **Function Calling**.

Los ejecutivos comerciales pueden preguntar desde WhatsApp:
- "¿Cómo vamos en colocaciones este mes?"
- "¿Qué canal tuvo mayor monto?"
- "Dame una gráfica de los últimos 6 meses"

Y reciben respuestas en **segundos** con datos reales.

---

## 🏗️ Arquitectura

```
Ejecutivo Comercial
    ↓ (WhatsApp)
Meta Cloud API
    ↓ (webhook)
FastAPI Server
    ↓ (HTTP)
GPT-4o + Function Calling
    ↓ (HTTP)
API Santander (Power Automate)
    ↓
Base de Datos Santander
```

**Clave:** GPT-4o NUNCA toca la BD directamente — solo consume la API como cliente HTTP.

---

## ✨ Features

- ✅ **Function Calling con GPT-4o** — el agente decide qué datos consultar según la pregunta
- ✅ **WhatsApp Cloud API oficial** — integración nativa de Meta
- ✅ **Consultas multi-dimensión** — total, por canal, por líder, por jefe comercial
- ✅ **Gráficas automáticas** — genera PNG y los envía directo por WhatsApp
- ✅ **Historial de conversaciones** — persistido por usuario
- ✅ **Multi-usuario simultáneo** — sesión independiente por número de teléfono
- ✅ **Deploy automatizado** — CI/CD con GitHub Actions

---

## 🛠️ Stack técnico

| Componente | Tecnología |
|------------|------------|
| LLM | OpenAI GPT-4o |
| Backend | FastAPI + Uvicorn |
| Messaging | WhatsApp Cloud API (Meta) |
| Data Source | API REST (Power Automate) |
| Charts | Plotly + Kaleido |
| Deploy | DigitalOcean Droplet + systemd |
| Proxy | nginx + Let's Encrypt |
| CI/CD | GitHub Actions |

---

## 📦 Instalación local

### 1. Clonar el repo

```bash
git clone https://github.com/llanosjp/santander-fc-llm.git
cd santander-fc-llm
```

### 2. Crear virtual environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.template .env
# Editar .env con tus credenciales
```

### 4. Probar en modo CLI

```bash
python main.py
```

Ejemplo de interacción:

```
Tú: ¿Cuántos créditos se colocaron este mes?

Agente: 📊 *KPI Total — Abril 2026*

*Créditos:* 1,234
*Monto total:* S/. 45,678,900
*Ticket promedio:* S/. 37,000

📈 Crecimiento sostenido vs. mes anterior
```

---

## 🚀 Deploy a producción

Ver **[DEPLOY.md](./DEPLOY.md)** para instrucciones completas.

Resumen:

```bash
# En el droplet
export SANTANDER_API_URL="..."
export OPENAI_API_KEY="..."
export WHATSAPP_PHONE_NUMBER_ID="..."
export WHATSAPP_ACCESS_TOKEN="..."
export WHATSAPP_VERIFY_TOKEN="santander-wsp-2026"

bash <(curl -s https://raw.githubusercontent.com/llanosjp/santander-fc-llm/master/scripts/setup-server.sh)
```

Esto configura:
- Servicio systemd corriendo 24/7
- nginx como reverse proxy
- Firewall
- El agente listo para recibir webhooks de WhatsApp

---

## 🔧 Tools disponibles

El agente tiene acceso a estas 7 herramientas (el LLM decide cuál usar según la pregunta):

| Tool | Descripción |
|------|-------------|
| `get_kpi_total` | KPIs globales del período |
| `get_kpi_por_canal` | Desglose por canal de venta |
| `get_kpi_por_lider` | Ranking de líderes de equipo |
| `get_kpi_por_jefe` | Ranking de jefes comerciales |
| `get_chart_jefes` | Gráfica de líneas por jefe |
| `get_chart_lideres` | Gráfica de líneas por líder |
| `get_chart_yoy` | Comparativa Year-over-Year |

---

## 📊 Ejemplos de uso

### Consulta simple

**Usuario:** "¿Cómo vamos este mes?"

**Agente:**
```
📊 *KPI Total — Abril 2026*

*Créditos:* 1,234
*Monto total:* S/. 45,678,900
*Ticket promedio:* S/. 37,000

📈 Crecimiento sostenido vs. mes anterior
```

### Desglose por dimensión

**Usuario:** "¿Qué canal tuvo mayor colocación?"

**Agente:**
```
📊 *KPI por Canal — Abril 2026*

*Patios:* S/. 25,000,000 (55%)
*Konecta:* S/. 12,000,000 (26%)
*Vertice:* S/. 8,678,900 (19%)

📈 Patios mantiene liderazgo
```

### Gráfica automática

**Usuario:** "Dame una gráfica de los últimos 6 meses"

**Agente:** [Envía PNG con gráfica de líneas]

---

## 🔒 Seguridad

### Por qué es seguro

1. **GPT-4o NUNCA toca la BD directamente** — solo llama a funciones específicas que nosotros definimos
2. **La API actúa como firewall** — solo expone los datos que decidimos exponer
3. **Sin SQL directo** — el agente no puede hacer queries arbitrarias
4. **Webhook verificado** — Meta solo envía requests a nuestro servidor verificado
5. **HTTPS obligatorio** — toda comunicación encriptada

### Capas de seguridad

```
CAPA EXTERNA — IA (GPT-4o)
  Solo habla con funciones controladas
  No tiene acceso directo a sistemas internos
      ↓
CAPA INTERMEDIA — API Santander
  Expone solo los datos permitidos
  Actúa como filtro y guardián
      ↓
CAPA INTERNA — Base de Datos
  Nunca accedida directamente por la IA
  Protegida detrás de la API
```

---

## 📝 Variables de entorno

Ver `.env.template` para la lista completa.

Mínimo requerido:

```bash
SANTANDER_API_URL=https://prod-XX.westus.logic.azure.com/workflows/...
OPENAI_API_KEY=sk-...
WHATSAPP_PHONE_NUMBER_ID=123456789
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxx
WHATSAPP_VERIFY_TOKEN=santander-wsp-2026
```

---

## 🧪 Testing

```bash
# CLI interactivo
python main.py

# Servidor local (sin WhatsApp)
uvicorn server:app --reload

# Probar endpoint de salud
curl http://localhost:8000/health
```

---

## 📂 Estructura del proyecto

```
santander-fc-llm/
├── agent.py              # Loop de function calling con GPT-4o
├── config.py             # Configuración centralizada
├── main.py               # CLI interactivo
├── server.py             # FastAPI webhook server
├── session_store.py      # Persistencia de sesiones
├── tools/
│   ├── schemas.py        # Definición de tools para el LLM
│   ├── handlers.py       # Implementación de cada tool
│   └── registry.py       # Mapeo nombre → función
├── whatsapp/
│   ├── client.py         # Cliente HTTP para enviar mensajes
│   └── webhook.py        # Parser de payloads entrantes
├── scripts/
│   ├── setup-server.sh   # Setup inicial del droplet
│   └── setup-ssl.sh      # Configuración SSL
├── .github/workflows/
│   └── deploy.yml        # CI/CD automático
└── requirements.txt      # Dependencias Python
```

---

## 🎓 Aprendizajes clave

### 1. Function Calling es el patrón correcto

**MAL:**
- Pasarle todos los datos al LLM → caro, lento, poco preciso

**BIEN:**
- Definir herramientas específicas → el LLM decide cuál usar → solo traemos los datos necesarios

### 2. La API es el firewall

GPT-4o no conoce la estructura de la BD, no puede hacer SQL directo, no puede modificar nada. Solo puede llamar a funciones que nosotros exponemos.

### 3. WhatsApp requiere HTTPS

Meta NO acepta webhooks HTTP. Necesitás certificado SSL válido (Let's Encrypt es gratis).

### 4. Systemd para producción

No uses `nohup` ni `screen`. Systemd reinicia automáticamente si el proceso muere.

---

## 🚧 Roadmap

- [x] MVP funcional (KPIs + gráficas)
- [x] Deploy a producción (DigitalOcean)
- [x] CI/CD con GitHub Actions
- [ ] Alertas proactivas (ej: "Tu meta del mes está en riesgo")
- [ ] Más dimensiones (productos, zonas, campañas)
- [ ] Dashboard web para ver conversaciones
- [ ] Multi-idioma (quechua, inglés)

---

## 📞 Contacto

**Autor:** Jean Pierre Llanos  
**Proyecto:** Hackathon Interna de IA — Santander Perú  
**Repo:** https://github.com/llanosjp/santander-fc-llm

---

## 📄 Licencia

Uso interno — Santander Perú  
Este proyecto fue desarrollado como iniciativa propia para el área de IA.

---

## ⭐ Lo que hace esto especial

No es un chatbot con respuestas pre-cargadas.  
No es un dashboard que requiere capacitación.  
Es un **compañero de trabajo** que habla tu idioma y tiene acceso a los datos que necesitás.

**Preguntale lo que quieras — él sabe dónde buscar.**
