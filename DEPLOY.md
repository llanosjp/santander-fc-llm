# Deploy a DigitalOcean — Santander FC LLM

Guía completa para desplegar el agente en producción con CI/CD automático.

---

## 📋 Pre-requisitos

1. **Droplet de DigitalOcean** creado (Ubuntu 22.04 o superior)
2. **Dominio** apuntando al droplet (o usar IP temporal)
3. **Credenciales de Meta** (Phone Number ID + Access Token)
4. **API de Santander** funcionando (Power Automate URL)
5. **OpenAI API Key** con créditos

---

## 🚀 PASO 1: Setup inicial del servidor (SOLO 1 VEZ)

### 1.1 Conectarse al droplet

```bash
ssh root@TU_IP_DEL_DROPLET
```

### 1.2 Crear variables de entorno

```bash
export SANTANDER_API_URL="https://prod-XX.westus.logic.azure.com/workflows/..."
export OPENAI_API_KEY="sk-..."
export WHATSAPP_PHONE_NUMBER_ID="123456789"
export WHATSAPP_ACCESS_TOKEN="EAAxxxxxxxxxx"
export WHATSAPP_VERIFY_TOKEN="santander-wsp-2026"
```

### 1.3 Descargar y ejecutar setup

```bash
curl -o setup-server.sh https://raw.githubusercontent.com/llanosjp/santander-fc-llm/master/scripts/setup-server.sh
bash setup-server.sh
```

Esto instala:
- Python 3.11 + dependencias
- nginx
- El repo clonado en `/opt/santander-fc-llm`
- Servicio systemd corriendo 24/7
- Firewall configurado

### 1.4 Verificar que funciona

```bash
# Ver logs en tiempo real
journalctl -u santander-llm -f

# Probar endpoint de salud
curl http://localhost:8000/health
```

Deberías ver: `{"status":"ok","sessions":0}`

---

## 🔒 PASO 2: Configurar SSL (OBLIGATORIO para WhatsApp)

### 2.1 Configurar DNS

Crear un registro A apuntando a la IP del droplet:

```
Tipo: A
Nombre: agente (o el subdominio que prefieras)
Valor: TU_IP_DEL_DROPLET
TTL: 300
```

Esperar 5-10 minutos a que propague.

### 2.2 Instalar certificado SSL

```bash
cd /opt/santander-fc-llm
bash scripts/setup-ssl.sh agente.tudominio.com
```

Esto configura automáticamente Let's Encrypt + nginx con HTTPS.

### 2.3 Verificar HTTPS

```bash
curl https://agente.tudominio.com/health
```

---

## 📱 PASO 3: Configurar webhook en Meta

