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
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

from django.db.models import Q
from django.utils import timezone
from permissoes.models import PermissaoMembro, PermissaoPerfil, PermissaoDepartamento

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
