"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: permissoes/decorators.py
"""
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from django.db.models import Q
from permissoes.models import PermissaoMembro, PermissaoDepartamento, PermissaoPerfil

def requer_permissao(modulo_slug, acao='ver'):
    """
    Decorador centralizado de RBAC (Role-Based Access Control) + Escopo Temporário + Ações Granulares.
    acao pode ser: 'ver', 'editar', 'excluir' ou uma ação customizada que exista em acoes_extras.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            # Super Admin (God Mode Bypass)
            if request.user.is_superuser or getattr(request.user, 'nivel_hierarquico', '') == 'super_admin':
                return view_func(request, *args, **kwargs)

            now = timezone.now()
            q_expiracao = Q(data_expiracao__isnull=True) | Q(data_expiracao__gt=now)

            def has_action(perm):
                if acao in ['ver', 'editar', 'excluir']:
                    return getattr(perm, f'pode_{acao}')
                return perm.acoes_extras.get(acao) == True

            # 1. Verifica Permissão Direta do Membro
            perms_membro = PermissaoMembro.objects.filter(
                q_expiracao,
                membro=request.user,
                modulo__slug=modulo_slug
            )
            if any(has_action(p) for p in perms_membro):
                return view_func(request, *args, **kwargs)

            # 2. Verifica Permissão do Perfil (Roles)
            perms_perfil = PermissaoPerfil.objects.filter(
                q_expiracao,
                perfil__membros=request.user,
                modulo__slug=modulo_slug
            )
            if any(has_action(p) for p in perms_perfil):
                return view_func(request, *args, **kwargs)

            # 3. Verifica Permissão Herdada do Departamento
            user_depts = request.user.departamentos_ativos.all() | \
                         request.user.departamentos_liderados.all() | \
                         request.user.departamentos_subliderados.all()

            perms_dept = PermissaoDepartamento.objects.filter(
                q_expiracao,
                departamento__in=user_depts.distinct(),
                modulo__slug=modulo_slug
            )
            if any(has_action(p) for p in perms_dept):
                return view_func(request, *args, **kwargs)

            # Acesso Negado
            messages.error(request, f"Acesso Negado: Você não tem permissão para '{acao}' no módulo '{modulo_slug}'.")

            referer = request.META.get('HTTP_REFERER')
            if referer:
                return redirect(referer)
            return redirect('dashboard')

        return _wrapped_view
    return decorator
