from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def reenviar_emails_pendentes_job():
    """
    Função do CronJob que varre os emails falhos e tenta reenviar,
    respeitando o master switch do SysAdmin.
    """
    try:
        from core.models import EmailLog, ConfiguracaoSistema
        from intranet.services.gmail_service import reenviar_email_falho

        config = ConfiguracaoSistema.objects.first()
        if not config or not config.envios_email_ativos:
            return  # Master switch desligado

        falhas = EmailLog.objects.filter(status='falha')
        for log in falhas:
            # Tenta reenviar
            reenviar_email_falho(log.id)

    except Exception as e:
        logger.error(f"Erro no CRON de reenvio de emails: {e}")

def reenviar_whatsapp_pendentes_job():
    """
    Função do CronJob que varre os whatsapps falhos e tenta reenviar.
    """
    try:
        from core.models import LogWhatsApp, ConfiguracaoSistema
        from intranet.services.whatsapp_service import reenviar_whatsapp_falho

        config = ConfiguracaoSistema.objects.first()
        if not config or not config.whatsapp_ativo:
            return

        falhas = LogWhatsApp.objects.filter(status='falha')
        for log in falhas:
            reenviar_whatsapp_falho(log.id)

    except Exception as e:
        logger.error(f"Erro no CRON de reenvio de WhatsApp: {e}")

def start_scheduler():
    from core.models import ConfiguracaoSistema

    scheduler = BackgroundScheduler()

    intervalo_email = 1
    intervalo_wpp = 1
    try:
        config = ConfiguracaoSistema.objects.first()
        if config:
            if config.intervalo_reenvio_emails_horas:
                intervalo_email = config.intervalo_reenvio_emails_horas
            if config.intervalo_reenvio_whatsapp_horas:
                intervalo_wpp = config.intervalo_reenvio_whatsapp_horas
    except Exception:
        pass

    scheduler.add_job(reenviar_emails_pendentes_job, 'interval', hours=intervalo_email, id='reenvio_email', replace_existing=True)
    scheduler.add_job(reenviar_whatsapp_pendentes_job, 'interval', hours=intervalo_wpp, id='reenvio_whatsapp', replace_existing=True)
    scheduler.start()
    logger.info(f"APScheduler Iniciado: Reenvio automático E-mail ({intervalo_email}h) | WhatsApp ({intervalo_wpp}h).")
