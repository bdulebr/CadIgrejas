from core.models import ConfiguracaoSistema, LinkRapido

def global_config(request):
    config = ConfiguracaoSistema.objects.first()
    todas_links = LinkRapido.objects.filter(is_active=True).order_by('ordem')

    links_permitidos = []
    for link in todas_links:
        if link.visibilidade == 'geral':
            links_permitidos.append(link)
        elif link.visibilidade == 'membros' and request.user.is_authenticated:
            links_permitidos.append(link)
        elif link.visibilidade == 'lideres' and request.user.is_authenticated:
            if request.user.nivel_hierarquico in ['super_admin', 'pastor_regente', 'pastor', 'missionario', 'lider', 'sub_lider']:
                links_permitidos.append(link)
        elif link.visibilidade == 'admin' and request.user.is_authenticated:
            if request.user.nivel_hierarquico == 'super_admin' or request.user.is_superuser:
                links_permitidos.append(link)
    is_almoxarifado_team = False
    if request.user.is_authenticated:
        try:
            from almoxarifado.views import can_edit_almoxarifado
            is_almoxarifado_team = can_edit_almoxarifado(request.user)
        except ImportError:
            pass

    return {
        'sys_config': config,
        'links_rapidos': links_permitidos,
        'is_almoxarifado_team': is_almoxarifado_team
    }
