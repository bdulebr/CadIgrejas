"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: ministerio_casais/apps.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.apps import AppConfig

class MinisterioCasaisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ministerio_casais'

    def ready(self):
        import ministerio_casais.signals
