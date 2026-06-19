"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: ministerio_casais/signals.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Casal
import threading
from django.conf import settings
from intranet.services.gmail_service import enviar_email_html

def enviar_email_casal_background(casal_id, base_url):
    try:
        from core.models import ConfiguracaoSistema
        sys_config = ConfiguracaoSistema.objects.first()
        logo_url = base_url + sys_config.igreja_logo.url if sys_config and sys_config.igreja_logo else base_url + '/static/img/logo.jpg'

        casal = Casal.objects.get(id=casal_id)

        recipients = []
        if casal.email_1:
            recipients.append(casal.email_1)
        if casal.email_2:
            recipients.append(casal.email_2)

        if recipients:
            for dest in recipients:
                enviar_email_html(
                    destinatario=dest,
                    assunto='Bem-vindos ao Ministério de Casais da Palavra de Vida!',
                    template_name='ministerio_casais/email_boas_vindas_casal.html',
                    context={
                        'casal': casal,
                        'base_url': base_url
                    }
                )
    except Exception as e:
        print(f"Erro ao enviar email para o casal {casal_id}: {e}")

@receiver(post_save, sender=Casal)
def casal_post_save(sender, instance, created, **kwargs):
    if created:
        # Pega a url base
        base_url = getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000')
        # Roda em thread para não travar o frontend
        threading.Thread(target=enviar_email_casal_background, args=(instance.id, base_url)).start()
