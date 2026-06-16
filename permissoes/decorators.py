"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: permissoes/decorators.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from permissoes.models import PermissaoMembro, PermissaoDepartamento

def requer_permissao(modulo_slug, acao='ver'):
    """
    Decorador centralizado de RBAC (Role-Based Access Control).
    acao pode ser: 'ver', 'editar', 'excluir'
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            # Super Admin (God Mode Bypass)
            if request.user.is_superuser or request.user.nivel_hierarquico == 'super_admin':
                return view_func(request, *args, **kwargs)

            # Verifica Permissão Direta do Membro
            kwargs_permissao = {f"pode_{acao}": True}

            tem_permissao_membro = PermissaoMembro.objects.filter(
                membro=request.user,
                modulo__slug=modulo_slug,
                **kwargs_permissao
            ).exists()

            if tem_permissao_membro:
                return view_func(request, *args, **kwargs)

            # Verifica Permissão Herdada do Departamento
            # Consideramos os departamentos onde ele é ativo, líder ou sublider
            user_depts = request.user.departamentos_ativos.all() | \
                         request.user.departamentos_liderados.all() | \
                         request.user.departamentos_subliderados.all()
            user_depts = user_depts.distinct()

            tem_permissao_dept = PermissaoDepartamento.objects.filter(
                departamento__in=user_depts,
                modulo__slug=modulo_slug,
                **kwargs_permissao
            ).exists()

            if tem_permissao_dept:
                return view_func(request, *args, **kwargs)

            # Acesso Negado
            messages.error(request, f"Acesso Negado: Você não tem permissão para {acao} no módulo '{modulo_slug}'.")

            # Tenta mandar para o dashboard anterior ou para a home
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return redirect(referer)
            return redirect('dashboard')

        return _wrapped_view
    return decorator
