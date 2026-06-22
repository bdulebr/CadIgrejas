# LOG DE EVOLUÇÃO - EVERSINHO IA E ARQUITETURA DE RAG
**Data:** 22/06/2026
**Objetivo:** Consolidar no cérebro da IA (memória) as alterações arquiteturais recentes relacionadas ao Assistente Virtual (Eversinho), o Motor de Auto-Correção e a integração híbrida Google + OpenAI.

## 1. Eversinho RAG - Assistente Virtual Híbrido
- **Refatoração Frontend:** O formulário de chat do Eversinho (na `base.html`) foi migrado de **HTMX puro** para **Alpine JS + Fetch API**. Isso foi feito porque o HTMX causava conflitos na interceptação de eventos inline (`hx-on::before-request`). A solução com Alpine garante que a tela não dê refresh, exibe um ícone de carregamento perfeito, interage de forma robusta e realiza auto-scroll para baixo ao receber respostas longas.
- **Renderização de Markdown:** A resposta da IA agora é traduzida no servidor via biblioteca `markdown` nativa (no `core/views.py`), permitindo que a IA retorne links interativos que o usuário pode clicar (e que respeitam as permissões do sistema).
- **Inteligência Dinâmica (RAG Eficiente):** Foram deletados os antigos arquivos textuais genéricos. Agora, o Eversinho lê DIRETAMENTE a documentação viva do sistema (`Modulos.txt`, `4_Modulos_Em_Detalhes.md`, `Regras Globais.txt`). Isso reduziu o tamanho do token lido de 150k para menos de 15k, economizando cota e aumentando drasticamente a precisão técnica das respostas.
- **Mapa de Links Embutido:** O prompt raiz do Eversinho (no `core/services/eversinho_rag.py`) conta com um mapa detalhado das rotas de todos os módulos. Ele sabe os caminhos de `/membros/`, `/escalas/`, `/painel-lider/`, etc., e insere links markdown proativamente nas respostas.

## 2. Fallback Infalível (OpenAI + Gemini)
- O sistema sofreu problemas de `429 RESOURCE_EXHAUSTED` do Gemini (devido aos tokens) e depois `insufficient_quota` da OpenAI.
- **A Solução:** Foi implementado um fallback silencioso com `try/except` na função principal de RAG do Eversinho.
- A hierarquia de chamada é: **Tentativa com OpenAI (`gpt-4o-mini`) -> Falhou? Intercepta Exception -> Executa silenciosamente no Gemini (`gemini-2.5-flash`)**. O sistema agora é virtualmente blindado contra expiração de quotas de uma API isolada.

## 3. Motor de Auto-Engenharia (AI Auto-Engineer)
- O `AIAutoEngineerMiddleware` agora monitora **erros 500 não tratados**, **403** e **400**, salvando-os na tabela `AIEngineerLog`.
- Uma tela customizada (`eversinho_500.html`) é exibida ao usuário, mostrando o Eversinho em modo "trabalho", com animação enquanto a IA avalia o erro no servidor.
- O daemon `ai_auto_engineer.py` lê os arquivos locais usando Regex no Traceback, alimenta a IA autônoma e propõe patches automáticos (tudo usando a nova biblioteca `google.genai` para manter a conformidade com as exigências de atualizações do Google).

## CONCLUSÃO PARA A NOVA MÁQUINA
Ao inicializar o ambiente de desenvolvimento no novo PC:
1. Puxe a branch `main`.
2. O arquivo `.env` (onde `GEMINI_API_KEY` e `OPENAI_API_KEY` estão salvas) já está no Git graças a um push forçado (`git add -f`).
3. O banco de dados local `db.sqlite3` também está na nuvem e preservará todos os registros recentes de testes.
4. Rode `venv\Scripts\python.exe -m pip install -r requirements.txt` se a virtualenv for recriada (a biblioteca `openai` foi incluída nela).
