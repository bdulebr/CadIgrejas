"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: core/management/commands/enviar_lembretes_curso.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from ministerio_casais.models import TurmaCurso, MatriculaCursoCasal
from intranet.services.gmail_service import enviar_email_html
from core.models import ConfiguracaoSistema

class Command(BaseCommand):
    help = 'Envia e-mails de lembrete para casais matriculados em turmas que começam amanhã'

    def handle(self, *args, **options):
        amanha = timezone.now().date() + timezone.timedelta(days=1)

        turmas_amanha = TurmaCurso.objects.filter(data_inicio=amanha)

        if not turmas_amanha.exists():
            self.stdout.write(self.style.SUCCESS(f'Nenhuma turma começando em {amanha}.'))
            return

        sys_config = ConfiguracaoSistema.objects.first()
        from django.conf import settings
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000') # Substituir pela env de produção depois

        if sys_config and sys_config.igreja_logo:
            logo_url = base_url + sys_config.igreja_logo.url
        else:
            logo_url = base_url + '/static/img/logo.jpg'

        emails_enviados = 0

        for turma in turmas_amanha:
            matriculas = MatriculaCursoCasal.objects.filter(turma=turma)
            for matricula in matriculas:
                casal = matricula.casal
                destinatarios = []
                if casal.email_1:
                    destinatarios.append(casal.email_1)
                if casal.email_2:
                    destinatarios.append(casal.email_2)

                if not destinatarios:
                    continue

                try:
                    for dest in destinatarios:
                        enviar_email_html(
                            destinatario=dest,
                            assunto=f'Lembrete: O curso "{turma.curso.nome}" começa amanhã!',
                            template_name='ministerio_casais/email_lembrete_curso.html',
                            context={
                                'casal': casal,
                                'curso': turma.curso,
                                'turma': turma,
                                'base_url': base_url
                            }
                        )
                    emails_enviados += len(destinatarios)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Erro ao enviar para {casal}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Concluído. {emails_enviados} e-mails de lembrete enviados com sucesso.'))
