#!/bin/bash
# Script de Instalação e Configuração do PostgreSQL 17 (Ubuntu/Debian)

echo "Iniciando instalação do PostgreSQL 17 na VPS..."

# Adicionar repositório oficial do Postgres
sudo apt install curl ca-certificates gnupg -y
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list

# Instalar o Postgres 17
sudo apt update
sudo apt install -y postgresql-17 postgresql-contrib-17

# Iniciar serviço
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Configurar Banco, Usuário e Senha
sudo -u postgres psql -c "CREATE DATABASE intranet_pve;"
sudo -u postgres psql -c "CREATE USER erp_admin WITH PASSWORD 'PVE@MasterDB2026!';"
sudo -u postgres psql -c "ALTER ROLE erp_admin SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE erp_admin SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE erp_admin SET timezone TO 'America/Sao_Paulo';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE intranet_pve TO erp_admin;"

# Liberar porta para localhost (Django e Nginx rodando na mesma máquina)
echo "PostgreSQL 17 instalado com sucesso na porta 5432."
echo "Use DATABASE_URL=postgres://erp_admin:PVE@MasterDB2026!@localhost:5432/intranet_pve no seu .env"
