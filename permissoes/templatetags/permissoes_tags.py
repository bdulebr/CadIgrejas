"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: permissoes/templatetags/permissoes_tags.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.db.models import Q
from permissoes.models import PermissaoMembro, PermissaoPerfil, PermissaoDepartamento
from django.utils import timezone
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def has_menu_perm(user, modulo_slug):
    if not user.is_authenticated:
        return False
    if user.is_superuser or getattr(user, 'nivel_hierarquico', '') == 'super_admin':
        return True

    now = timezone.now()
    q_expiracao = Q(data_expiracao__isnull=True) | Q(data_expiracao__gt=now)

    if PermissaoMembro.objects.filter(q_expiracao, membro=user, modulo__slug=modulo_slug, pode_ver_menu=True).exists():
        return True

    if PermissaoPerfil.objects.filter(q_expiracao, perfil__membros=user, modulo__slug=modulo_slug, pode_ver_menu=True).exists():
        return True

    if hasattr(user, 'departamentos_liderados'):
        if PermissaoDepartamento.objects.filter(q_expiracao, departamento__in=user.departamentos_liderados.all(), modulo__slug=modulo_slug, pode_ver_menu=True).exists():
            return True

    return False

@register.filter
def has_action_perm(user, args_str):
    """
    Checks if a user has a specific action permission in a module.
    Usage: {% if request.user|has_action_perm:'casais,editar' %}
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser or getattr(user, 'nivel_hierarquico', '') == 'super_admin':
        return True

    try:
        modulo_slug, acao = args_str.split(',')
        modulo_slug = modulo_slug.strip()
        acao = acao.strip()
    except ValueError:
        return False

    now = timezone.now()
    q_expiracao = Q(data_expiracao__isnull=True) | Q(data_expiracao__gt=now)

    def has_action(perm):
        if acao in ['ver', 'editar', 'excluir']:
            return getattr(perm, f'pode_{acao}')
        return perm.acoes_extras.get(acao) == True

    perms_membro = PermissaoMembro.objects.filter(q_expiracao, membro=user, modulo__slug=modulo_slug)
    if any(has_action(p) for p in perms_membro):
        return True

    perms_perfil = PermissaoPerfil.objects.filter(q_expiracao, perfil__membros=user, modulo__slug=modulo_slug)
    if any(has_action(p) for p in perms_perfil):
        return True

    user_depts = user.departamentos_ativos.all() | user.departamentos_liderados.all() | user.departamentos_subliderados.all()
    perms_dept = PermissaoDepartamento.objects.filter(q_expiracao, departamento__in=user_depts.distinct(), modulo__slug=modulo_slug)
    if any(has_action(p) for p in perms_dept):
        return True

    return False
