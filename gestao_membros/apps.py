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
