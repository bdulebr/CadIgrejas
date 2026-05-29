# 🚀 Guia Definitivo de Deploy em VPS Linux (Ubuntu 22.04 / 24.04)

Este guia pressupõe que você contratou uma VPS limpa com Ubuntu, tem acesso root/sudo e já apontou o seu domínio (ex: `intranet.pvenseada.org`) para o IP da VPS.

## 1. Preparando o Terreno (Pacotes Iniciais)

Logado via SSH na sua VPS, atualize o sistema e instale os pacotes base:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-venv python3-pip python3-dev libpq-dev postgresql postgresql-contrib nginx curl git -y
```

## 2. Configurando o Banco de Dados (PostgreSQL)

Entre no console do PostgreSQL para criar o banco de dados e o usuário:

```bash
sudo -u postgres psql
```

Dentro do console do PostgreSQL, digite:

```sql
CREATE DATABASE intranet_db;
CREATE USER intranet_user WITH PASSWORD 'sua_senha_super_secreta';
ALTER ROLE intranet_user SET client_encoding TO 'utf8';
ALTER ROLE intranet_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE intranet_user SET timezone TO 'America/Sao_Paulo';
GRANT ALL PRIVILEGES ON DATABASE intranet_db TO intranet_user;
\q
```

## 3. Clonando o Projeto do GitHub

Vá para a pasta `/var/www/` e baixe o repositório:

```bash
cd /var/www/
sudo git clone https://github.com/bdulebr/CadIgrejas.git intranet
cd intranet
```

## 4. Criando o Ambiente Virtual e Instalando Dependências

Crie a `.env` com base no arquivo de exemplo e instale as bibliotecas.

```bash
sudo chown -R $USER:$USER /var/www/intranet
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

# Copiando a ENV
cp .env.example .env
nano .env
```
> [!IMPORTANT]
> Edite a `.env`! Coloque `DATABASE_URL=postgres://intranet_user:sua_senha_super_secreta@localhost:5432/intranet_db`, mude o `ALLOWED_HOSTS`, gere uma `SECRET_KEY` segura e ative as variáveis de HTTPS e Domínio.

## 5. Rodando as Migrações (Banco Limpo)

O PostgreSQL está vazio. Vamos criar as tabelas e o SysAdmin inicial:

```bash
python manage.py migrate
python manage.py collectstatic --noinput

# Criando o Super Usuário Inicial
python manage.py createsuperuser
```

## 6. Configurando o Serviço do Gunicorn (systemd)

Para que o site nunca caia e inicie junto com a máquina, crie um serviço do Gunicorn.

```bash
sudo nano /etc/systemd/system/intranet.service
```

Cole o conteúdo abaixo (ajuste caminhos se necessário):

```ini
[Unit]
Description=Gunicorn daemon para a Intranet PV Enseada
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/intranet
ExecStart=/var/www/intranet/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/var/www/intranet/intranet.sock intranet.wsgi:application

[Install]
WantedBy=multi-user.target
```

Inicie e ative o serviço:

```bash
sudo systemctl start intranet
sudo systemctl enable intranet
```

## 7. Configurando o Nginx (Proxy Reverso)

O Nginx vai receber o tráfego da porta 80 (e depois 443 com SSL) e jogar para o Gunicorn, além de servir as imagens ultrarrápido.

```bash
sudo nano /etc/nginx/sites-available/intranet
```

Cole o conteúdo:

```nginx
server {
    listen 80;
    server_name intranet.pvenseada.org www.intranet.pvenseada.org;

    # Bloqueia tamanho de arquivos maiores que 50MB
    client_max_body_size 50M;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    # Arquivos Estáticos e Mídia
    location /static/ {
        root /var/www/intranet;
    }

    location /media/ {
        root /var/www/intranet;
    }

    # Proxy para o Gunicorn
    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/intranet/intranet.sock;
    }
}
```

Ative o site e reinicie o Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/intranet /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## 8. Segurança e SSL (HTTPS Obrigatório)

Rode o Certbot da Let's Encrypt para colocar o cadeado verde e instalar o certificado SSL:

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d intranet.pvenseada.org -d www.intranet.pvenseada.org
```

## 🎉 Pronto!
O sistema está no ar! Sempre que quiser atualizar o código, basta rodar:
```bash
cd /var/www/intranet
git pull origin main
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart intranet
```
