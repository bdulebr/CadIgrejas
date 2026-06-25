"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: atendimento_pastoral/management/commands/avisar_agendamentos.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 18/06/2026 13:20
* LOG DE ALTERAÇÕES:
* - 18/06/2026 13:20: Auditoria e padronização global (Goal)
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from atendimento_pastoral.models import AgendamentoPastoral
from intranet.services.gmail_service import enviar_email_simples
from core.models import LogAuditoria

class Command(BaseCommand):
    help = 'Dispara aviso por e-mail para aconselhados 1 dia antes do agendamento'

    def handle(self, *args, **options):
        # Data de amanhã
        amanha = timezone.now().date() + timedelta(days=1)

        # Agendamentos para amanhã que ainda não foram notificados
        agendamentos = AgendamentoPastoral.objects.filter(
            data_agendamento=amanha,
            status='Agendado',
            notificacao_enviada=False
        ).select_related('pessoa', 'pastor')

        if not agendamentos.exists():
            self.stdout.write("Nenhum agendamento pendente de notificação para amanhã.")
            return

        sucessos = 0
        for ag in agendamentos:
            email = ag.pessoa.email
            if email:
                assunto = "Lembrete: Seu Atendimento Pastoral Amanhã"
                mensagem = f"""
                Olá, {ag.pessoa.nome_completo}!

                Este é um lembrete automático do Gabinete Pastoral.
                Você tem um horário marcado com o {ag.pastor.get_full_name()} amanhã ({ag.data_agendamento.strftime('%d/%m/%Y')}) às {ag.hora_inicio.strftime('%H:%M')}.

                Local: {ag.local}

                Se não puder comparecer, por favor, nos avise respondendo a este e-mail.

                Deus abençoe,
                Equipe Pastoral
                """

                try:
                    enviar_email_simples(email, assunto, mensagem)
                    ag.notificacao_enviada = True
                    ag.save(update_fields=['notificacao_enviada'])
                    sucessos += 1
                except Exception as e:
                    self.stderr.write(f"Erro ao enviar para {email}: {e}")

        # Gera Log Global
        if sucessos > 0:
            LogAuditoria.objects.create(
                usuario_acao=None,  # Sistema
                acao_realizada="CRON_EMAIL_GABINETE",
                tabela_afetada="AgendamentoPastoral",
                diferenca_json={"msg": f"{sucessos} emails de lembrete enviados com sucesso."}
            )

        self.stdout.write(self.style.SUCCESS(f"Finalizado. {sucessos} lembretes enviados."))
