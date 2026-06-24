# Eversinho Agentic AI - Ferramentas Implementadas

## Fase 1: Arsenal de Comando

As seguintes ferramentas de Inteligência Artificial foram implementadas com base no framework Gemini (Function Calling) e com a proteção Zero-Trust do Django (injeção de `request.user` nas tools):

### 1. `gerenciar_membros`
- **Capacidades**: Listar membros do banco de dados (top 10 ordenado e filtrado por nome) e criar novos cadastros (nome, e-mail, telefone).
- **Proteção Zero-Trust**: O backend exige `core.view_membro` para listar e `core.add_membro` para criar. Caso contrário, a ferramenta intercepta e o Eversinho recebe uma negativa de segurança para repassar ao usuário.
- **Integração**: Modifica a tabela `Membro` nativa do sistema.

### 2. `gerenciar_escalas`
- **Capacidades**: Consultar escalas ativas (filtrando por mês/ano e departamento) e criar novas alocações pontuais (Data, Horário de Início e Término, Departamento e Membro).
- **Proteção Zero-Trust**: O usuário precisa ter permissões do módulo de Escalas e, obrigatoriamente, ser **Líder do Departamento** ou **SysAdmin** para inserir voluntários.
- **Anti-Conflito**: Tratamento de exceções capturando restrições de unicidade (`unique_membro_escala_horario_zerotrust`) no banco.

### 3. `gerenciar_dossie`
- **Capacidades**: Sistema confidencial de anotações pastorais. Permite consultar logs recentes de atendimento e registrar novas sessões.
- **Proteção Zero-Trust**: Extrema segurança. Apenas usuários com `ministerio_casais.add_historicoaconselhamentocasal` (Pastores/Conselheiros) conseguem listar ou criar dossiês.
- **Trilha de Auditoria**: O sistema injeta automaticamente o nome completo do Pastor Conselheiro logado na sessão caso ele não seja especificado.

## Status do Spider de Validação
O banco de dados e as rotas foram varridos via Spider pós-implantação.
- **Tabelas Scaneadas**: 89
- **Endpoints Validados**: 243
- **Erros Encontrados**: 0
Nenhum arquivo de Mock ou script de teste corrompeu a execução em produção. Todos foram limpos (`*.pyc` e diretórios `__pycache__` expurgados).

## Renderização de UI (HTMX)
O Eversinho está autorizado e configurado em `core/views.py` para retornar marcação HTML injetável. O painel do chat faz o bypass (através do pacote `markdown`) processando classes do Tailwind CSS e executando o parser automático do HTMX (`htmx.process`) para viabilizar botões dinâmicos de resposta nas conversas futuras.
