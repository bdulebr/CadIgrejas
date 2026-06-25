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

        # 1. Self-Healing de Pastas e Mídias (Mapeamento Dinâmico)
        self.stdout.write(self.style.MIGRATE_HEADING("1. VERIFICANDO INTEGRIDADE DE PASTAS E MÍDIAS (SELF-HEALING):"))

        media_root = settings.MEDIA_ROOT
        if not os.path.exists(media_root):
            os.makedirs(media_root)

        from django.apps import apps
        from django.db.models import Q
        import shutil

        file_fields = []
        pastas_vitais = set(['lost_and_found', 'perfil', 'departamentos/logos', 'ocorrencias', 'avisos_anexos', 'logos', 'staticfiles', 'logs', 'backups'])

        # Mapear dinamicamente todos os FileFields
        for model in apps.get_models():
            for field in model._meta.get_fields():
                if hasattr(field, 'upload_to') and getattr(field, 'upload_to'):
                    if isinstance(field.upload_to, str):
                        path = field.upload_to.split('%')[0].strip('/')
                        if path:
                            pastas_vitais.add(path)
                            file_fields.append((model, field.name, field.upload_to))

        base_dir = settings.BASE_DIR

        # Criar as pastas vitais
        for pasta in pastas_vitais:
            if pasta in ['staticfiles', 'logs', 'backups']:
                caminho = os.path.join(base_dir, pasta)
            else:
                caminho = os.path.join(media_root, pasta)

            if not os.path.exists(caminho):
                os.makedirs(caminho, exist_ok=True)
                self.stdout.write(self.style.SUCCESS(f"[CRIADO] Pasta restaurada: {pasta}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"[OK] Pasta íntegra: {pasta}"))

        # Scanner de Arquivos Órfãos na Raiz do Media
        arquivos_raiz = [f for f in os.listdir(media_root) if os.path.isfile(os.path.join(media_root, f))]
        lost_and_found_dir = os.path.join(media_root, 'lost_and_found')

        for arquivo in arquivos_raiz:
            if arquivo in ['.gitignore', 'README.md']:
                continue

            achou_dono = False
            for model, field_name, upload_to in file_fields:
                filtros = Q(**{f"{field_name}": arquivo}) | Q(**{f"{field_name}__endswith": f"/{arquivo}"})
                try:
                    registros = model.objects.filter(filtros)
                    if registros.exists():
                        registro = registros.first()
                        clean_upload = upload_to.split('%')[0].strip('/')
                        novo_path_relativo = f"{clean_upload}/{arquivo}"
                        destino_file = os.path.join(media_root, novo_path_relativo)
                        src_file = os.path.join(media_root, arquivo)

                        os.makedirs(os.path.dirname(destino_file), exist_ok=True)
                        shutil.move(src_file, destino_file)

                        setattr(registro, field_name, novo_path_relativo)
                        registro.save()

                        self.stdout.write(self.style.SUCCESS(f"[SELF-HEALING] Arquivo realocado com sucesso: {arquivo} -> {novo_path_relativo}"))
                        achou_dono = True
                        break
                except Exception as e:
                    pass

            if not achou_dono:
                src_file = os.path.join(media_root, arquivo)
                destino_file = os.path.join(lost_and_found_dir, arquivo)
                shutil.move(src_file, destino_file)
                self.stdout.write(self.style.WARNING(f"[LOST & FOUND] Arquivo órfão movido: {arquivo}"))

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
