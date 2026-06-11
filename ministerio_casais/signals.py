from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Casal
import threading
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def enviar_email_casal_background(casal_id, base_url):
    try:
        from core.models import ConfiguracaoSistema
        sys_config = ConfiguracaoSistema.objects.first()
        logo_url = base_url + sys_config.igreja_logo.url if sys_config and sys_config.igreja_logo else base_url + '/static/img/logo.jpg'

        casal = Casal.objects.get(id=casal_id)

        # Prepara a mensagem HTML
        html_message = render_to_string('ministerio_casais/email_boas_vindas_casal.html', {
            'casal': casal,
            'base_url': base_url,
            'logo_url': logo_url
        })
        plain_message = strip_tags(html_message)

        recipients = []
        if casal.email_1:
            recipients.append(casal.email_1)
        if casal.email_2:
            recipients.append(casal.email_2)

        if recipients:
            send_mail(
                subject='Bem-vindos ao Ministério de Casais da Palavra de Vida!',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                html_message=html_message,
                fail_silently=True,
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
