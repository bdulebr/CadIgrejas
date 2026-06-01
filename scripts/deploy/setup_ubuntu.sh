#!/bin/bash
# ==============================================================================
# Script de Instalação Automatizada - Intranet PV Enseada (Ubuntu 24.04 LTS)
# ==============================================================================
# Este script deve ser executado como root na VPS.
# Caminho de Instalação: /var/www/intranet
# ==============================================================================

# 1. Atualização do Sistema
echo "🔄 Atualizando repositórios e pacotes do sistema..."
apt update && apt upgrade -y

# 2. Instalação de Dependências
echo "📦 Instalando dependências (Python, Nginx, SQLite3, Certbot)..."
apt install -y python3.12 python3.12-venv python3-pip python3-dev \
    nginx curl git sqlite3 libsqlite3-dev certbot python3-certbot-nginx

# 3. Preparando o Diretório do Projeto
echo "📁 Preparando diretório /var/www/intranet..."
mkdir -p /var/www/intranet
# Assumindo que o repositório já será clonado aqui, ou já foi.
# Ajuste de permissões (nginx usa o usuário www-data)
chown -R www-data:www-data /var/www/intranet
chmod -R 775 /var/www/intranet

# 4. Criando e Ativando Ambiente Virtual
echo "🐍 Configurando ambiente virtual Python..."
cd /var/www/intranet
sudo -u www-data python3.12 -m venv venv
# Instala as dependências (se o requirements.txt já estiver na pasta)
if [ -f "requirements.txt" ]; then
    echo "⬇️ Instalando pacotes do requirements.txt..."
    sudo -u www-data /var/www/intranet/venv/bin/pip install --upgrade pip
    sudo -u www-data /var/www/intranet/venv/bin/pip install -r requirements.txt
    sudo -u www-data /var/www/intranet/venv/bin/pip install gunicorn  # Garantir o Gunicorn
fi

# 5. Coleta de Estáticos e Migrações de Banco de Dados
echo "⚙️ Configurando Django (Estáticos e Migrações)..."
# É necessário ter o .env configurado aqui para rodar os comandos sem erros
# sudo -u www-data /var/www/intranet/venv/bin/python manage.py collectstatic --noinput
# sudo -u www-data /var/www/intranet/venv/bin/python manage.py migrate

# 6. Configuração do Gunicorn (Systemd)
echo "🚀 Configurando Gunicorn Service e Socket..."
cp /var/www/intranet/scripts/deploy/intranet.socket /etc/systemd/system/
cp /var/www/intranet/scripts/deploy/intranet.service /etc/systemd/system/

systemctl daemon-reload
systemctl start intranet.socket
systemctl enable intranet.socket

# 7. Configuração do Nginx
echo "🌐 Configurando Servidor Nginx..."
cp /var/www/intranet/scripts/deploy/nginx.conf /etc/nginx/sites-available/intranet
ln -sf /etc/nginx/sites-available/intranet /etc/nginx/sites-enabled/
# Remove o site default do Nginx
rm -f /etc/nginx/sites-enabled/default

# Testa e reinicia o Nginx
nginx -t && systemctl restart nginx

# 8. Configuração de SSL (Let's Encrypt / HTTPS)
echo "🔒 Configurando certificado SSL (HTTPS) com Certbot..."
echo "Aviso: O domínio intranet.pvenseada.org precisa já apontar para o IP desta VPS."
# certbot --nginx -d intranet.pvenseada.org --non-interactive --agree-tos -m marcos@pvenseada.org

echo "✅ Instalação base concluída com sucesso! Verifique os status com:"
echo "sudo systemctl status intranet.socket"
echo "sudo systemctl status nginx"
