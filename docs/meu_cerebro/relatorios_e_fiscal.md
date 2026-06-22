# Relatórios do PDV e Adequação Fiscal 2026

## 1. Relatórios de Caixa
O sistema de relatórios do PDV ("Gerenciador de Caixa") foi expandido para incluir:
- Extrato de Vendas do Dia, Mês e Ano.
- Controle de Fiados pendentes por período.
- Totais recebidos e em haver.
- **Exportação em PDF**: O setor financeiro agora pode baixar relatórios consolidados em formato PDF usando a biblioteca `xhtml2pdf`. As views `relatorios_painel` e `exportar_financeiro_pdf` gerenciam essa emissão.

## 2. Cadastro de Produtos e Tributação
O modelo `Produto` em `pdv/models.py` foi atualizado para suportar as normas da **Nova Reforma Fiscal (2026)**:
- O NCM passou a ser preenchido obrigatoriamente (por padrão recebe "00000000" para evitar erros em registros antigos).
- Adição dos impostos opcionais:
  - `CBS` (Contribuição sobre Bens e Serviços)
  - `IBS` (Imposto sobre Bens e Serviços)
  - `IS` (Imposto Seletivo)
- O formulário `pdv/templates/pdv/form_produto.html` agora utiliza AlpineJS e **BrasilAPI** para consultar códigos NCM baseados no nome do produto, reduzindo a digitação manual e auxiliando os operadores.

## 3. Comandos Úteis
- F2, F3, F4, F5, F6 e F10 já conhecidos na Frente de Caixa.
- Adição do F11 para **Limpar Carrinho**, que esvazia a compra sem limpar a identificação do cliente e sem registrar "venda cancelada" no banco.

*Revisado em Junho de 2026 durante a implantação da gestão de Fiados e Reforma Fiscal.*
