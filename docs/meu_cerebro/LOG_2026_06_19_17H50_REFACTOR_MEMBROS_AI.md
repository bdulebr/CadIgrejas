# Refatoração do Módulo de Gestão de Membros (AI Autofill & UX)

**Data**: 19/06/2026
**Autor**: Agente Antigravity / Marcos Lira

## O Problema
O módulo de Gestão de Membros, responsável por cadastrar e administrar voluntários, possuía formulários longos, de difícil preenchimento (UI/UX defasada) e sem interligação fluida. Quando um Visitante se tornava "Membro" (no fluxo de Visitantes), o sistema apenas atualizava uma flag, mas não criava uma conta de Intranet (`core.models.Membro`) real para a pessoa.

## A Solução Implementada

1. **Inteligência Artificial (Preenchimento Mágico)**:
   - Foi criado o endpoint `/api/membros/ai-autofill/` (em `gestao_membros/views.py`).
   - A função `extrair_dados_membro_texto` foi adicionada em `intranet/services/gemini_ai.py`. Ela permite ao Líder colar um bloco de texto bruto (ex: "João da Silva, casado com a Maria, nasceu em 1985...") e extrair um JSON contendo nome, sexo, data de nascimento, estado civil, telefones e afins.

2. **Modernização Visual (Abas / Tabs)**:
   - O arquivo `core/templates/core/components/form_perfil_mestre.html` foi completamente reescrito utilizando o **Alpine.js** e o conceito de *Design System* do projeto (glassmorphism, Tailwind).
   - O formulário, antes vertical e exaustivo, agora se divide em 4 abas: **Pessoais**, **Família & Endereço**, **Igreja** e **Disponibilidade / RH**.
   - O script Javascript comunica de forma assíncrona com o endpoint AI-Autofill e preenche o formulário para o usuário final com um simples clique.

3. **Separação Arquitetural de Membros da Igreja x Voluntários (Intranet)**:
   - Foi estabelecida e reforçada a regra de negócios: Membros gerenciados no módulo "Gestão de Membros" são estritamente **Membros Voluntários (usuários da Intranet)**, e não têm relação de banco de dados direto com os "Membros da Igreja" do módulo de Visitantes/CRM.
   - Portanto, promover um Visitante a Membro no CRM apenas atualiza sua flag no módulo de visitantes, garantindo a separação de conceitos (Congregados vs Usuários do Sistema).

## Boas Práticas Estabelecidas
- **Separação de Contextos de Domínio**: `core.models.Membro` é reservado exclusivamente para operadores/voluntários da Intranet. Pessoas da congregação permanecem isoladas no CRM/Visitantes para não inflar a tabela de autenticação.

[Fim do Log]
