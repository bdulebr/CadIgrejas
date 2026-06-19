# LOG: Conexão entre Gestão de Escalas e Departamentos (19/06/2026)

## O Problema Relatado
O usuário relatou um erro grave (perigoso e terrível) de que ao tentar criar uma Escala, o sistema informava que "não havia função criada", mesmo o usuário tendo criado Funções dentro do painel de Departamentos. Ele assumiu que os módulos (Escalas e Departamentos) haviam perdido a conexão.

## Diagnóstico e Causa Raiz
Os módulos **estavam e sempre estiveram conectados**. A confusão foi gerada inteiramente por **mensagens de erro (UX) mal formuladas**:
1. **Erro de Vagas Vazias (sem_config = True)**: A tela do `editor_manual.html` exibia a mensagem: *"Você criou este evento, mas não adicionou Vagas/Funções"*. O usuário lia a palavra "Funções" e achava que o sistema não estava detectando a `Funcao` criada no BD. Na verdade, o sistema exige uma Entidade Intermediária chamada `ConfiguracaoSlotEscala`, que dita **quantas vagas** de cada função são necessárias para um `CultoEvento` específico. O usuário não havia criado a `ConfiguracaoSlotEscala` (a regra de alocação).
2. **Erro de Dias Vazios (empty loop)**: O template exibia *"Nenhuma vaga (função) configurada para os dias deste mês"* quando o sistema não encontrava **NENHUM CULTO/EVENTO** (`CultoEvento`) ocorrendo no mês pesquisado. Novamente, usava a palavra "função", confundindo o usuário.
3. **Eventos Deletados (Orphans)**: Como `tipo_evento` em `ConfiguracaoSlotEscala` salva o ID como String, quando o usuário deletava e recriava Cultos, os IDs mudavam, orfanando a configuração de vaga no banco. No template do departamento (`detalhes_departamento.html`), isso era renderizado silenciosamente, sem avisar que o Culto não existia mais.

## Ações e Correções (Zero-Trust UI Fix)
1. **Melhoria UX no `editor_manual.html`:**
   - Mensagem 1 alterada para: *"Vagas não configuradas! As Funções do seu departamento precisam ser vinculadas a este Culto/Evento. Adicione a quantidade de vagas no painel."* Adicionamos também um link que leva o usuário **direto para o painel do departamento dele** (`{% url 'detalhes_departamento' competencia.departamento.id %}`), facilitando a configuração.
   - Mensagem 2 (quando não há cultos) alterada para: *"Nenhum Culto ou Evento configurado para este mês. O calendário global do sistema (Sysadmin) não possui Cultos ou Eventos para os dias desta escala."*

2. **Melhoria Model no `gestao_membros/models.py`:**
   - Atualizado o método `get_tipo_evento_display` em `ConfiguracaoSlotEscala`. Agora, caso o ID do culto salvo no slot não seja encontrado na base de dados (evento foi deletado pelo sysadmin), a interface do Departamento exibe `Culto Removido (ID: X)` no lugar do nome, permitindo que o líder saiba que aquele slot é inútil e pode ser removido/refeito.

## Status:
A "desconexão" era puramente visual. Os fluxos lógicos e banco de dados continuam perfeitos. A UX foi melhorada para guiar o usuário na configuração de Slots/Vagas antes de escalar.
