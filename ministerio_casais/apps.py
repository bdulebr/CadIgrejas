from django.apps import AppConfig

class MinisterioCasaisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ministerio_casais'

    def ready(self):
        import ministerio_casais.signals
