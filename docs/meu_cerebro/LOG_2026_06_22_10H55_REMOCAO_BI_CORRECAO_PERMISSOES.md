# Log de Atualização: Remoção Módulo BI e Correção de Permissões
Data: 22 de Junho de 2026

## 1. Remoção do Módulo Business Intelligence (BI)
Conforme solicitação, o módulo de Business Intelligence (BI) foi completamente removido do sistema, visto que os próprios módulos individuais já contêm seus relatórios personalizados, tornando o BI genérico redundante.

### Ações Realizadas:
- Removidas as views `bi_dashboard_geral`, `bi_data_async` e `ai_insights_bi` em `core/views.py`.
- Excluídas as rotas relacionadas ao BI em `core/urls.py`.
- Deletada a pasta de templates `core/templates/core/pages/bi_*` (dashboard e views parciais de BI).
- Removida a referência (link no menu lateral) ao Painel BI no arquivo `core/templates/core/base.html`.
- Script de limpeza executado com sucesso para remover artefatos soltos.

## 2. Correção de Erro Crítico Identificado pelo Spyder (AI Watchdog)
Durante a auditoria rodando o Spyder (`manage.py run_spider`), foi detectado um erro 500 nas rotas `/perfil/` e `/sysadmin/` referente a `AttributeError: 'Membro' object has no attribute 'departamento_responsavel'`.

### Problema:
Na tag customizada `permissoes_tags.py`, havia uma checagem obsoleta e errônea `if user.departamento_responsavel:`. O model `Membro` não possui o atributo `departamento_responsavel`, e sim uma relação `departamentos_liderados`.

### Solução:
- O código em `permissoes/templatetags/permissoes_tags.py` foi corrigido para verificar `user.departamentos_liderados` através de `hasattr(user, 'departamentos_liderados')`.
- Caso o usuário seja líder em um ou mais departamentos com a permissão ativada, a regra de permissão é aplicada corretamente através do filtro `departamento__in=user.departamentos_liderados.all()`.
- Validação executada via `Client` do Django Test e confirmada resposta 200 OK nos endpoints `/perfil/` e `/sysadmin/`.

## 3. Checklist e Finalização
Todas as tecnologias (Backend, Frontend Django e Banco de Dados) estão sincronizadas. Não há views quebradas ou anomalias residuais remanescentes no código referentes à exclusão do BI.
