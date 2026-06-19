# Log de Arquitetura: Padronização de URLs Cloud-Native e HTMX Polling

**Data/Hora**: 19/06/2026 19:47

## O Que Foi Feito
- **HTMX Polling no Check-in**: Implementada a funcionalidade de "Real-Time" sem a necessidade de instanciar novos canais de WebSocket. Utilizamos a diretiva HTMX `hx-get` combinada com `hx-trigger="every 5s"` no container de Check-ins Hoje do módulo de Escalas. O HTMX busca a página completa de fundo e faz o `hx-swap="outerHTML"` apenas no grid designado via `hx-select`.
- **Refatoração de URLs Absolutas (Cloud-Native)**:
  - Detectou-se que o sistema dependia fortemente de `request.build_absolute_uri()` e `request.get_host()`.
  - Essas funções em Python/Django tendem a falhar ou retornar IPs locais (`127.0.0.1` ou `localhost`) quando a aplicação está rodando em VPS de Produção (Linux) por trás de servidores ASGI como Waitress/Daphne e Reverse Proxies como Nginx, comprometendo QR Codes e E-mails.
  - A solução foi adotar estritamente a variável global `BASE_URL` (puxada do arquivo `.env` via `django-environ`).
  - O `BASE_URL` foi inserido no context processor em `core/context_processors.py` para acesso em todo e qualquer template (`{{ BASE_URL }}`).
  - Todos os geradores de QR Code (Almoxarifado, Visitantes) e disparos de E-mail com links Mágicos (Ministério de Casais, Gestão de Membros) foram migrados para usar `settings.BASE_URL`.

## Auditoria e Validação (Spider)
- Após a migração em massa, o robô Spider (`run_spider.py`) foi executado e concluiu o fuzzing de 222 endpoints e 82 tabelas do Banco de Dados retornando **0 Erros**.
- Um erro anterior reportado pelo Spider (Erro 500 no PDF Individual de Casais gerado pela restrição negativa de `availWidth` do xhtml2pdf) foi devidamente mitigado adicionando proporções explícitas (width em `%`) no `<th>` das tabelas HTML do template.

## Aprendizado para a IA de Auto-Reparo
O arquivo de lições do AI Daemon (`docs/meu_cerebro/ai_daemon/LESSONS.md`) foi alimentado com a regra de nunca utilizar `request.build_absolute_uri()` para montagem de links absolutos de infraestrutura e sobre as armadilhas de largura de tabela em `xhtml2pdf`.
