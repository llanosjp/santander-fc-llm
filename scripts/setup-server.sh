#!/bin/bash
#
# Setup inicial del servidor DigitalOcean (SOLO SE EJECUTA 1 VEZ)
# Ejecutar como root: bash setup-server.sh
#

set -e

echo "🚀 Configurando servidor para Santander FC LLM..."

# ── 1. Actualizar sistema ─────────────────────────────────────────────────────
echo "📦 Actualizando paquetes del sistema..."
apt update && apt upgrade -y

# ── 2. Instalar dependencias ──────────────────────────────────────────────────
echo "📦 Instalando Python 3.11, nginx, certbot..."
apt install -y python3.11 python3.11-venv python3-pip nginx certbot python3-certbot-nginx git

# ── 3. Crear directorio del proyecto ──────────────────────────────────────────
echo "📁 Clonando repositorio..."
cd /opt
git clone https://github.com/llanosjp/santander-fc-llm.git
cd santander-fc-llm

# ── 4. Crear virtual environment ──────────────────────────────────────────────
echo "🐍 Creando virtual environment..."
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ── 5. Crear archivo .env (usando variables de entorno) ───────────────────────
echo "🔐 Creando archivo .env..."
cat > .env << EOF
SANTANDER_API_URL=${SANTANDER_API_URL}
OPENAI_API_KEY=${OPENAI_API_KEY}
MODEL=gpt-4o
WHATSAPP_PHONE_NUMBER_ID=${WHATSAPP_PHONE_NUMBER_ID}
WHATSAPP_ACCESS_TOKEN=${WHATSAPP_ACCESS_TOKEN}
WHATSAPP_VERIFY_TOKEN=${WHATSAPP_VERIFY_TOKEN}
WHATSAPP_API_VERSION=v19.0
EOF

chmod 600 .env

# ── 6. Crear servicio systemd ──────────────────────────────────────────────────
echo "⚙️ Configurando servicio systemd..."
cat > /etc/systemd/system/santander-llm.service << 'EOF'
[Unit]
Description=Santander FC LLM - WhatsApp Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/santander-fc-llm
Environment="PATH=/opt/santander-fc-llm/venv/bin"
ExecStart=/opt/santander-fc-llm/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# ── 7. Configurar nginx ────────────────────────────────────────────────────────
echo "🌐 Configurando nginx..."
cat > /etc/nginx/sites-available/santander-llm << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/santander-llm /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# ── 8. Habilitar e iniciar servicio ───────────────────────────────────────────
echo "🔄 Iniciando servicio..."
systemctl daemon-reload
systemctl enable santander-llm
systemctl start santander-llm
systemctl status santander-llm --no-pager

# ── 9. Configurar firewall ────────────────────────────────────────────────────
echo "🔒 Configurando firewall..."
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable

echo ""
echo "✅ Setup completado"
echo ""
echo "📋 Próximos pasos:"
echo "   1. Configurar DNS apuntando a esta IP"
echo "   2. Ejecutar: bash scripts/setup-ssl.sh TU_DOMINIO"
echo "   3. Configurar GitHub Secrets para CI/CD"
echo ""
echo "🔍 Verificar servicio: systemctl status santander-llm"
echo "🔍 Ver logs: journalctl -u santander-llm -f"
echo ""
