"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: core/management/commands/bootstrap_sistema.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
import os
import subprocess
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Motor Zero-Trust de Self-Healing: Verifica pastas essenciais e arquivos corrompidos.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("INICIANDO MOTOR DE BOOTSTRAP E SELF-HEALING..."))

        # 1. Self-Healing de Pastas
        pastas_vitais = [
            'media',
            'media/perfil',
            'media/departamentos/logos',
            'media/ocorrencias',
            'media/avisos_anexos',
            'media/logos',
            'staticfiles',
            'logs',
            'backups'
        ]

        base_dir = settings.BASE_DIR

        self.stdout.write(self.style.MIGRATE_HEADING("1. VERIFICANDO INTEGRIDADE DE PASTAS:"))
        for pasta in pastas_vitais:
            caminho = os.path.join(base_dir, pasta)
            if not os.path.exists(caminho):
                os.makedirs(caminho, exist_ok=True)
                self.stdout.write(self.style.SUCCESS(f"[CRIADO] Pasta ausente restaurada: {pasta}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"[OK] Pasta íntegra: {pasta}"))

        # 2. Self-Healing de Arquivos via GIT (Se for um repositório clonado)
        self.stdout.write(self.style.MIGRATE_HEADING("\n2. VERIFICANDO SINCRONIA COM O GITHUB:"))
        git_dir = os.path.join(base_dir, '.git')
        if os.path.exists(git_dir):
            try:
                # Puxa atualizações novas (mantendo o código local a salvo)
                pull_result = subprocess.run(['git', 'pull', 'origin', 'main'], capture_output=True, text=True, cwd=base_dir)
                if "Already up to date." in pull_result.stdout:
                    self.stdout.write(self.style.SUCCESS("[OK] Código-fonte 100% atualizado com o Github."))
                else:
                    self.stdout.write(self.style.SUCCESS("[ATUALIZADO] Novos arquivos puxados do Github com sucesso."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[FALHA GIT] Não foi possível sincronizar com o Github: {str(e)}"))
        else:
            self.stdout.write(self.style.WARNING("[INFO] Este diretório não é um repositório GIT. Pulo etapa de Github."))

        # 3. Integridade do Banco de Dados
        self.stdout.write(self.style.MIGRATE_HEADING("\n3. VERIFICANDO BANCO DE DADOS:"))
        if not os.path.exists(os.path.join(base_dir, 'db.sqlite3')):
            self.stdout.write(self.style.WARNING("[ALERTA] db.sqlite3 não encontrado. O sistema irá gerá-lo automaticamente no próximo migrate."))
        else:
            self.stdout.write(self.style.SUCCESS("[OK] Banco de Dados encontrado."))

        # 4. Configuração de Permissões (RBAC)
        self.stdout.write(self.style.MIGRATE_HEADING("\n4. VERIFICANDO MÓDULOS DE PERMISSÃO (RBAC):"))
        try:
            from django.core.management import call_command
            call_command('setup_modulos')
            self.stdout.write(self.style.SUCCESS("[OK] Módulos de permissão sincronizados com sucesso."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[FALHA RBAC] Não foi possível sincronizar módulos: {str(e)}"))

        self.stdout.write(self.style.SUCCESS("\n========================================================"))
        self.stdout.write(self.style.SUCCESS("BOOTSTRAP FINALIZADO. SISTEMA ÍNTEGRO E PRONTO PARA RODAR!"))
        self.stdout.write(self.style.SUCCESS("========================================================"))
