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

def start_scheduler():
    from core.models import ConfiguracaoSistema

    scheduler = BackgroundScheduler()

    # Busca a configuração, se existir, para definir a frequência
    intervalo_horas = 1
    try:
        config = ConfiguracaoSistema.objects.first()
        if config and config.intervalo_reenvio_emails_horas:
            intervalo_horas = config.intervalo_reenvio_emails_horas
    except Exception:
        pass

    scheduler.add_job(reenviar_emails_pendentes_job, 'interval', hours=intervalo_horas, id='reenvio_email', replace_existing=True)
    scheduler.start()
    logger.info(f"APScheduler Iniciado: Reenvio automático de e-mails a cada {intervalo_horas} hora(s).")
