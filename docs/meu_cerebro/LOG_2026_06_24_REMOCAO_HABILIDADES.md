# LOG - 24/06/2026 - Remoção Completa das Habilidades do Sistema

## Problema Identificado
Com a introdução e o amadurecimento do modelo de `Funções Departamentais`, o conceito anterior de `Habilidades` e `Talentos` tornou-se completamente inútil e redundante, gerando ruído cognitivo no usuário e na Inteligência Artificial (Motores de Automação Gemini/Groq).

## Solução Arquitetural
Todo o ecossistema de Habilidades foi erradicado e substituído de forma centralizada pelo ecossistema de Funções, simplificando as lógicas de Escala e RH.

## Modificações Realizadas:
1. **Modelos (Banco de Dados)**:
    - O model `Habilidade` em `gestao_membros/models.py` foi **deletado**.
    - O campo M2M `habilidades` no model `Membro` (core/models.py) foi **deletado**.
    - O campo M2M `requisitos` na `Funcao` (gestao_membros/models.py) foi **deletado**.
    - Foram geradas e aplicadas as migrações: `core/migrations/0034_remove_membro_habilidades.py` e `gestao_membros/migrations/0018_remove_funcao_requisitos_delete_habilidade.py`.

2. **Frontend UI**:
    - O quadro `Habilidades / Talentos` foi removido da aba `Disponibilidade / RH` no Formulário Mestre de Perfil.
    - A opção de criar habilidades dentro do painel do Departamento foi removida do template `detalhes_departamento.html`.

3. **Motores de IA**:
    - Os prompts dos motores (`gemini_ai.py` e `groq_ai.py`) que realizam as alocações automáticas de escalas foram limpos para remover a exigência ou correlação com "Habilidades". O JSON de payload do motor foi enxugado.

4. **Backend/Admin**:
    - Todos os forms, views de adição/edição de membro, dashboard de liderança e Admin Django foram limpos. O Spider executou auditoria global retornando 0 erros.

## Regras Atuais de Negócio
- Para escalar alguém automaticamente, o motor deve cruzar o `departamentos_ativos` e o `funcoes_associadas` do voluntário com os eventos gerados.
- Nenhum voluntário pode ser escalado se a Função do Evento não estiver contida na lista de `funcoes_associadas` que o usuário ativou no seu perfil.
- Se a função estiver sem nenhum membro habilitado para ela, a IA emitirá um aviso "Funções sem voluntários compatíveis não foram preenchidas." e pulará o preenchimento.
