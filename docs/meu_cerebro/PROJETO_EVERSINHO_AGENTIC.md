# Projeto: Eversinho Agentic AI (Visão Arquitetural)

## Objetivo
Evoluir o assistente virtual "Eversinho" de um chatbot passivo (FAQ) para um **Agente Autônomo de IA (Co-piloto Executivo)**, capaz de tomar ações reais no sistema ERP (CadIgrejas), respeitando estritamente as permissões do usuário logado.

## Status: APROVADO (Visão Macro)
*(Aguardando fase de implementação)*

---

## Pilares Fundamentais do Projeto (Aprovados)

### 1. O "Cérebro" de Permissões (Zero-Trust AI)
A inteligência artificial não fará bypass das regras de segurança do Django. O motor de Tool Calling/Function Calling receberá em seu contexto o usuário logado (`request.user`).
Antes da IA conseguir invocar qualquer ferramenta (ex: `excluir_usuario`, `alterar_caixa`), a própria *tool* fará a checagem das permissões de grupos e lideranças (`has_perm`, checagens de departamento). Se o usuário não tiver permissão, a IA receberá um erro interno e repassará a negativa ao usuário com a mensagem "Deus tá vendo! Você não tem autorização para isso".

### 2. O "Cinto do Batman" (Function Calling)
Integração profunda usando frameworks como LangChain ou LlamaIndex acoplados ao LLM (Groq/Gemini). O Eversinho possuirá um arsenal de ferramentas (funções Python nativas mapeadas).
- **Exemplo de Capacidade:** O usuário pede para enviar um aviso para a turma de casais. O Eversinho identifica a intenção, processa a lista de contatos do banco e dispara silenciosamente os gatilhos de *E-mail* e *WhatsApp*, prestando contas no chat em seguida ("Feito! Mandei para 45 pessoas").

### 3. Visão Computacional (Eversinho Multimodal)
Uso de modelos multimodais (Gemini Pro Vision / GPT-4o / Groq LLaVA) para interpretar imagens (ex: prints, fotos de documentos).
- **Caso de Uso:** O usuário arrasta a foto de uma ficha física de visitantes para o chat. O Eversinho lê os dados com OCR e compreensão de contexto, estrutura as entidades (Nome, Telefone, Endereço) e invoca a ferramenta de "Cadastro de Visitante", automatizando a entrada de dados.

### 4. Chat Interativo com "Botões de Ação" (UI Dinâmica + HTMX)
Respostas da IA não se limitarão a blocos de Markdown. O Eversinho retornará fragmentos HTML renderizados pelo servidor (via WebSockets/HTMX).
- **Caso de Uso:** Ao invés de descrever como a escala de voluntários ficou, a IA renderizará um componente visual (Mini-calendário/Kanban) dentro do chat com opções de aprovação. O usuário poderá clicar em botões como `[Salvar Escala]` ou `[Rejeitar e Refazer]`.

### 5. Contexto Sensorial (Eversinho "Onipresente")
A inicialização do chat mandará o contexto da página atual (URL, Entidade Ativa) como `System Prompt` injetado na thread da conversa.
- **Caso de Uso:** Ao abrir o chat na aba de Tesouraria, o Eversinho já inicia focado em relatórios financeiros e conciliação bancária. Se aberto no módulo de Membros, foca no gerenciamento de perfis.

---
## Restrições
*(Conforme ordens da liderança, as opções de Comando de Voz e Gamificação/Personalidade "Humorística" foram excluídas do escopo desta evolução).*
