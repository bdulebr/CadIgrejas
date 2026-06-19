# LOG: Padronização Global de PDFs e E-mails + Correção Escalas
**Data:** 19/06/2026 15:20

## 1. Problema de Geração de PDFs (Imagens e Logos Quebrados)
Foi identificado que o `xhtml2pdf` rodando em ambiente Windows falhava ao carregar as imagens de logo do banco de dados (especificamente `ConfiguracaoSistema.igreja_logo`). Ele tentava resolver o `.path` e quebrava.
**Solução Aplicada:**
- Criada a função `fetch_resources(uri, rel)` em todas as views que geram PDF (`escalas`, `visitantes`, `almoxarifado`, `ministerio_casais`).
- Injetada a flag `link_callback=fetch_resources` dentro das chamadas `pisa.pisaDocument()`.
- Substituição de `igreja_logo.path` por `igreja_logo.url` ou fallback `settings.STATIC_URL + 'img/logo.jpg'`.

## 2. Padronização Global de E-mails
Alguns módulos não estavam seguindo o novo layout padronizado de e-mails (`base_email.html` via `intranet/services/gmail_service.py`).
**Solução Aplicada:**
- O módulo `almoxarifado` (Termo de Cautela LGPD) foi refatorado para deixar de usar texto puro (`EmailMessage`) e passou a usar `enviar_email_html`.
- Foi criado o template `core/templates/emails/generico.html` para ser utilizado por módulos que apenas enviam mensagens curtas injetando a variável `{{ content|safe }}`, prevenindo erros de `TemplateDoesNotExist`.

## 3. Correção de Lógica no Módulo de Escalas (Mês/Ano)
O formulário de "Nova Competência" e "IA OCR" no módulo de Escalas permitia digitação de texto livre para o Mês/Ano. Como o backend exige estritamente o formato `MM/YYYY` para renderizar as datas do calendário no editor, o texto livre gerava quebras silenciosas ou confusão aos usuários.
**Solução Aplicada:**
- Alterado o `<input type="text">` para `<input type="month" name="mes_ano_input">`.
- Injetada a variável `{{ mes_atual }}` (formatada em `YYYY-MM`) no painel, garantindo que o calendário já abre pré-selecionado no mês vigente.
- Adicionado conversor no `views.py` (`nova_competencia` e `importar_escala_ocr`) para traduzir `YYYY-MM` para `MM/YYYY` antes de persistir no banco de dados.
- **Correção Crítica no OCR (Ano Falso):** O Gemini estava "adivinhando" e retornando anos incorretos (ex: `03/06/2024` ao invés de `2026`). Isso fazia com que o sistema salvasse os voluntários no banco, porém no ano de `2024`, deixando o calendário de `2026` vazio aos olhos do usuário. Solução: foi criado um regex extrator rígido `re.search(r'(\d{2}/\d{2})')` que despreza qualquer ano que a IA retorne e injeta à força o ano provido pelo usuário na interface.

## 4. Estabilidade da Integração Gemini OCR
Durante testes em ambiente simulado, foi interceptada uma anomalia em que a API do Google Gemini retornava falha silenciosa por gargalo de limite de uso (`503 UNAVAILABLE` e `429 Quota Exceeded`), resultando na não geração das escalas.
**Solução Aplicada:**
- Criada lógica de _Automatic Retry_ com _Exponential Backoff_ (3 tentativas) dentro do serviço em `intranet/services/gemini_ai.py` (função `analisar_escala_gemini`).
- Adicionada regra rigorosa de **Fuzzy Matching Neural** diretamente no prompt de envio: A IA agora é instruída explicitamente a fazer dedução aproximada de membros por nomes parciais ou apelidos com base na lista do banco de dados, maximizando o reconhecimento mesmo para PDFs fora de padrão.

## 5. Atualização de Interface do OCR (Groq -> Gemini)
A integração de IA OCR foi migrada internamente para utilizar a API do Google Gemini, deixando o Groq apenas como provedor secundário de contorno de falha. A UI foi atualizada para refletir isso ("Processar com Groq" alterado para "Gerar Escala") removendo a marca de terceiros.

## Status Atual
Todos os relatórios, dossiês, recibos em PDF e disparos de e-mail foram padronizados de ponta a ponta no sistema, resolvendo a instabilidade com ativos locais e respeitando a identidade visual da Igreja.
