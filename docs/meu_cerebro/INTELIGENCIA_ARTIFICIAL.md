# Inteligência Artificial e Integrações de Serviços

A Intranet da PV Enseada não é apenas um CRUD, mas um ecossistema inteligente conectado a diversas APIs e motores de processamento de linguagem natural (LLM). Abaixo, detalho os serviços disponíveis na pasta `intranet/services/`.

## 1. Motores de IA
A Inteligência Artificial atua como funcionário virtual da igreja ("Eversinho").
- `gemini_ai.py`: Módulo que integra a API nativa do Google Gemini.
  - **Uso Principal**: Visão Computacional / OCR Multimodal. Ex: Lê planilhas de Escalas, PDFs e Imagens, processa e extrai entidades em formato JSON (Structured Outputs).
  - **RAG e Fuzzy**: Usa o contexto local (Dicionário de Membros do banco) injetado no prompt para encontrar com alta precisão o `ID` de um membro apenas por ver o apelido ou "nome pela metade" em um papel escaneado.
- `groq_ai.py`: Integra a API da Groq (Llama-3).
  - **Uso Principal**: Inferências de texto ultra-rápidas e de baixo custo. Gera e-mails baseados em contexto, resume prontuários de atendimento pastoral e filtra conflitos simples em horários.

## 2. Ecossistema Google (Workspace)
A igreja opera fortemente sobre as ferramentas do Google.
- `gmail_service.py`: Motor de envio de E-mails via SMTP do Gmail.
  - Sub-rotinas para Termos de Cautela (Almoxarifado), Alertas Disciplinares (Membros) e Logs de Erro.
- `google_drive.py` e `gdrive.py`: Integração com a API do Google Drive (`google-api-python-client`).
  - **Uso Principal**: Espelha o módulo `midia_lgpd` (PV Drive) nativamente no Google Drive da Igreja. Arquivos anexados no sistema são subidos para lá para economizar disco do VPS local.
- `google_calendar.py`: Espelhamento da Agenda. Eventos criados no `escalas` ou no `atendimento_pastoral` disparam um webhook síncrono para criar eventos no Google Calendar oficial da Liderança.

## 3. Geração de Documentos (PDF)
- `pdf_generator.py` e `pdf_service.py`: Utiliza `xhtml2pdf` / `ReportLab`.
  - **Uso Principal**: Geração da Escala Mensal formatada para impressão, Ficha Limpa (Termos de LGPD), Extratos da Tesouraria e Fichas do Ministério de Casais (Certificados de Conclusão).

## Conclusão da Camada de Serviços
Toda requisição externa fica isolada em `intranet/services/`. Nenhuma view do Django chama `requests.post()` solto para APIs, garantindo que se amanhã trocarmos o Groq pela OpenAI, por exemplo, o impacto no código (`views.py`) será zero.
