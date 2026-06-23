# Alertas de Segurança 403 e Invasões

## Objetivo
Interceptar usuários ou visitantes que tentam acessar rotas para as quais não possuem permissão (`PermissionDenied` ou `status=403`), e alertar os administradores de forma proativa.

## Componentes Técnicos
1. **Banco de Dados**:
   - `AlertaInvasao` guarda os logs de cada tentativa (quem, quando, onde, IP, User-Agent).
   - `ConfiguracaoSistema` armazena as chaves mestre para ligar/desligar alertas, bem como o número de WhatsApp e E-mail dos responsáveis.

2. **Middleware (`core/middleware.py`)**:
   - O `RequestMiddleware` armazena o request no thread locals (embora o interceptor possa usar o request direto).
   - O método `_registrar_invasao` dentro de `middleware.py` é disparado sempre que um `Response` for 403 ou uma exceção `PermissionDenied` for lançada nas views (via `@requer_permissao`).
   - O registro dispara uma **Thread em Background** (`disparar_alerta_invasao_403`) para não atrasar a resposta ao usuário que receberá a tela do "Eversinho Bravo".

3. **Disparador (`core/utils_notifications.py`)**:
   - `disparar_alerta_invasao_403(alerta_id)`: Renderiza os templates de Email (`alerta_invasao_403.html`) e WhatsApp (`alerta_invasao_403.txt`) e invoca os serviços `gmail_service.py` e `whatsapp_service.py`.

4. **Interface do Administrador (Sysadmin Dashboard)**:
   - Aba "Segurança & Controle": Possui os campos para ligar/desligar a função e informar os contatos.
   - Aba "Histórico de Invasões 403" (`activeTab='invasoes'`): Lista cronológica com botão "Detalhes" ou "Ver IP". A lista possui cores de perigo e badges de status para tratamento posterior.

## LGPD / Conformidade
Nenhum dado é coletado sem o consentimento dos termos de uso da igreja, já que as interceptações priorizam membros logados. Para visitantes, apenas IP (dado técnico) é colhido com intuito de proteção de infraestrutura e prevenção a fraude / ataques (Base Legal: Proteção de Crédito e Legítimo Interesse para defesa do sistema).
