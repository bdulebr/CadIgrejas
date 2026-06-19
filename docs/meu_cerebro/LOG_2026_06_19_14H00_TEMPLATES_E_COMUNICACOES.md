# Log de Atualização - Auditoria e Padronização de Templates de E-mail e PDF
**Data:** 19/06/2026
**Objetivo:** Revisar, criar e unificar o design de todas as comunicações eletrônicas e documentais geradas pelo ERP da Igreja (E-mails e PDFs).

## Problemas Identificados (Descobertas)
- Muitos arquivos `*.html` que eram usados em `enviar_email_html` no módulo de escalas, secretaria e avisos NÃO EXISTIAM fisicamente no código (ex: `nova_escala.html`, `escala_cancelada.html`).
- Módulos antigos (`visitantes`, `ministerio_casais`) ainda disparavam e-mails usando `django.core.mail.send_mail` jogando texto puro no corpo do e-mail ao invés da infraestrutura central `gmail_service`.
- O gerador de PDF de Escalas (`escalas/pdf_generator.py`) tentava buscar o layout no model `TemplateDocumento`. Caso não encontrasse, ele travava o método e não gerava nada.

## Implementações e Resoluções

### 1. Sistema de E-mails
- Foi criado o diretório `core/templates/emails/`.
- Foi criado o `base_email.html`, que injeta dinamicamente o `IGREJA_LOGO`, `IGREJA_NOME` e `IGREJA_CNPJ` (Puxados do `ConfiguracaoSistema`) como cabeçalho e rodapé oficial.
- Foram criados todos os templates faltantes (`boas_vindas.html`, `nova_escala.html`, `escala_atualizada.html`, `escala_cancelada.html`, `termo_lgpd.html`, `novo_aviso.html`, `promocao_hierarquica.html`, `lembrete_curso.html`).
- Refatoração dos signals e views em `visitantes` e `ministerio_casais` para abolir o `send_mail` hardcoded e adotar o `enviar_email_html(..., template_name='...')`.
- *Script de Validação:* Criado `scratch/test_templates.py` que iterou sobre todos os templates de e-mail e confirmou que 100% deles renderizam sem erros de sintaxe Jinja/Django.

### 2. Geração de Documentos (PDF)
- Foi criado o template mestre `core/templates/core/base_pdf.html` usando regras CSS `@page` nativas do `xhtml2pdf` para gerar cabeçalhos flutuantes e paginação automática (`<pdf:pagenumber>`).
- O módulo de **Escalas** foi corrigido. O `pdf_generator.py` agora processa os dados organizados num dicionário e despacha para `escalas/templates/escalas/pdf_escala.html`, o qual implementamos e herda do `base_pdf`.
- Os módulos de **Visitantes** (Relatório Geral e Dossiê Individual), **Almoxarifado** (Termos de Cautela) e **Ministério de Casais** (Relatórios) tiveram seus templates `.html` injetados com `{% extends "core/base_pdf.html" %}`, padronizando todo o sistema de ERP visualmente.

## Como as coisas funcionam agora?
Sempre que precisar criar um e-mail novo ou PDF novo em qualquer módulo:
1. **E-mail:** Crie o HTML com `{% extends "emails/base_email.html" %}`. Para enviar, importe e use `intranet.services.gmail_service.enviar_email_html`.
2. **PDF:** Crie o HTML com `{% extends "core/base_pdf.html" %}`. O script renderiza a string com `render_to_string` e passa para o `xhtml2pdf.pisa`.
