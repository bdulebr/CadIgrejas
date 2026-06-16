"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: core/management/commands/backup_db.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
import os
import shutil
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from intranet.services.google_drive import upload_arquivo_drive

class Command(BaseCommand):
    help = 'Cria um backup do banco de dados SQLite e faz upload para o Google Drive.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando processo de backup da base de dados...")

        # Caminho original do DB
        db_path = settings.DATABASES['default']['NAME']

        if not os.path.exists(db_path):
            self.stdout.write(self.style.ERROR(f"Banco de dados não encontrado em {db_path}"))
            return

        # Gera nome com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"db_backup_pve_{timestamp}.sqlite3"
        backup_zip_filename = f"db_backup_pve_{timestamp}.zip"

        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        backup_path = os.path.join(backup_dir, backup_filename)
        zip_path = os.path.join(backup_dir, backup_zip_filename)

        try:
            # 1. Copiar o arquivo
            shutil.copy2(db_path, backup_path)
            self.stdout.write(f"Cópia local criada: {backup_path}")

            # 2. Comprimir o arquivo
            import zipfile
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(backup_path, arcname=backup_filename)
            self.stdout.write(f"Arquivo compactado criado: {zip_path}")

            # 3. Enviar pro Google Drive
            self.stdout.write("Enviando para o Google Drive...")
            link = upload_arquivo_drive(zip_path, backup_zip_filename)

            if link:
                self.stdout.write(self.style.SUCCESS(f"Backup enviado com sucesso! Link: {link}"))
            else:
                self.stdout.write(self.style.WARNING("O backup local foi criado, mas o upload para o Google Drive falhou (verifique as credenciais)."))

            # Limpeza do arquivo .sqlite3 solto (mantém só o zip local)
            if os.path.exists(backup_path):
                os.remove(backup_path)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro durante o backup: {str(e)}"))
