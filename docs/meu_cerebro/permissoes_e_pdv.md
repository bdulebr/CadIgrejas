# Atualização do Sistema: Menu Lateral Dinâmico e Reservas PDV

**Data:** 22/06/2026
**Módulos Afetados:** `core`, `permissoes`, `pdv`

## 1. Menu Lateral Dinâmico (Módulo de Permissões)
O sistema agora gerencia a visibilidade do menu lateral de forma dinâmica usando permissões do banco de dados, abandonando a lógica hardcoded de `user.nivel_hierarquico` nos templates.

**Como funciona:**
- O modelo abstrato `PermissaoBase` agora possui o campo `pode_ver_menu (BooleanField, default=False)`.
- Isso foi herdado por `PermissaoMembro`, `PermissaoPerfil` e `PermissaoDepartamento`.
- Foi criado o custom template tag `{% load permissoes_tags %}` no pacote `permissoes`.
- A tag `has_menu_perm(user, modulo_slug)` avalia as permissões do usuário e retorna `True` se alguma regra conceder `pode_ver_menu`. SuperAdmins e Sysadmins recebem bypass automático (`True`).
- O `core/templates/core/base.html` foi refatorado para exibir seções (`midia`, `pdv`, `tesouraria`, etc.) usando `{% if request.user|has_menu_perm:'slug' %}`.

## 2. Sistema de Reservas no Frente de Caixa (Módulo PDV)
Foi adicionada a funcionalidade de fazer "Reserva" de itens diretamente no Frente de Caixa.

**Como funciona:**
- O modelo `Venda` (`pdv/models.py`) recebeu:
  - `tipo_venda` (`imediata` ou `reserva`)
  - `status_pagamento` (`pago` ou `pendente`)
  - `status_entrega` (`entregue` ou `retirar`)
  - `nome_cliente_reserva`
- No template `frente_caixa.html` (Alpine.js), foi adicionado o botão "Reservar" (F9), que captura o nome do cliente e o status do pagamento (pago ou na retirada).
- A view `api_finalizar_venda` processa o payload JSON e **somente envia para o Livro Caixa (MovimentoCaixa)** se `status_pagamento == 'pago'`.
- Foi adicionada a tela flutuante (modal) de "Reservas Pendentes" (F7), alimentada pelas novas views `api_listar_reservas` e `api_atualizar_reserva`, permitindo ao caixa marcar como pago e/ou marcar como entregue.
