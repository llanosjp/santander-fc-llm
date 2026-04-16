#!/bin/bash
#
# Configurar SSL con Let's Encrypt (OBLIGATORIO para WhatsApp webhook)
# Ejecutar como root: bash setup-ssl.sh TU_DOMINIO
#

set -e

if [ -z "$1" ]; then
    echo "❌ Error: debes especificar el dominio"
    echo "Uso: bash setup-ssl.sh agente.tudominio.com"
    exit 1
fi

DOMAIN=$1

echo "🔒 Configurando SSL para $DOMAIN..."

# ── 1. Actualizar configuración de nginx con el dominio ──────────────────────
cat > /etc/nginx/sites-available/santander-llm << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

nginx -t
systemctl reload nginx

# ── 2. Obtener certificado SSL con certbot ───────────────────────────────────
echo "📜 Obteniendo certificado SSL..."
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --register-unsafely-without-email --redirect

echo ""
echo "✅ SSL configurado correctamente"
echo ""
echo "🌐 Tu webhook URL es: https://$DOMAIN/webhook"
echo ""
echo "📋 Configurar en Meta Developer Portal:"
echo "   1. WhatsApp → Configuration → Webhook"
echo "   2. Callback URL: https://$DOMAIN/webhook"
echo "   3. Verify Token: santander-wsp-2026"
echo "   4. Webhook Fields: messages"
echo ""
