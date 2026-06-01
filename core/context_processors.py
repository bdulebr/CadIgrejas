from core.models import ConfiguracaoSistema, LinkRapido

def global_config(request):
    config = ConfiguracaoSistema.objects.first()
    links = LinkRapido.objects.all().order_by('ordem')
    return {
        'sys_config': config,
        'links_rapidos': links
    }
