"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: ministerio_casais/management/commands/disparar_lembretes_cursos.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
import os
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from ministerio_casais.models import CursoCasal, MatriculaCursoCasal
from intranet.services.gmail_service import enviar_email_html
import time

class Command(BaseCommand):
    help = 'Dispara e-mails de lembrete para casais matriculados em cursos que iniciam no dia seguinte.'

    def handle(self, *args, **kwargs):
        amanha = timezone.now().date() + timedelta(days=1)

        # Buscar cursos que iniciam amanhã
        cursos_amanha = CursoCasal.objects.filter(data_inicio=amanha)

        if not cursos_amanha.exists():
            self.stdout.write(self.style.SUCCESS("Nenhum curso começando amanhã. Nada a fazer."))
            return

        total_emails = 0

        for curso in cursos_amanha:
            self.stdout.write(f"Processando lembretes para o curso: {curso.nome}...")

            # Pegar todos os casais matriculados neste curso
            matriculas = MatriculaCursoCasal.objects.filter(curso=curso, casal__arquivado=False)

            for matricula in matriculas:
                casal = matricula.casal
                emails_destino = []
                if casal.email_1: emails_destino.append(casal.email_1)
                if casal.email_2: emails_destino.append(casal.email_2)

                if not emails_destino:
                    continue

                assunto = f"Lembrete: O curso {curso.nome} começa amanhã!"
                contexto = {'casal': casal, 'curso': curso}

                for email in emails_destino:
                    try:
                        enviar_email_html(email, assunto, 'ministerio_casais/email_lembrete_curso.html', contexto)
                        self.stdout.write(f"  - E-mail enviado para {email}")
                        total_emails += 1
                        time.sleep(1) # Rate limit suave
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  Erro ao enviar para {email}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Rotina finalizada. Total de e-mails enviados: {total_emails}"))
