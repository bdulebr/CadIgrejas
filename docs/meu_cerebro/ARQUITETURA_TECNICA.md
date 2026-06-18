# Arquitetura Técnica e Tecnologias Base

Esta é a fundação da Intranet da Palavra de Vida Enseada. Todo o sistema opera sobre este stack tecnológico.

## Tecnologias e Padrões Principais
1. **Back-end:** Django 6.0+ (com Python 3.12/3.13)
2. **Front-end UI:** Tailwind CSS (via django-tailwind/crispy-tailwind) + Alpine.js para modais e estado local.
3. **Reatividade e SPA Feel:** HTMX (`django-htmx`) - substitui requests pesados por trocas de partials dinâmicas. Formulários e botões operam majoritariamente com `hx-post`, `hx-get`, e `hx-target`.
4. **Banco de Dados:** SQLite (com transições previstas para PostgreSQL com psycopg2 em produção).
5. **Automação e Background:** `APScheduler` (para jobs recorrentes) e scripts autônomos em `core/management/commands/`.

## IAs e Machine Learning
- **Google Gemini (File API + RAG):** Usado para extração OCR cirúrgica de planilhas e PDFs estruturados, cruzando chaves de dicionários internos.
- **Groq (Llama-3):** Utilizado para inferências mais simples e baratas quando necessário.
- **Auto-Reparo:** Middleware injetado (`Eversinho`) que intercepta exceções 500 (`ExceptionMiddleware`), lê o trace log, pede a correção pro LLM e reescreve arquivos `.py` em tempo real para auto-corrigir bugs do sistema sem intervenção humana.

## Princípios de Design e UX
- **Glassmorphism:** Amplamente empregado (`backdrop-blur-md`, `bg-white/10`).
- **Zero-Refresh:** Navegação ocorre via HTMX injetando blocos no `#main-content`.
- **Acessibilidade:** Padrões visuais grandes e chamativos. Textos amigáveis para pessoas de mais idade (Ex: Módulo de PDV não exige logins complexos, botões focados em touch e atalhos de teclado como F2 e F10).
