"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: gestao_membros/apps.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.apps import AppConfig
from django.db.models.signals import post_migrate

def seed_system_departments(sender, **kwargs):
    from django.core.management import call_command
    call_command('setup_departamentos')

class GestaoMembrosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestao_membros'

    def ready(self):
        post_migrate.connect(seed_system_departments, sender=self)
