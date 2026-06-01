# Plano de Ação: Deploy Produção & Mobile API

Este plano consolida as 7 etapas cruciais para migrar a Intranet do ambiente de desenvolvimento local (Windows) para o Servidor de Produção Oficial (VPS Linux Ubuntu 24.04) operando sob HTTPS, além de preparar a fundação para o futuro App Android.

## 1. Revisão e Refatoração da API (Mobile Ready)
- **Diagnóstico:** O Django REST Framework (DRF) já está instalado, mas precisamos garantir que os serializers cubram todo o banco.
- **Ação:** Revisar o app `/api/`, criando ou atualizando Endpoints JWT protegidos para fornecer:
  - Estrutura completa de membros (Dossiê, Cargos, Departamentos)
  - Escalas mensais e leitura de PDFs gerados
  - Feed do Almoxarifado (Itens, Quantidades)
  - Sicronização bidirecional Offline-First (o Android puxará a carga toda e enviará deltas).

## 2. Preparação para Linux Ubuntu 24.04 LTS
- **Diagnóstico:** A infra atual roda em Waitress no Windows. Precisamos de Gunicorn + Nginx.
- **Ação:** Criar arquivos de configuração prontos para o Ubuntu:
  - Script bash automatizado de instalação (`setup_ubuntu.sh`)
  - Configurações do Systemd (`intranet.service` e `intranet.socket`)
  - Configuração de Proxy Reverso Nginx (`nginx.conf`) focado em performance.

## 3. Configuração do Domínio Oficial (HTTPS)
- **Ação:** Preparar o `.env.example` e as configurações do Django para operar estritamente em `https://intranet.pvenseada.org`.
- Ajustar `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS`.
- Configurar flags de segurança rigorosa: `SECURE_SSL_REDIRECT = True`, `SESSION_COOKIE_SECURE = True`.

## 4. Integração Google Workspace for Nonprofits
- **Ação:** Injetar suporte sólido à API do Google.
- Definir credenciais do OAuth2 para SSO (Single Sign-On) "Entrar com Google".
- Configurar envio de E-mails transacionais (SMTP Oficial) através do Workspace (`marcos@pvenseada.org`).
- Conexão nativa com a API do Google Drive (já iniciada no PV Drive) para armazenar os uploads pesados sem consumir HD da VPS.

## 5. Faxina Limpa (Wipe Dev Environment)
- **Ação:** Executar a limpeza terminal do ambiente local antes da transferência:
  - Apagar recursivamente todas as pastas `__pycache__`.
  - Apagar a pasta `venv/` (o Ubuntu terá a dele).
  - Garantir que o `.gitignore` blinde o repositório contra arquivos inúteis.

## 6. Checklist 100% Produção (DevOps)
- **Ação:**
  - Forçar o bloqueio `DEBUG = False`.
  - Ativar o `whitenoise` para compressão máxima (Brotli/Gzip) de CSS/JS (coletar estáticos).
  - Trocar o cache local pelo Redis (opcional) ou Memcached, ou configurar o DB Cache padrão do Django para aguentar alta carga.

## 7. Caçada Extrema a Bugs (Bug Hunt)
- **Ação:** Passar uma malha fina final em todas as views buscando:
  - SQL Injection vulnerabilities ou N+1 queries escondidas.
  - Testar fluxos com e sem permissões de Liderança.
  - Verificar responsividade final de botões e links corrompidos (404).
