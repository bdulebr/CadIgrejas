"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: permissoes/utils.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 18/06/2026 13:20
* LOG DE ALTERAÇÕES:
* - 18/06/2026 13:20: Auditoria e padronização global (Goal)
"""
from django.utils import timezone
from django.db.models import Q
from permissoes.models import PermissaoMembro, PermissaoDepartamento, PermissaoPerfil

def obter_escopo_acesso(membro, modulo_slug):
    """
    Retorna o nível máximo de escopo de acesso que o membro tem para o módulo fornecido.
    Ordem de precedência: 'global' > 'departamento' > 'proprio'.
    Se o membro for super_admin ou is_superuser, retorna 'global'.
    Se não houver permissão, retorna 'nenhum'.
    """
    if membro.is_superuser or getattr(membro, 'nivel_hierarquico', '') == 'super_admin':
        return 'global'

    now = timezone.now()
    q_expiracao = Q(data_expiracao__isnull=True) | Q(data_expiracao__gt=now)

    escopos = set()

    # 1. Permissões de Membro
    perms_membro = PermissaoMembro.objects.filter(
        q_expiracao,
        membro=membro,
        modulo__slug=modulo_slug
    )
    for p in perms_membro:
        escopos.add(p.escopo_acesso)

    # 2. Permissões de Perfil
    perms_perfil = PermissaoPerfil.objects.filter(
        q_expiracao,
        perfil__membros=membro,
        modulo__slug=modulo_slug
    )
    for p in perms_perfil:
        escopos.add(p.escopo_acesso)

    # 3. Permissões de Departamento
    user_depts = membro.departamentos_ativos.all() | \
        membro.departamentos_liderados.all() | \
        membro.departamentos_subliderados.all()

    perms_dept = PermissaoDepartamento.objects.filter(
        q_expiracao,
        departamento__in=user_depts.distinct(),
        modulo__slug=modulo_slug
    )
    for p in perms_dept:
        escopos.add(p.escopo_acesso)

    # Resolve precedência
    if 'global' in escopos:
        return 'global'
    if 'departamento' in escopos:
        return 'departamento'
    if 'proprio' in escopos:
        return 'proprio'

    return 'nenhum'
