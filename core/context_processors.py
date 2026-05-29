from core.models import ConfiguracaoSistema

def global_config(request):
    config = ConfiguracaoSistema.objects.first()
    return {
        'sys_config': config
    }
