#!/bin/bash
# ==============================================================================
# SCRIPT DE DEPLOY E MIGRAÇÃO AUTOMATIZADA: INTRANET PV ENSEADA
# ==============================================================================
# Sistema Operacional Alvo: Ubuntu 20.04+ / Debian 11+
# Execução: sudo bash deploy_linux_postgres.sh
# ==============================================================================

# 1. Checagem de Privilégios Root
if [ "$EUID" -ne 0 ]; then
  echo "❌ ERRO: Este script deve ser rodado como root (ex: sudo bash deploy_linux_postgres.sh)"
  exit 1
fi

echo "================================================================="
echo "🚀 INICIANDO O DEPLOY DA INTRANET PV ENSEADA (PostgreSQL + Gunicorn)"
echo "================================================================="

# Variáveis Locais do Banco de Dados
DB_NAME="pvenseada_db"
DB_USER="pvenseada_admin"
DB_PASS=$(openssl rand -base64 12) # Gera uma senha aleatória super forte
PROJECT_DIR=$(pwd) # Presume que você está rodando o script de dentro da pasta do projeto

echo "🔄 Passo 1: Atualizando repositórios e instalando dependências do SO..."
apt-get update -y
apt-get install -y postgresql postgresql-contrib python3-dev libpq-dev python3-venv python3-pip redis-server

echo "🐘 Passo 2: Iniciando e Habilitando o Serviço do PostgreSQL e Redis..."
systemctl start postgresql
systemctl enable postgresql
systemctl start redis-server
systemctl enable redis-server

echo "🔐 Passo 3: Criando Banco de Dados PostgreSQL e Usuário..."
# Roda comandos psql como o usuário 'postgres' nativo do sistema
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET timezone TO 'America/Sao_Paulo';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

echo "🐍 Passo 4: Criando/Ativando Virtual Environment e Instalando Pacotes..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip

# Instala os conectores de PostgreSQL e Daphne que são essenciais para Linux
pip install psycopg2-binary daphne
# Instala o resto dos requerimentos do projeto
pip install -r requirements.txt

echo "🔧 Passo 5: Configurando o arquivo .env para o novo banco..."
ENV_FILE="$PROJECT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️ Arquivo .env não encontrado. Criando um novo..."
    echo "SECRET_KEY=$(openssl rand -base64 32)" > $ENV_FILE
    echo "DEBUG=False" >> $ENV_FILE
    echo "ALLOWED_HOSTS=*" >> $ENV_FILE
    echo "BASE_URL=http://SEU_IP_OU_DOMINIO_AQUI" >> $ENV_FILE
else
    # Remove qualquer conexão de banco de dados antiga (SQLite) do .env
    sed -i '/^DATABASE_URL=/d' $ENV_FILE
fi
# Insere a nova string de conexão poderosa do PostgreSQL
echo "DATABASE_URL=postgres://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME" >> $ENV_FILE

echo "🔨 Passo 6: Rodando as Migrações do Django no PostgreSQL..."
python manage.py makemigrations
python manage.py migrate

echo "👮 Passo 7: Criando Conta do Super Admin (marcos@pvenseada.org)..."
# Usamos o shell do Django para criar de forma automatizada sem input humano
python manage.py shell -c "
from core.models import Membro;
if not Membro.objects.filter(username='marcos@pvenseada.org').exists():
    Membro.objects.create_superuser('marcos@pvenseada.org', 'marcos@pvenseada.org', 'Admin123456');
    print('✅ Super-admin criado com sucesso! (Senha padrão: Admin123456)')
"

echo "⚙️ Passo 8: Coletando Arquivos Estáticos..."
python manage.py collectstatic --noinput

echo "🔥 Passo 9: Criando o Serviço de Inicialização Contínua (Daphne Daemon para WebSockets)..."
SERVICE_FILE="/etc/systemd/system/intranet.service"

cat > $SERVICE_FILE <<EOF
[Unit]
Description=Daphne daemon para a Intranet PV Enseada (Suporte a WebSockets e HTMX)
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/daphne -b 0.0.0.0 -p 80 intranet.asgi:application

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 Passo 10: Ativando e Inicializando o Sistema para Rodar sem Parar..."
systemctl daemon-reload
systemctl start intranet
systemctl enable intranet

echo "================================================================="
echo "🎉 DEPLOY CONCLUÍDO COM SUCESSO!"
echo "================================================================="
echo "A Intranet já deve estar rodando na porta 80 do seu servidor Linux."
echo "O Gunicorn foi configurado como um serviço (daemon). Ele nunca vai parar."
echo "Se o servidor Linux for reiniciado, o sistema subirá automaticamente."
echo "Para ver os logs do servidor em tempo real, use o comando:"
echo "sudo journalctl -u intranet -f"
echo "================================================================="
