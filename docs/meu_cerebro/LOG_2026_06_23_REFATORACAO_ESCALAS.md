# Auditoria de Refatoração: Módulo Gestão de Escalas

**Data:** 23/06/2026
**Autor:** Antigravity (IA)
**Objetivo:** Repaginação massiva da UI/UX de Escalas e adição de Instruções Padrões.

## O que foi feito:
1. **Banco de Dados**: Adicionado o campo `instrucoes_padrao_escala` (TextField) na tabela `Departamento` (`gestao_membros/models.py`). Migrações geradas e aplicadas.
2. **Views & Controllers**:
   - Atualizada a view `detalhes_departamento` e criada a nova view `salvar_instrucoes_escala` em `gestao_membros/views.py`.
   - Adicionada a rota `salvar-instrucoes-escala/` em `urls.py`.
3. **Escalas PDF**: Injeção da variável `competencia.departamento.instrucoes_padrao_escala` na base do documento de escalas gerado pelo xhtml2pdf (`pdf_escala.html`).
4. **Painel de Escalas (`painel.html`)**:
   - Refatoração completa com AlpineJS (`x-data="{ aba_ativa: 'gestao' }"`).
   - Divisão clara em 2 Abas: "Escalas Mensais" e "Importar PDF / Excel (IA)".
5. **Editor Manual de Escalas (`editor_manual.html`)**:
   - **Remoção Absoluta de Modais**. O processo de atribuição agora é "Zero-Click Fatigue".
   - Nova **Sidebar Fixa (w-80)** exibindo a listagem de membros vivos.
   - Implementada variável global de estado no AlpineJS (`selectedMemberId`, `selectedMemberName`) com barra de busca real-time.
   - Os slots de escala (*dropzones*) leem a variável selecionada e invocam a alocação instantaneamente via Fetch API ao clicar na vaga desejada.

## Testes & Qualidade
- **Spider**: Varredura confirmou 0 erros em 88 tabelas e 243 endpoints scaneados.
- **Browser Subagent**: Lançado para validar as rotas de escalas após a remoção dos mocks e lixos.
- **Limpeza**: Arquivos mocks removidos de `scratch/*.py`.
