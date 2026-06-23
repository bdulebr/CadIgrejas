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

def disparar_alerta_invasao_403(alerta_id):
    from core.models import AlertaInvasao, ConfiguracaoSistema
    from intranet.services.gmail_service import enviar_email_html
    from intranet.services.whatsapp_service import enviar_whatsapp_template
    from django.template.loader import render_to_string
    import os

    try:
        alerta = AlertaInvasao.objects.get(id=alerta_id)
        config = ConfiguracaoSistema.objects.get(id=1)

        if not config.alerta_invasao_ativo:
            return

        nome = alerta.membro.get_full_name() if alerta.membro else "Visitante Anônimo"
        email_membro = alerta.membro.email if alerta.membro else "N/A"
        telefone = alerta.membro.telefone_celular if alerta.membro else "N/A"
        departamentos = ", ".join([d.nome for d in alerta.membro.departamentos.all()]) if alerta.membro else "N/A"

        contexto = {
            'is_membro': bool(alerta.membro),
            'nome': nome,
            'email_membro': email_membro,
            'telefone': telefone,
            'departamentos': departamentos,
            'data_hora': alerta.data_hora.strftime("%d/%m/%Y %H:%M:%S"),
            'ip': alerta.ip or "Desconhecido",
            'rota': alerta.caminho_url
        }

        # Enviar Email se configurado
        if config.email_admin_alertas:
            html_content = render_to_string('core/emails/alerta_invasao_403.html', contexto)
            # Envia assíncrono via Celery/Thread local do gmail_service, assumindo que enviar_email_html joga pra DB de logs
            enviar_email_html(
                destinatario=config.email_admin_alertas,
                assunto="🚨 ALERTA: Tentativa de Invasão (Acesso Negado 403)",
                html_content=html_content
            )

        # Enviar WhatsApp
        if config.whatsapp_admin_alertas and config.whatsapp_ativo:
            txt_content = render_to_string('core/whatsapp/alerta_invasao_403.txt', contexto)
            # Template simples via WhatsApp Service
            enviar_whatsapp_template(
                numero_destino=config.whatsapp_admin_alertas,
                mensagem=txt_content
            )

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Erro ao disparar alerta 403: {e}")
