# Configuração de Infraestrutura WebSockets (Django Channels + HTMX)

**Data**: 19/06/2026
**Autor**: Agente Antigravity / Marcos Lira

## O Cenário
A Intranet possuía um sistema de notificações passivo ("sininho") que só exibia os dados quando a tela carregava ou via F5. Com a decisão de usar a tecnologia **Redis no Linux**, tornou-se viável habilitar uma camada de "Real-Time Absoluto" via WebSockets sem prejudicar o peso do sistema, usando a abstração mágica do HTMX.

## A Solução Implementada

1. **Instalação de Dependências Base**:
   - Foram instalados e adicionados ao `requirements.txt`: `channels`, `channels-redis` e o servidor assíncrono `daphne`.
   - No `settings.py`, o `daphne` foi incluído no topo do `INSTALLED_APPS` (substituindo o antigo handler WSGI padrão em ambiente de desenvolvimento/produção async).

2. **Migração para ASGI**:
   - `intranet/asgi.py` agora possui roteamento bidirecional. Requisições `http` vão para o Django clássico, requisições `websocket` passam pelo `AuthMiddlewareStack` e caem no `core.routing`.

3. **O Consumer e as Salas**:
   - Criamos o `core.consumers.NotificationConsumer`. Ao abrir o site, cada usuário logado ganha uma conexão persistente e entra no "grupo" com o seu próprio ID (`user_ID`).

4. **HTMX OOB Swapping (O Pulo do Gato)**:
   - Em vez de usar Javascript complexo, importamos a extensão `<script src=".../ext/ws.js">` no `base.html`.
   - O botão do sininho foi envelopado com `hx-ext="ws" ws-connect="/ws/notifications/"`.
   - Em `core/utils_notifications.py`, criamos a função `enviar_notificacao_real_time`. Essa função **renderiza blocos HTML com o atributo `hx-swap-oob="afterbegin"` e `hx-swap-oob="true"`**.
   - Quando o Django Channels joga esse HTML pelo WebSocket, o HTMX intercepta e costura o alerta na tela de forma silenciosa e instantânea, além de acender a bolinha vermelha do sino se ele estava apagado!

## Como Usar Daqui pra Frente
Em qualquer lugar do código (views, tarefas celery, actions do admin), ao invés de usar `Notificacao.objects.create(...)`, importe a nova função:
```python
from core.utils_notifications import enviar_notificacao_real_time

enviar_notificacao_real_time(
    usuario=lider_destino,
    titulo="Nova Escala!",
    mensagem="Você foi escalado no culto de Domingo.",
    link_acao="/escalas/minhas/"
)
```
A mágica ocorrerá automaticamente.

[Fim do Log]
