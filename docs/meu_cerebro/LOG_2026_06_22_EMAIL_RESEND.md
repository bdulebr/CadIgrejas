# Registro de Memória (Cérebro do Agente)
## Data: 22 de Junho de 2026 - 15h15
## Assunto: Motor de Reenvio de E-mails (Manual e CRON)

### Contexto
O usuário solicitou uma feature essencial no módulo SysAdmin: A possibilidade de reenviar e-mails que falharam (seja manualmente um a um, em lote, ou via CRON automático a cada X horas).

### Alterações de Banco de Dados (`core.models`)
- `EmailLog`: Passou a salvar nativamente o `corpo_html` da mensagem no momento do disparo. **Atenção:** Logs gerados antes dessa atualização não poderão ser reenviados (pois o banco não possuía o HTML injetado deles).
- `EmailLog`: Recebeu também o contador `qtd_reenvios`.
- `ConfiguracaoSistema`: Ganhou a variável `intervalo_reenvio_emails_horas`.

### Lógica de Reenvio (`intranet/services/gmail_service.py`)
- Função `reenviar_email_falho(log_id)`: Busca o log por ID, extrai o `corpo_html`, converte para plain text com `strip_tags` (para a versão text/plain), anexa o HTML original e re-dispara usando o `DEFAULT_FROM_EMAIL`. Se sucesso, altera status para `enviado` e limpa a `erro_mensagem`.

### Automação em Segundo Plano (Background CRON)
- Utilizando a biblioteca `APScheduler` (que já estava nos requirements), foi criado o arquivo `core/scheduler.py`.
- O Job foi acoplado dentro de `core/apps.py` (`ready()`). Ele verifica o tempo configurado em `ConfiguracaoSistema` e, de X em X horas, varre o banco rodando o reenvio automático de forma invisível.

### Frontend Sysadmin (`sysadmin_dashboard.html`)
- Inserido input numérico para definir o `intervalo_reenvio_emails_horas`.
- Botão "Reenviar Todas as Falhas" (Batch mode) no cabeçalho da tabela.
- Mini botões "Reenviar" acoplados em cada linha que tenha `status == 'falha'`.
