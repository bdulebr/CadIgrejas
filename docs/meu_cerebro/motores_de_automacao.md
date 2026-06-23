# Motores de Automação e CRON Jobs (Background Tasks)

## Arquitetura Geral
O sistema não utiliza Celery para evitar overhead de infraestrutura (Redis/RabbitMQ). Ao invés disso, toda a automação roda *in-memory* ou em threads separadas (no servidor ASGI Daphne ou WSGI Gunicorn).

### 1. APScheduler (`core/scheduler.py`)
O `APScheduler` (Advanced Python Scheduler) foi ativado e gerencia o **CRON** nativamente na inicialização do servidor.
**Injeção do Motor:** Ocorre no `core/apps.py` no método `ready()`. O sistema checa a variável `sys.argv` para garantir que só seja iniciado quando rodar via `daphne`, `hupper`, `gunicorn`, `uvicorn`, `waitress` ou `runserver` (Evita duplicação ao rodar o comando `migrate`).

**Jobs Cadastrados:**
- **`reenviar_emails_pendentes_job` e `reenviar_whatsapp_pendentes_job`:** (Freqüência variável através do SysAdmin) Varre os logs de "Falha" e tenta reenviar as mensagens usando SMTP e WhatsApp.
- **`rotina_diaria_00h` (Meia-noite):** Dispara o comando `rotina_meia_noite` (Faz backup do Banco de Dados SQLite e verifica o Almoxarifado/Validade dos Lotes, criando avisos caso existam produtos vencendo).
- **`rotina_diaria_08h` (Manhã 08:00):** Dispara `enviar_lembretes_curso` (Ministerio de Casais) e `avisar_agendamentos` (Gabinete Pastoral) avisando os membros via WhatsApp/Email sobre os compromissos para o *dia seguinte*.

### 2. AI Daemon (`ai_daemon.py`)
Esse processo não roda no APScheduler! O `AI Auto-Engineer Middleware` requer um monitor contínuo na fila de bugs.
**Injeção do Motor:** Ele é inicializado ativamente através do arquivo de lote `run_prod.bat` como um processo à parte no Windows (`start /B venv\Scripts\python manage.py ai_daemon`).
**Como Funciona:** Em um loop infinito com `time.sleep(5)` de intervalo, ele olha a tabela `AIEngineerLog`. Se achar um erro `PENDENTE`, invoca o motor de Groq/Gemini AI e executa o patch no código-fonte em tempo real (Modo Zero-Trust).

### Limpeza de Legado
- O comando `disparar_lembretes_cursos.py` (antigo no módulo Casais) tentava ler uma coluna inexistente no Banco e era redundante com `enviar_lembretes_curso.py`. Ele foi excluído e a responsabilidade da automação agora está solidamente 100% no motor principal (APScheduler).
