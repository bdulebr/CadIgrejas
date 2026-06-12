<#
.SYNOPSIS
Instala o PostgreSQL 17 via Winget e configura o banco "intranet_pve".
Requer execução como Administrador.
#>

if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Warning "Por favor, execute este script como Administrador!"
    Exit
}

Write-Host "Iniciando instalação do PostgreSQL 17..." -ForegroundColor Cyan

# Instalar Postgres via Winget
winget install --id PostgreSQL.PostgreSQL --silent --accept-package-agreements --accept-source-agreements

# Esperar alguns segundos para os serviços subirem
Start-Sleep -Seconds 10

# Caminho padrão do psql no Windows
$psql_path = "C:\Program Files\PostgreSQL\17\bin\psql.exe"

if (Test-Path $psql_path) {
    Write-Host "Configurando Banco de Dados e Usuários..." -ForegroundColor Cyan
    
    # Criar Role (erp_admin)
    & $psql_path -U postgres -c "CREATE USER erp_admin WITH PASSWORD 'PVE@MasterDB2026!';"
    & $psql_path -U postgres -c "ALTER ROLE erp_admin SET client_encoding TO 'utf8';"
    & $psql_path -U postgres -c "ALTER ROLE erp_admin SET default_transaction_isolation TO 'read committed';"
    & $psql_path -U postgres -c "ALTER ROLE erp_admin SET timezone TO 'America/Sao_Paulo';"
    
    # Criar DB
    & $psql_path -U postgres -c "CREATE DATABASE intranet_pve;"
    
    # Privilégios
    & $psql_path -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE intranet_pve TO erp_admin;"

    Write-Host "Instalação e Configuração Concluídas!" -ForegroundColor Green
    Write-Host "Adicione isso no seu .env local: DATABASE_URL=postgres://erp_admin:PVE@MasterDB2026!@localhost:5432/intranet_pve" -ForegroundColor Yellow
} else {
    Write-Error "A instalação falhou ou o diretório psql.exe não foi encontrado."
}
