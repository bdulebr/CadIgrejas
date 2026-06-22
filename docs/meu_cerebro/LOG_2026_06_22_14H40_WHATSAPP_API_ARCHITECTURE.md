# Registro de Memória (Cérebro do Agente)
## Data: 22 de Junho de 2026 - 14h40
## Assunto: Arquitetura de Integração com WhatsApp (Meta Cloud API) e Herança da API Mesquita

### Contexto
O usuário solicitou a preparação do ecossistema do `CadIgrejas` para envios de mensagens e PDFs via WhatsApp de forma corporativa e gratuita, preparando o terreno para quando o sistema subir em uma VPS. Adotamos o caminho da **Meta Cloud API** (Caminho Oficial) devido à escalabilidade e ausência de risco de banimentos para números de negócio.

### Ações Implementadas
1. **Modelagem de Dados (`ConfiguracaoSistema` em `core/models.py`)**
   - Injetamos as variáveis: `whatsapp_ativo` (Master Switch), `whatsapp_phone_number_id` (ID do Celular) e `whatsapp_access_token` (Bearer Token Permanente).

2. **Frontend do Painel Sysadmin (`core/templates/core/pages/sysadmin_dashboard.html`)**
   - Criada a aba "WhatsApp API" com formulário para salvar as chaves sem precisar editar o `.env`.

3. **Backend Sysadmin (`core/views.py` e `core/urls.py`)**
   - Adicionadas rotas e views de Toggle (`sysadmin_toggle_whatsapp`) e Save (`sysadmin_salvar_whatsapp`).

4. **Motor de Disparo (`intranet/services/whatsapp_service.py`)**
   - Sob ordem direta de investigação, auditamos o projeto externo `API_WHATSAPP_MESQUITA` e extraímos a inteligência da classe `WhatsAppClient`.
   - Nossa classe absorveu as capacidades de `send_text`, `send_document`, `send_button_message` e `download_media`.
   - Modificamos a base para consultar as chaves no Django ORM (`ConfiguracaoSistema`) em vez das antigas variáveis do sistema.

### Diretriz para Futuras Implementações
Qualquer módulo no sistema que necessitar de enviar alertas por WhatsApp **NÃO DEVE** consumir bibliotecas de terceiros ou Requests diretos. Deve apenas importar:
```python
from intranet.services.whatsapp_service import enviar_whatsapp_mensagem, enviar_whatsapp_pdf
```
O serviço local lidará com o travamento (Master Switch) e leitura dos tokens.
