"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: core/apps.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        import core.signals

        # Inicia o CRON apenas se não for comando de migração/shell para evitar duplicidades
        import sys
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv or 'waitress' in sys.argv:
            try:
                from core.scheduler import start_scheduler
                start_scheduler()
            except Exception as e:
                print(f"Erro ao iniciar o APScheduler: {e}")
