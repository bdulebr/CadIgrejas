# Refatoração Global de E-mails e Master Switch (Sysadmin)
Data: 22 de Junho de 2026 - 11:13

## Problema Identificado
O sistema possuía uma trava global de segurança no Sysadmin (`ConfiguracaoSistema.envios_email_ativos`) que deveria pausar todos os envios de e-mail do sistema. Contudo, 5 módulos diferentes ignoravam essa regra por utilizarem as bibliotecas nativas do Django (`send_mail`, `EmailMessage`, `EmailMultiAlternatives`) diretamente, sem passar pelo nosso motor centralizado.
Além disso, o motor central não aceitava disparo para listas de múltiplos destinatários.

## Módulos Infratores e Correções
Foram identificados e refatorados os seguintes arquivos para usar exclusivamente `intranet.services.gmail_service.enviar_email_html` ou `enviar_email_simples`:
- `midia_lgpd/views.py`: Termos de Consentimento (LGPD Criança).
- `core/management/commands/ai_auto_engineer.py`: Relatórios do motor de IA.
- `almoxarifado/tasks.py`: Envio de PDF do Termo de Cautela.
- `ministerio_casais/views.py`: Envio de PDF dos Certificados de Curso.
- `tesouraria/views.py`: Envio de Planilha Excel Fechamento para a Sede.

## Arquitetura Melhorada no Motor
No arquivo `intranet/services/gmail_service.py`:
- Adicionado suporte nativo à anexos na função `enviar_email_simples(..., anexos=None)`.
- Adicionado tratamento para conversão automática de `destinatario` para arrays (`list`) quando passado um único email, ou parsing de strings com listas, garantindo suporte ao envio massivo em `enviar_email_html` e `enviar_email_simples`.
- O log no banco de dados `EmailLog` agora intercepta e trata `destinatarios` que sejam listas, cortando com `[:254]` para não estourar o limite da coluna.

## Testes Realizados
Foram escritos testes de integração (`test_emails.py`) operando na camada de simulação:
1. Desligar a configuração global.
2. Acionar envio simples e envio HTML para listas de emails.
3. Verificar na tabela `EmailLog` se o e-mail foi interceptado e cancelado com falha motivada pelo "MASTER SWITCH OFF".
4. Religado o botão global e validado o funcionamento. Todos os testes passaram com sucesso.
