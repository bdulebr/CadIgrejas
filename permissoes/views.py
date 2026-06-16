"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: permissoes/views.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from core.models import Membro
from gestao_membros.models import Departamento
from .models import ModuloSistema, PermissaoMembro, PermissaoDepartamento

def is_super_admin(user):
    return user.is_superuser or user.nivel_hierarquico == 'super_admin'

@login_required
@user_passes_test(is_super_admin)
def painel_permissoes(request):
    membros = Membro.objects.filter(is_active=True).order_by('first_name')
    departamentos = Departamento.objects.all().order_by('nome')
    modulos = ModuloSistema.objects.all().order_by('nome')

    # Pre-calculating permissions to avoid N+1 queries in the template
    # Format: membro_perms[membro_id][modulo_id] = {'ver': True, 'editar': False, 'excluir': False}
    membro_perms = {}
    for m in membros:
        membro_perms[m.id] = {mod.id: {'ver': False, 'editar': False, 'excluir': False} for mod in modulos}

    for perm in PermissaoMembro.objects.all():
        if perm.membro_id in membro_perms:
            membro_perms[perm.membro_id][perm.modulo_id] = {
                'ver': perm.pode_ver,
                'editar': perm.pode_editar,
                'excluir': perm.pode_excluir
            }

    dept_perms = {}
    for d in departamentos:
        dept_perms[d.id] = {mod.id: {'ver': False, 'editar': False, 'excluir': False} for mod in modulos}

    for perm in PermissaoDepartamento.objects.all():
        if perm.departamento_id in dept_perms:
            dept_perms[perm.departamento_id][perm.modulo_id] = {
                'ver': perm.pode_ver,
                'editar': perm.pode_editar,
                'excluir': perm.pode_excluir
            }

    context = {
        'membros': membros,
        'departamentos': departamentos,
        'modulos': modulos,
        'membro_perms': membro_perms,
        'dept_perms': dept_perms,
    }
    return render(request, 'permissoes/dashboard.html', context)

@login_required
@user_passes_test(is_super_admin)
def salvar_permissoes_membro(request, membro_id):
    membro = get_object_or_404(Membro, id=membro_id)
    if request.method == 'POST':
        PermissaoMembro.objects.filter(membro=membro).delete()

        modulos = ModuloSistema.objects.all()
        for mod in modulos:
            pode_ver = request.POST.get(f'ver_{mod.id}') == 'on'
            pode_editar = request.POST.get(f'editar_{mod.id}') == 'on'
            pode_excluir = request.POST.get(f'excluir_{mod.id}') == 'on'

            if pode_ver or pode_editar or pode_excluir:
                PermissaoMembro.objects.create(
                    membro=membro,
                    modulo=mod,
                    pode_ver=pode_ver,
                    pode_editar=pode_editar,
                    pode_excluir=pode_excluir
                )

        messages.success(request, f'Permissões atualizadas para o membro {membro.get_full_name()}.')
    return redirect('permissoes:dashboard')

@login_required
@user_passes_test(is_super_admin)
def salvar_permissoes_departamento(request, departamento_id):
    departamento = get_object_or_404(Departamento, id=departamento_id)
    if request.method == 'POST':
        PermissaoDepartamento.objects.filter(departamento=departamento).delete()

        modulos = ModuloSistema.objects.all()
        for mod in modulos:
            pode_ver = request.POST.get(f'ver_{mod.id}') == 'on'
            pode_editar = request.POST.get(f'editar_{mod.id}') == 'on'
            pode_excluir = request.POST.get(f'excluir_{mod.id}') == 'on'

            if pode_ver or pode_editar or pode_excluir:
                PermissaoDepartamento.objects.create(
                    departamento=departamento,
                    modulo=mod,
                    pode_ver=pode_ver,
                    pode_editar=pode_editar,
                    pode_excluir=pode_excluir
                )

        messages.success(request, f'Permissões atualizadas para o departamento {departamento.nome}.')
    return redirect('permissoes:dashboard')
