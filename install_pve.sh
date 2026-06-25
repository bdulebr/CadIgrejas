#!/bin/bash
# ==============================================================================
# SCRIPT DE INSTALAÇÃO AUTOMATIZADA: INTRANET PV ENSEADA
# ==============================================================================
# Sistema Operacional Alvo: Ubuntu 22.04 LTS / Debian 11+
# Execução via internet:
# curl -sL https://raw.githubusercontent.com/bdulebr/CadIgrejas/main/install_pve.sh | sudo bash
# ==============================================================================

# Cores para logs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
  ____  _     __  _____                    _
 |  _ \| |   / / | ____| _ __   ___   ___| | __ _
 | |_) | |  / /  |  _|  | '_ \ / __| / _ \ |/ _` |
 |  __/| | / /   | |___ | | | |\__ \|  __/ | (_| |
 |_|   |_|/_/    |_____||_| |_||___/ \___|_|\__,_|

EOF
echo -e "Instalador Automático - Intranet PV Enseada${NC}"
echo "================================================================="

# 1. Checagem de Privilégios Root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}❌ ERRO: Este script deve ser rodado como root (ex: sudo bash install_pve.sh)${NC}"
  exit 1
fi

# Configurações Padrão de Produção (Fornecidas pelo Usuário)
DOMAIN="intranet.pvenseada.org"
ADMIN_EMAIL="marcos@pvenseada.org"
ADMIN_PASS="LMar261614@2025"
PROJECT_DIR="/var/www/intranet_pve"
REPO_URL="https://github.com/bdulebr/CadIgrejas.git"
DB_NAME="pvenseada_db"
DB_USER="pvenseada_admin"
DB_PASS=$(openssl rand -base64 12)

echo -e "${GREEN}✅ Configurações carregadas:${NC}"
echo "Domínio: $DOMAIN"
echo "Diretório: $PROJECT_DIR"
echo "E-mail Admin: $ADMIN_EMAIL"

echo -e "${BLUE}🔄 Passo 1: Atualizando pacotes e instalando dependências...${NC}"
apt-get update -y
apt-get install -y postgresql postgresql-contrib python3-dev libpq-dev python3-venv python3-pip redis-server nginx certbot python3-certbot-nginx git curl

echo -e "${BLUE}🐘 Passo 2: Configurando Banco de Dados (PostgreSQL) e Redis...${NC}"
systemctl start postgresql
systemctl enable postgresql
systemctl start redis-server
systemctl enable redis-server

# Cria Banco e Usuário
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "Banco já existe."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" 2>/dev/null || sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASS';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET timezone TO 'America/Sao_Paulo';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

echo -e "${BLUE}📦 Passo 3: Clonando Repositório e Configurando Projeto...${NC}"
if [ -d "$PROJECT_DIR" ]; then
    echo "⚠️ Diretório $PROJECT_DIR já existe. Atualizando código via git pull..."
    cd $PROJECT_DIR
    git reset --hard
    git pull origin main
else
    git clone $REPO_URL $PROJECT_DIR
    cd $PROJECT_DIR
fi

# Acertar permissões iniciais
chown -R root:www-data $PROJECT_DIR
chmod -R 775 $PROJECT_DIR

echo -e "${BLUE}🐍 Passo 4: Criando Virtual Environment e Instalando Pacotes...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install psycopg2-binary daphne
pip install -r requirements.txt

echo -e "${BLUE}🔧 Passo 5: Gerando arquivo .env Seguro...${NC}"
ENV_FILE="$PROJECT_DIR/.env"
SECRET_KEY_GEN=$(openssl rand -base64 50 | tr -d '\n')
cat > $ENV_FILE <<EOF
SECRET_KEY=$SECRET_KEY_GEN
DEBUG=False
USE_HTTPS=True
ALLOWED_HOSTS=*
BASE_URL=https://$DOMAIN
USE_REDIS=True
REDIS_URL=redis://127.0.0.1:6379/1
DATABASE_URL=postgres://$DB_USER:$DB_PASS@127.0.0.1:5432/$DB_NAME
EOF

echo -e "${BLUE}🔨 Passo 6: Migrações, Estáticos e Criação de Admin...${NC}"
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput

python manage.py shell -c "
from core.models import Membro;
if not Membro.objects.filter(username='$ADMIN_EMAIL').exists():
    Membro.objects.create_superuser('$ADMIN_EMAIL', '$ADMIN_EMAIL', '$ADMIN_PASS');
    print('✅ Super-admin ($ADMIN_EMAIL) criado com sucesso!')
else:
    user = Membro.objects.get(username='$ADMIN_EMAIL')
    user.set_password('$ADMIN_PASS')
    user.save()
    print('✅ Senha do Super-admin ($ADMIN_EMAIL) resetada com sucesso!')
"

echo -e "${BLUE}🔥 Passo 7: Criando Serviço do Daphne (WebSockets & Django Channels)...${NC}"
SERVICE_FILE="/etc/systemd/system/intranet_pve.service"
cat > $SERVICE_FILE <<EOF
[Unit]
Description=Daphne daemon para a Intranet PV Enseada (ASGI)
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="DJANGO_SETTINGS_MODULE=intranet.settings"
ExecStart=$PROJECT_DIR/venv/bin/daphne -b 127.0.0.1 -p 8000 intranet.asgi:application
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl stop intranet_pve 2>/dev/null
systemctl start intranet_pve
systemctl enable intranet_pve

echo -e "${BLUE}🌐 Passo 8: Configurando Nginx Reverso...${NC}"
NGINX_CONF="/etc/nginx/sites-available/intranet_pve"
cat > $NGINX_CONF <<"EOF"
server {
    listen 80;
    server_name SERVER_DOMAIN;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        root SERVER_PROJECT_DIR;
    }

    location /media/ {
        root SERVER_PROJECT_DIR;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
sed -i "s/SERVER_DOMAIN/$DOMAIN/g" $NGINX_CONF
sed -i "s|SERVER_PROJECT_DIR|$PROJECT_DIR|g" $NGINX_CONF

ln -sf /etc/nginx/sites-available/intranet_pve /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl restart nginx

echo -e "${BLUE}🔒 Passo 9: Emitindo Certificado SSL (Let's Encrypt)...${NC}"
certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m $ADMIN_EMAIL --redirect

# Ajustar permissões da pasta media caso a aplicação tenha criado pastas como root
chmod -R 775 $PROJECT_DIR/media
chown -R root:www-data $PROJECT_DIR/media

echo "================================================================="
echo -e "${GREEN}🎉 INSTALAÇÃO DA INTRANET CONCLUÍDA COM SUCESSO!${NC}"
echo "================================================================="
echo "Acesse: https://$DOMAIN"
echo "Login: $ADMIN_EMAIL"
echo "Senha: $ADMIN_PASS"
echo ""
echo "Comandos Úteis:"
echo "Ver logs do sistema: journalctl -u intranet_pve -f"
echo "Reiniciar sistema: systemctl restart intranet_pve"
echo "================================================================="
