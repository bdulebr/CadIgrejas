# Registro de Memória (Cérebro do Agente)
## Data: 22 de Junho de 2026 - 15h40
## Assunto: Arquitetura Global do Motor de WhatsApp API

### Contexto
O usuário solicitou que o sistema de E-mails com contingência e reenvios automáticos fosse integralmente replicado para a Meta Cloud API (WhatsApp). A meta era "espelhar" as tabelas, as rotinas de fundo e conectar todos os envios de sistemas para alertar também via WhatsApp usando os "templates de mensagens" configurados.

### O que foi construído
1. **Modelagem de Dados**:
   - `LogWhatsApp` em `core/models.py`. Retém o Destinatário, o Template usado e o *payload exato* em JSON (`corpo_json`) além de gravar as `erro_mensagem`.
   - Adicionada `intervalo_reenvio_whatsapp_horas` em `ConfiguracaoSistema`.

2. **Serviço Core (`intranet/services/whatsapp_service.py`)**:
   - A classe `WhatsAppClient` foi reescrita. A função interna `_execute_request` agora é a única porta de saída, o que garante que TODO disparo passe pela gravação de log.
   - Criada a rotina de *sanitização profunda* de telefones, forçando o formato internacional (55) exigido pela Meta, limpando traços e parênteses.
   - Implementado o `enviar_whatsapp_template()` capaz de renderizar arquivos `.txt` (como `escala_atualizada.txt`) simulando o motor de templates do Facebook para testes locais via texto puro.
   - Implementado o `reenviar_whatsapp_falho(log_id)` que puxa o payload JSON e dispara novamente.

3. **Automação (CRON) e Integração**:
   - Adicionado Job em `core/scheduler.py` chamado `reenviar_whatsapp_pendentes_job`.
   - Adicionado envio via API nos endpoints de Criação, Atualização e Deleção de Escalas em `escalas/views.py`.

4. **Frontend / SysAdmin**:
   - Uma aba idêntica à de e-mails foi introduzida no painel. O sysadmin agora enxerga individualmente falhas e sucessos, o motivo do erro na API da Meta e possui o botão azul "Reenviar Todas as Falhas".
