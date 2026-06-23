"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: permissoes/views.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 2.0.0
* DATA DA ÚLTIMA ALTERAÇÃO: 23/06/2026
* LOG DE ALTERAÇÕES:
* - 23/06/2026: Refatoração RBAC 2.0 (Escopos, Prazos e Grupos)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from core.models import Membro
from gestao_membros.models import Departamento
from .models import ModuloSistema, PermissaoMembro, PermissaoDepartamento, PerfilAcesso, PermissaoPerfil
from django.utils.dateparse import parse_datetime

def is_super_admin(user):
    return user.is_superuser or user.nivel_hierarquico == 'super_admin'

@login_required
@user_passes_test(is_super_admin)
def painel_permissoes(request):
    membros = Membro.objects.filter(is_active=True).order_by('first_name')
    departamentos = Departamento.objects.all().order_by('nome')
    modulos = ModuloSistema.objects.all().order_by('nome')
    perfis = PerfilAcesso.objects.all().prefetch_related('membros').order_by('nome')

    # Dicts para evitar N+1
    membro_perms = {m.id: {mod.id: {'ver': False, 'editar': False, 'excluir': False, 'escopo': 'global', 'expiracao': None} for mod in modulos} for m in membros}
    dept_perms = {d.id: {mod.id: {'ver': False, 'editar': False, 'excluir': False, 'escopo': 'global', 'expiracao': None} for mod in modulos} for d in departamentos}
    perfil_perms = {p.id: {mod.id: {'ver': False, 'editar': False, 'excluir': False, 'escopo': 'global', 'expiracao': None} for mod in modulos} for p in perfis}

    for perm in PermissaoMembro.objects.all():
        if perm.membro_id in membro_perms:
            membro_perms[perm.membro_id][perm.modulo_id] = {
                'ver': perm.pode_ver, 'editar': perm.pode_editar, 'excluir': perm.pode_excluir,
                'escopo': perm.escopo_acesso, 'expiracao': perm.data_expiracao
            }

    for perm in PermissaoDepartamento.objects.all():
        if perm.departamento_id in dept_perms:
            dept_perms[perm.departamento_id][perm.modulo_id] = {
                'ver': perm.pode_ver, 'editar': perm.pode_editar, 'excluir': perm.pode_excluir,
                'escopo': perm.escopo_acesso, 'expiracao': perm.data_expiracao
            }

    for perm in PermissaoPerfil.objects.all():
        if perm.perfil_id in perfil_perms:
            perfil_perms[perm.perfil_id][perm.modulo_id] = {
                'ver': perm.pode_ver, 'editar': perm.pode_editar, 'excluir': perm.pode_excluir,
                'escopo': perm.escopo_acesso, 'expiracao': perm.data_expiracao
            }

    context = {
        'membros': membros,
        'departamentos': departamentos,
        'modulos': modulos,
        'perfis': perfis,
        'membro_perms': membro_perms,
        'dept_perms': dept_perms,
        'perfil_perms': perfil_perms,
    }
    return render(request, 'permissoes/dashboard.html', context)

def _processar_e_salvar_permissoes(request, modelo_permissao, obj_relacional, field_name, autor):
    """Helper para salvar as permissões extraindo do POST os escopos e expirações"""
    modelo_permissao.objects.filter(**{field_name: obj_relacional}).delete()
    modulos = ModuloSistema.objects.all()
    for mod in modulos:
        pode_ver = request.POST.get(f'ver_{mod.id}') == 'on'
        pode_editar = request.POST.get(f'editar_{mod.id}') == 'on'
        pode_excluir = request.POST.get(f'excluir_{mod.id}') == 'on'

        escopo = request.POST.get(f'escopo_{mod.id}', 'global')
        expiracao_str = request.POST.get(f'expiracao_{mod.id}', '')
        data_exp = parse_datetime(expiracao_str) if expiracao_str else None

        if pode_ver or pode_editar or pode_excluir:
            modelo_permissao.objects.create(
                **{field_name: obj_relacional},
                modulo=mod,
                pode_ver=pode_ver,
                pode_editar=pode_editar,
                pode_excluir=pode_excluir,
                escopo_acesso=escopo,
                data_expiracao=data_exp,
                concedido_por=autor
            )

@login_required
@user_passes_test(is_super_admin)
def salvar_permissoes_membro(request, membro_id):
    membro = get_object_or_404(Membro, id=membro_id)
    if request.method == 'POST':
        _processar_e_salvar_permissoes(request, PermissaoMembro, membro, 'membro', request.user)
        messages.success(request, f'Permissões (RBAC 2.0) atualizadas para {membro.get_full_name()}.')
    return redirect('permissoes:dashboard')

@login_required
@user_passes_test(is_super_admin)
def salvar_permissoes_departamento(request, departamento_id):
    departamento = get_object_or_404(Departamento, id=departamento_id)
    if request.method == 'POST':
        _processar_e_salvar_permissoes(request, PermissaoDepartamento, departamento, 'departamento', request.user)
        messages.success(request, f'Permissões (RBAC 2.0) atualizadas para {departamento.nome}.')
    return redirect('permissoes:dashboard')

@login_required
@user_passes_test(is_super_admin)
def salvar_permissoes_perfil(request, perfil_id):
    perfil = get_object_or_404(PerfilAcesso, id=perfil_id)
    if request.method == 'POST':
        _processar_e_salvar_permissoes(request, PermissaoPerfil, perfil, 'perfil', request.user)
        messages.success(request, f'Permissões atualizadas para o Grupo "{perfil.nome}".')
    return redirect('permissoes:dashboard')

@login_required
@user_passes_test(is_super_admin)
def criar_perfil_acesso(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao', '')
        if nome:
            PerfilAcesso.objects.create(nome=nome, descricao=descricao)
            messages.success(request, f'Grupo de Permissões "{nome}" criado com sucesso.')
    return redirect('permissoes:dashboard')

@login_required
@user_passes_test(is_super_admin)
def excluir_perfil_acesso(request, perfil_id):
    perfil = get_object_or_404(PerfilAcesso, id=perfil_id)
    perfil.delete()
    messages.success(request, f'Grupo "{perfil.nome}" excluído.')
    return redirect('permissoes:dashboard')

@login_required
@user_passes_test(is_super_admin)
def gerir_membros_perfil(request, perfil_id):
    perfil = get_object_or_404(PerfilAcesso, id=perfil_id)
    if request.method == 'POST':
        membros_ids = request.POST.getlist('membros')
        perfil.membros.set(Membro.objects.filter(id__in=membros_ids))
        messages.success(request, f'Membros do grupo "{perfil.nome}" atualizados.')
    return redirect('permissoes:dashboard')
