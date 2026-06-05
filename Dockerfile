# Dockerfile para Produção (Ubuntu Server)
FROM python:3.12-slim

# Evita que o Python grave arquivos .pyc e força o stdout/stderr desbuffered
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala dependências do sistema necessárias para compilar bibliotecas e rodar PostgreSQL
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        python3-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho dentro do container
WORKDIR /app

# Copia e instala as dependências
COPY requirements.txt /app/
# Tenta converter o arquivo para UTF-8 caso venha do Windows em UTF-16
RUN iconv -f UTF-16LE -t UTF-8 requirements.txt > requirements_utf8.txt || cp requirements.txt requirements_utf8.txt
RUN pip install --upgrade pip && pip install -r requirements_utf8.txt

# Copia o restante do código
COPY . /app/

# Coleta arquivos estáticos automaticamente no build (opcional, pode ser feito no docker-compose command)
# RUN python manage.py collectstatic --noinput

# Expor a porta 8000
EXPOSE 8000

# O Comando de inicialização será gerenciado pelo docker-compose para permitir migrações, mas deixamos um padrão:
CMD ["gunicorn", "intranet.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "2", "--timeout", "60"]
