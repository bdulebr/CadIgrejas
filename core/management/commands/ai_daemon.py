import time
from django.core.management.base import BaseCommand
from django.core.management import call_command
from core.models import AIEngineerLog

class Command(BaseCommand):
    help = 'Daemon da IA: Fica em loop observando erros PENDENTE e aciona a engenharia.'

    def handle(self, *args, **options):
        self.stdout.write("==================================================")
        self.stdout.write("👻 AI DAEMON INICIADO (Modo Fantasma / Hot-Reload)")
        self.stdout.write("==================================================")
        self.stdout.write("Vigiando a fila de erros em tempo real...")

        while True:
            # Processa um erro por vez
            pendente = AIEngineerLog.objects.filter(status='PENDENTE').first()
            if pendente:
                self.stdout.write(f"\n[DAEMON] Bug interceptado na fila! ID: {pendente.id}")
                try:
                    # Chama o motor de IA passando o ID do log
                    call_command('ai_auto_engineer', target_log_id=pendente.id)
                except Exception as e:
                    self.stderr.write(f"[DAEMON] Falha ao processar a cura: {e}")
                    pendente.status = 'ERRO_DAEMON'
                    pendente.detalhes += f"\n\nErro Daemon: {str(e)}"
                    pendente.save()

            # Dorme 5 segundos e checa de novo (baixo uso de CPU)
            time.sleep(5)