1. Ir a [Meta Developer Portal](https://developers.facebook.com/)
2. WhatsApp → Configuration → Webhook
3. Click en **"Edit"**
4. Completar:
   - **Callback URL:** `https://agente.tudominio.com/webhook`
   - **Verify Token:** `santander-wsp-2026`
5. Click en **"Verify and Save"**
6. Subscribir a **messages** en Webhook fields

Si Meta muestra ✅ verde → **el webhook está funcionando**.

---

## 🔄 PASO 4: Configurar CI/CD con GitHub Actions

### 4.1 Generar SSH key para GitHub Actions

En el **droplet**:

```bash
ssh-keygen -t ed25519 -C "github-actions" -f /root/.ssh/github-actions -N ""
cat /root/.ssh/github-actions.pub >> /root/.ssh/authorized_keys
cat /root/.ssh/github-actions
```

Copiar la **private key** (todo el contenido — desde `-----BEGIN` hasta `-----END`).

### 4.2 Configurar GitHub Secrets

En GitHub → Settings → Secrets and variables → Actions → New repository secret

Crear estos 3 secrets:

| Name | Value |
|------|-------|
| `DROPLET_IP` | Tu IP del droplet (ejemplo: `159.89.123.45`) |
| `DROPLET_USER` | `root` |
| `DROPLET_SSH_KEY` | La private key que copiaste arriba |

### 4.3 Probar deploy automático

```bash
# En tu máquina local
cd /home/jp/projects/santander-fc-llm
git add .
git commit -m "test: verificar CI/CD"
git push origin master
```

En GitHub → Actions → deberías ver el workflow corriendo.

Si termina en ✅ verde → cada push hace deploy automático.

---

## 📊 PASO 5: Verificar que todo funciona

### 5.1 Probar desde WhatsApp

Enviar mensaje al número de WhatsApp de prueba de Meta:

```
¿Cómo van las colocaciones este mes?
```

Deberías recibir respuesta del agente en segundos.

### 5.2 Ver logs del servidor

```bash
journalctl -u santander-llm -f
```

Deberías ver:
- Requests entrantes desde WhatsApp
- Llamadas a OpenAI
- Respuestas enviadas

---

## 🔧 Comandos útiles

```bash
# Ver estado del servicio
systemctl status santander-llm

# Reiniciar servicio
systemctl restart santander-llm

# Ver logs en tiempo real
journalctl -u santander-llm -f

# Ver últimas 100 líneas
journalctl -u santander-llm -n 100

# Actualizar código manualmente
cd /opt/santander-fc-llm
git pull origin master
systemctl restart santander-llm

# Probar endpoint
curl https://agente.tudominio.com/health
```

---

## 🚨 Troubleshooting

### El webhook no verifica en Meta

1. Verificar que el servicio está corriendo:
   ```bash
   systemctl status santander-llm
   ```

2. Verificar que el puerto 443 está abierto:
   ```bash
   ufw status
   ```

3. Probar manualmente el endpoint de verificación:
   ```bash
   curl "https://agente.tudominio.com/webhook?hub.mode=subscribe&hub.verify_token=santander-wsp-2026&hub.challenge=test123"
   ```
   Debería retornar: `test123`

### El agente no responde

1. Ver logs:
   ```bash
   journalctl -u santander-llm -f
   ```

2. Verificar que el `.env` tiene todas las variables:
   ```bash
   cat /opt/santander-fc-llm/.env
   ```

3. Probar el agente manualmente:
   ```bash
   cd /opt/santander-fc-llm
   source venv/bin/activate
   python main.py
   ```

### CI/CD falla

1. Verificar que los GitHub Secrets están bien configurados
2. Ver logs del workflow en GitHub → Actions
3. Verificar que la SSH key está en `authorized_keys`:
   ```bash
   cat /root/.ssh/authorized_keys
   ```

---

## 📝 Variables de entorno

El archivo `.env` se crea automáticamente en el servidor con estas variables:

```bash
SANTANDER_API_URL=<URL de Power Automate>
OPENAI_API_KEY=<API key de OpenAI>
MODEL=gpt-4o
WHATSAPP_PHONE_NUMBER_ID=<ID del número de WhatsApp>
WHATSAPP_ACCESS_TOKEN=<Access token de Meta>
WHATSAPP_VERIFY_TOKEN=santander-wsp-2026
WHATSAPP_API_VERSION=v19.0
```

**NUNCA** commitear el `.env` al repo — está en `.gitignore`.

---

## 🎯 Checklist final

- [ ] Servicio corriendo 24/7
- [ ] HTTPS configurado correctamente
- [ ] Webhook verificado en Meta
- [ ] Agente responde por WhatsApp
- [ ] CI/CD funcionando (push → deploy)
- [ ] Logs sin errores
- [ ] DNS apuntando correctamente
- [ ] Firewall configurado

---

## 📞 Soporte

Si algo falla:
1. Ver logs: `journalctl -u santander-llm -f`
2. Verificar estado: `systemctl status santander-llm`
3. Probar endpoint: `curl https://tu-dominio.com/health`

Todo funcionando = `{"status":"ok","sessions":N}`
