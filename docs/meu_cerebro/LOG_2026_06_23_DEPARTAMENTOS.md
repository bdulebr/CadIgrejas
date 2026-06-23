# Arquitetura do Módulo de Departamentos (v2.0)

## Resumo das Atualizações (23/06/2026)
O módulo de Departamentos foi expandido de um mero organizador de escalas para um **Ecossistema de Gestão de Equipe Completo**.

### 1. Novo Painel de Detalhes (Alpine.js)
A antiga "God View" de detalhes do departamento (`detalhes_departamento.html`) foi segmentada em 6 abas dinâmicas utilizando Alpine.js:
- **Dashboard:** Resumo de voluntários e vagas.
- **Equipe:** Gestão de Líderes, Sub-Líderes, Voluntários e resumo de Uniformes (baseado no `tamanho_camisa` do modelo `Membro`).
- **Escalas:** Motor de inteligência artificial de slots.
- **Cargos:** Cadastro de funções operacionais.
- **Mural:** Avisos integrados na view do setor.
- **Configurações:** Edição de dados do setor e exclusão.

### 2. Novas Funcionalidades Focadas (Sem reinventar a roda)
Ao invés de criar um cofre de arquivos (PV Drive já faz isso) ou um sistema de avaliações novo (Painel do Líder já faz isso), focamos em 3 dores logísticas:

1. **Recrutamento Interno (Vagas):**
   - **Model:** `VagaSetor` e `CandidaturaVaga` em `gestao_membros/models.py`.
   - **Funcionalidade:** O líder do setor cria uma "Vaga" (ex: Baterista). Isso aparece na página global "Servir na Igreja" (`/vagas-abertas/`), onde os membros da congregação se candidatam. O líder recebe os currículos na aba "Recrutamento" do setor e pode Aprovar ou Rejeitar.
   - A aprovação vincula automaticamente o membro ao `membros_ativos` do departamento.

2. **Agenda Interna do Setor (Ensaios):**
   - **Model:** `EventoInternoSetor`.
   - **Funcionalidade:** Separa os ensaios de quinta-feira dos "Cultos Oficiais" (Domingo). O líder agenda encontros internos e a equipe visualiza na aba "Agenda".

3. **Gestão de Uniformes:**
   - **Model:** Propriedade `tamanho_camisa` da model principal `Membro` (`core/models.py`).
   - **Funcionalidade:** A aba de equipe agora agrupa e conta automaticamente o estoque de camisetas necessário para o setor (ex: 5 P, 10 M), facilitando a compra para congressos e eventos.

## Notas Técnicas para a IA (Anti N+1)
Na view `detalhes_departamento`, utilizamos `prefetch_related` extensivamente para carregar tudo em uma tacada só e não derrubar o banco de dados. SEMPRE use isso quando for renderizar as 6 abas:
```python
Departamento.objects.prefetch_related(
    'membros_ativos', 'lideres', 'sub_lideres', 'funcoes',
    'avisos', 'avisos__autor', 'configuracao_slots', 'configuracao_slots__funcao',
    'vagas_abertas', 'vagas_abertas__candidaturas', 'vagas_abertas__candidaturas__membro',
    'eventos_internos'
)
```

## O que DEU ERRADO nesta sessão (Para não repetir)
- **Alucinação Funcional:** Tentei sugerir funcionalidades como "Cofre de Arquivos" e "Gestão Financeira" para os Departamentos. O usuário repudiou fortemente, pois o "PV Drive" e a "Tesouraria" já são módulos maduros. A regra é: **Não sobreponha módulos.**
- **Erros no Flake8:** Tive problemas com variáveis apagadas por acidente (`template_doc`, `csrf_exempt`) na faxina do código. O Flake8 (F821) salvou o dia indicando variáveis e imports não definidos antes de quebrar em produção.
- **Testes de Navegador (Chrome):** O QA autônomo falhou porque a porta de debug remota do Chrome não estava ativa no PC do usuário. Foi impossível realizar o clique nos botões via sub-agente.

(Fim do Log)
