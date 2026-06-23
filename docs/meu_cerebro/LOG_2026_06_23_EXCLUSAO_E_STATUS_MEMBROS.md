# Log de Auditoria - Ajuste de Segurança na Exclusão e Status de Membros

* **Data:** 23/06/2026
* **Módulos Afetados:** Gestão de Membros, Departamentos.

## Motivação (Bug e Requisito)
O usuário relatou duas anomalias cruciais no sistema de Gestão de Membros:
1. **Falha de Exclusão:** O sistema não permitia que absolutamente ninguém apagasse um membro definitivamente (estava bloqueado pela Blindagem Zero-Trust). O usuário solicitou que esse poder fosse concedido exclusivamente a ele (Super Admin).
2. **Falha de Relacionamento (Fantasmas em Departamentos):** Quando o usuário marcava um membro como inativo ("expulso"), esse membro continuava aparecendo nas listas ativas de Departamentos, Escalas e Setores devido à ausência de um gatilho de limpeza automática do relacionamento M2M (`ManyToManyField`). Além disso, o botão de inativar não estava sequer visível no FrontEnd.

## Implementações Técnicas Realizadas

1. **`gestao_membros/views.py` > `excluir_membro()`:**
   - Modificado para verificar `request.user.is_superuser`. Se não for, redireciona com mensagem de erro.
   - Se for, executa o comando irreversível `membro.delete()`, limpando totalmente a base de dados via banco relacional (`CASCADE`).

2. **`gestao_membros/views.py` > `editar_membro()`:**
   - Implementado gatilho para capturar `request.POST.get('status_conta')`.
   - Adicionado mecanismo de segurança reativo: se o status não for igual a `'ativo'`, o sistema fará a varredura e exclusão silenciosa do membro chamando `membro.departamentos_ativos.clear()`, `membro.departamentos_liderados.clear()` e `membro.departamentos_subliderados.clear()`. Isso expulsa a pessoa de qualquer escala e visibilidade departamental instantaneamente.

3. **`core/templates/core/components/form_perfil_mestre.html`:**
   - Adicionado o seletor visual na UI de edição para permitir que líderes configurem o Status da Conta para: `Ativo`, `Pendente`, `Inativo`, `Bloqueado`, `Transferido` ou `Falecido`.

## Validação e Qualidade
- **Banco de Dados:** Testes atestaram que o Django realiza o CASCADE e o `clear()` perfeitamente. Mocks utilizados para o teste foram destruídos logo em seguida.
- **Spider Bot:** Efetuou uma auditoria sobre 242 rotas não detectando regressão nas views após a refatoração.
- **Browser Subagent:** Testou fisicamente os cliques no navegador garantindo que os comboboxes funcionam de ponta a ponta sem erros de JS ou quebras de CSS.

**Status Final:** Resolvido e Blindado. Apenas superusuários podem deletar registros; inativar funciona como um hard-kick interdepartamental.
