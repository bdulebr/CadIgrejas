# Registro de Memória (Cérebro do Agente)
## Data: 22 de Junho de 2026 - 14h48
## Assunto: Motor de Webhook WhatsApp (Recebimento Seguro)

### Contexto
Dando continuidade à fundação da Meta Cloud API (WhatsApp), extraímos o complexo motor de segurança em FastAPI que existia no projeto isolado (`API_WHATSAPP_MESQUITA`) e o transcrevemos para rodar nativamente dentro do Django (`CadIgrejas`).
O objetivo é que o sistema não seja "surdo" ao enviar uma mensagem para um membro. Se o membro responder, ou enviar a foto de um comprovante para o número do sistema, o CadIgrejas processará e salvará o arquivo.

### Ações Implementadas
1. **Novos Campos de Segurança (`core/models.py`)**
   - Adicionados `whatsapp_verify_token` (Para responder ao desafio 'subscribe' da Meta) e `whatsapp_app_secret` (Chave criptográfica para validação HMAC SHA-256 das mensagens).

2. **Backend Sysadmin (`core/views.py` e `core/templates/core/pages/sysadmin_dashboard.html`)**
   - Injetamos as caixas de texto protegidas para salvar o Verify Token e o App Secret lado a lado.
   - Refatoramos a View `sysadmin_salvar_whatsapp` para salvar os campos parcialmente (sem sobrescrever campos não enviados).

3. **Motor Webhook (`core/webhooks.py`)**
   - Traduzido o código do antigo `main.py` (FastAPI) para View Django usando `@csrf_exempt`.
   - **Camadas de Segurança Ativas:** Se um pacote não for assinado usando a mesma chave do `App Secret`, a rota retorna HTTP 403 Forbidden.
   - **Download Automático:** Se a mensagem possuir mídia (`image`, `document`), a view chama automaticamente o `whatsapp_service.download_media` e guarda o arquivo na pasta `media/whatsapp_recebidos/`.

4. **Roteamento (`core/urls.py`)**
   - Rota `/webhook/whatsapp/` mapeada no servidor raiz.
