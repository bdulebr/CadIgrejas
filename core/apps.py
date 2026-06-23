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

        # Considera os principais servidores WSGI/ASGI e o dev server do Django
        is_server = any(x in sys.argv for x in ['runserver', 'gunicorn', 'waitress', 'daphne', 'uvicorn', 'hupper'])

        if is_server:
            try:
                from core.scheduler import start_scheduler
                start_scheduler()
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Erro ao iniciar o APScheduler: {e}")
