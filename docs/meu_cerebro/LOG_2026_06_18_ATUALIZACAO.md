# Atualizações: PDV Inteligente e OCR RAG (18/06/2026)

## 1. Módulo PDV (Frente de Caixa)
- **Acesso Direto (Zero Login):** Operadores de caixa não precisam logar na Intranet com e-mail e senha. Eles clicam no botão verde "Acesso Rápido ao Caixa" na tela de login e entram com o PIN de 4 dígitos.
- **Abertura/Fechamento Dinâmicos:** A tela de Dashboard do PDV foi limpa. Agora, a abertura do caixa (informar fundo de troco) e o fechamento (contar gaveta ao apertar F10) ocorrem de forma travada dentro do próprio `frente_caixa.html`. Se não houver caixa aberto, a tela fica "borrada" exigindo abertura.
- **Correção de Atalhos:** A tecla `ESC` não desloga mais o usuário, servindo apenas para cancelar modais. O atalho `F2` abre uma nova venda.
- **Produtos em Blocos:** O "Catálogo Rápido" na tela de vendas exibe os produtos de forma orgânica e visual, fáceis para tocar ou clicar, com UX focada em agilidade.

## 2. Motor OCR com RAG (Escalas Gemini)
- **O Problema Antigo:** O `pdfplumber` misturava textos nas tabelas das escalas de voluntários e o Groq "alucinava" nomes.
- **Solução Atual (Gemini + RAG):** Implementado no `gemini_ai.py` (`analisar_escala_gemini`).
- **Como Funciona:** O arquivo (PDF, Excel, CSV) é enviado diretamente via File API para o Gemini 1.5 Flash. No *Prompt*, é injetado todo o contexto do banco de dados: a lista real de Departamentos Ativos e a lista real de Membros Ativos (Nomes, Sobrenomes e Apelidos).
- **Resultado Estrito:** O Gemini extrai as escalas e cruza com exatidão, retornando o ID do Departamento e uma lista de IDs de Membros, acabando com a dependência da biblioteca `thefuzz` e garantindo que o sistema não invente nomes (zero alucinações).
- **Cultos Padrões Configuráveis:** O Banco foi semeado com "Domingo da Família" e "Quarta Profética".
- **Views Afetadas:** `importar_escala_ocr` em `escalas/views.py`.

## 3. Diretriz de Desenvolvimento
Sempre que for mexer no PDV, lembrar do arquivo `frente_caixa.html` e sua lógica de Alpine.js acoplada com modais. Sempre que for mexer nas escalas importadas, lembrar que o retorno do Gemini é sempre um JSON validado de IDs reais do banco de dados.
