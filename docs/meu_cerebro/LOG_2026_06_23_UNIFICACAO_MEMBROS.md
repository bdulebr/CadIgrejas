# Unificação de Perfil e Isolamento de Dossiê RH

Data: 23/06/2026

## Alterações Arquiteturais

1. **Remoção de Dados Sensíveis:** O campo `anotacoes_lideranca` foi extirpado do model principal `Membro` (core/models.py). Isso impede vazamentos de anotações privadas no 'Meu Perfil' do voluntário.
2. **Isolamento de RH:** Criado o model `AnotacaoRH` em `gestao_membros.models`. Agora, líderes inserem e leem notas confidenciais **exclusivamente** na aba de RH/Dossiê (`/painel-lider/rh/dossie/<id>/`). O histórico (quem e quando anotou) fica guardado e seguro.
3. **Unificação Visual:** As telas de 'Meu Perfil', 'Novo Membro' (admin) e 'Edição de Membro' utilizam agora um único componente mestre (`core/components/form_perfil_mestre.html`), garantindo uniformidade em todo o sistema. A engrenagem do Painel do Líder foi alterada para apontar direto para o Dossiê.

## Testes

- O motor spider (`run_spider.py`) rastreou o banco de dados atualizado e todas as 238 rotas do sistema.
- ZERO (0) ERROS críticos detectados.
