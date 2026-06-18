# Padrões de Código e Manutenção

Para manter a integridade, facilidade de manutenção e segurança do projeto da PV Enseada, as seguintes regras de codificação e arquitetura devem ser estritamente seguidas por qualquer desenvolvedor (Humano ou Inteligência Artificial) que toque neste sistema.

## 1. Zero-Trust e Auditoria
Qualquer tabela do banco que envolva dados sensíveis (`Tesouraria`, `Almoxarifado`, `Escalas`, `Permissoes`) deve estar integrada ao modelo de Blockchain Simulado (`core.models.LogImutavel`).
- **NÃO** edite ou exclua registros do banco via SQL bruto ou comandos shell em produção sem passar pelo ORM do Django.
- Todo `save()` em tabelas críticas (ex: `Lancamento`) verifica a consistência do hash (`hash_assinatura`) em relação aos dados em texto.

## 2. Padrão Front-end e UI (Zero-Refresh)
- O projeto usa `HTMX` para reatividade.
- Em vez de usar `<form action="..." method="POST">` e retornar um redirect de página inteira, use:
  ```html
  <form hx-post="{% url 'minha_view' %}" hx-target="#container-alvo" hx-swap="innerHTML">
  ```
- O TailwindCSS deve ser preferencialmente gerado via forms Crisp (`{% load crispy_tailwind_filters %}`) ou classes explícitas `bg-blue-500 rounded-lg shadow-md`.
- **Modais:** O controle de modais é feito pelo `Alpine.js` (`x-data="{ open: false }"`).
- **Glassmorphism e Idosos:** A paleta e a fonte (tamanhos de texto maiores) foram pensadas para a terceira idade. Botões devem ter pelo menos `p-3` ou `p-4` para touch.

## 3. Lógica de Negócio (Onde Fica?)
- **Views**: Apenas validam formulários e chamam o HTMX de volta.
- **Services (`intranet/services/`)**: Acesso a APIs externas (Google, Gemini, Groq, Gmail, PDF).
- **Models**: Constraints (`UniqueConstraint`), Validações de Banco e lógica que pertence à entidade em si (Ex: método `is_vencido()` do Almoxarifado).

## 4. Banco de Dados e Migrations
- Atualmente em SQLite. Código de transação deve ser compatível.
- Não altere as chaves de `slug` de módulos do sistema nem os `id_unico_fixo` de departamentos sem atualizar referências no código, pois views podem usar `.filter(slug='...')`.
- O Motor Anti-Conflito das Escalas usa `constraints` diretas no banco de dados (`UniqueConstraint` em Membro+Data+Horario_Inicio). Se precisar alterar, precisa gerar Migration.

## 5. Tratamento de Exceções
- O sistema possui um Middleware Injetado (`Eversinho`) de auto-reparo. Não mascare erros com `try...except Exception: pass`. Deixe quebrar se for um bug real, para que o middleware capture, log o erro (`LogAuditoria/AIEngineerLog`), envie por e-mail e tente se consertar via LLM.

## 6. LGPD (Lei Geral de Proteção de Dados)
- Nenhuma foto ou informação sensível pode ser tornada pública sem que o usuário tenha marcado `termos_aceitos = True` no seu perfil `Membro`.
- No módulo `atendimento_pastoral`, as anotações do pastor são marcadas com RLS (`Row-Level Security` simulado) com `is_restrito = True`.

**Ao iniciar novos desenvolvimentos:**
Sempre pesquise no Cérebro RAG (`docs/meu_cerebro`) antes de recriar módulos que já existam.
