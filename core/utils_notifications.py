from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.template.loader import render_to_string
from core.models import NotificacaoGlobal

def enviar_notificacao_real_time(usuario, titulo, mensagem, link_acao=None):
    """
    Cria uma notificação no BD e envia instantaneamente via WebSocket + HTMX
    para a tela do usuário.
    """
    # 1. Salvar no banco
    notif = NotificacaoGlobal.objects.create(
        destinatario=usuario,
        titulo=titulo,
        mensagem=mensagem,
        link_acao=link_acao
    )

    # 2. Renderizar o HTML da notificação isolada usando template string
    # HTMX hx-swap-oob="afterbegin" injeta isso no topo da lista
    html = f"""
    <div id="notificacoes-badge" hx-swap-oob="true" class="absolute top-1 right-1 flex h-3 w-3">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-3 w-3 bg-red-500 border border-gray-900"></span>
    </div>
    <div id="notificacoes-lista" hx-swap-oob="afterbegin">
        <div id="notif-{notif.id}" class="p-3 border-b border-gray-700/50 hover:bg-gray-700/50 transition-colors animate-fade-in-up bg-blue-900/20">
            <div class="flex justify-between items-start mb-1">
                <p class="text-sm font-bold text-white">{notif.titulo}</p>
                <button onclick="lerNotificacao({notif.id})" class="text-gray-500 hover:text-white" title="Marcar como lida">
                    <i data-lucide="x" class="w-4 h-4"></i>
                </button>
            </div>
            <p class="text-xs text-gray-300 mb-2">{notif.mensagem}</p>
            {f'<a href="{notif.link_acao}" onclick="lerNotificacao({notif.id})" class="text-xs font-bold text-blue-400 hover:underline">Ver Detalhes</a>' if notif.link_acao else ''}
            <p class="text-[10px] text-gray-500 mt-1">Agora mesmo</p>
        </div>
    </div>
    """

    # 3. Enviar via Channels para o grupo do usuário
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f"user_{usuario.id}",
            {
                "type": "send_notification",
                "html": html
            }
        )

    return notif
