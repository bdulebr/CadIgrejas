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

def rotina_diaria_00h():
    """
    Job disparado via CRON todos os dias à meia-noite (00:00).
    """
    from django.core.management import call_command
    try:
        call_command('rotina_meia_noite')
    except Exception as e:
        logger.error(f"Erro no CRON de rotina_meia_noite: {e}")

def rotina_diaria_08h():
    """
    Job disparado via CRON todos os dias às 08:00 da manhã.
    """
    from django.core.management import call_command
    try:
        call_command('enviar_lembretes_curso')
    except Exception as e:
        logger.error(f"Erro no CRON de enviar_lembretes_curso: {e}")

    try:
        call_command('avisar_agendamentos')
    except Exception as e:
        logger.error(f"Erro no CRON de avisar_agendamentos: {e}")


def start_scheduler():
    from core.models import ConfiguracaoSistema
    # Para usar cron, precisamos importar do triggers
    from apscheduler.triggers.cron import CronTrigger

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

    # Jobs Frequentes
    scheduler.add_job(reenviar_emails_pendentes_job, 'interval', hours=intervalo_email, id='reenvio_email', replace_existing=True)
    scheduler.add_job(reenviar_whatsapp_pendentes_job, 'interval', hours=intervalo_wpp, id='reenvio_whatsapp', replace_existing=True)

    # Jobs Diários (CRON)
    scheduler.add_job(rotina_diaria_00h, CronTrigger(hour=0, minute=0), id='rotina_meia_noite', replace_existing=True)
    scheduler.add_job(rotina_diaria_08h, CronTrigger(hour=8, minute=0), id='rotina_manha_08h', replace_existing=True)

    scheduler.start()
    logger.info(f"APScheduler Iniciado: Reenvio automático E-mail ({intervalo_email}h) | WhatsApp ({intervalo_wpp}h). Tarefas diárias 00h e 08h agendadas.")
