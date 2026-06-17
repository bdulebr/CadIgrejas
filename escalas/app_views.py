"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: escalas/app_views.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from escalas.models import Escala, CultoEvento
from gestao_membros.models import Indisponibilidade, Departamento
from core.models import Membro

def is_lider_any_dept(user):
    return user.departamentos_liderados.exists() or user.nivel_hierarquico in ['super_admin', 'pastor']

@login_required
def app_home(request):
    hoje = timezone.now().date()
    # Pega as escalas futuras do membro logado
    escalas = Escala.objects.filter(
        membro_escalado=request.user,
        data_escala__gte=hoje
    ).order_by('data_escala', 'horario_inicio')

    is_lider = is_lider_any_dept(request.user)

    return render(request, 'escalas/app/app_home.html', {
        'escalas': escalas,
        'is_lider': is_lider
    })

@login_required
def app_disponibilidade(request):
    hoje = timezone.now().date()
    # Pega as indisponibilidades ativas/futuras
    indisponibilidades = Indisponibilidade.objects.filter(
        membro=request.user,
        data_fim__gte=hoje
    ).order_by('data_inicio')

    is_lider = is_lider_any_dept(request.user)

    return render(request, 'escalas/app/app_disponibilidade.html', {
        'indisponibilidades': indisponibilidades,
        'is_lider': is_lider
    })

@login_required
def app_salvar_disponibilidade(request):
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '').strip()
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')

        if motivo and data_inicio and data_fim:
            Indisponibilidade.objects.create(
                membro=request.user,
                motivo=motivo,
                data_inicio=data_inicio,
                data_fim=data_fim
            )
            messages.success(request, "Ausência registrada com sucesso.")
        else:
            messages.error(request, "Preencha todos os campos obrigatórios.")

    return redirect('app_disponibilidade')

@login_required
def app_remover_disponibilidade(request, ind_id):
    if request.method == 'POST':
        ind = get_object_or_404(Indisponibilidade, id=ind_id, membro=request.user)
        ind.delete()
        messages.success(request, "Ausência removida com sucesso.")
    return redirect('app_disponibilidade')

@login_required
def app_lider(request):
    if not is_lider_any_dept(request.user):
        messages.error(request, "Acesso Negado. Você não é líder.")
        return redirect('app_home')

    if request.user.nivel_hierarquico in ['super_admin', 'pastor']:
        departamentos_liderados = Departamento.objects.all()
    else:
        departamentos_liderados = request.user.departamentos_liderados.all()

    # Informacoes pro painel
    hoje = timezone.now().date()
    limite = hoje + timedelta(days=30)

    membros_ids = set()
    for d in departamentos_liderados:
        for m in d.membros_ativos.all():
            membros_ids.add(m.id)

    total_membros = len(membros_ids)
    ausencias_ativas = Indisponibilidade.objects.filter(
        membro_id__in=membros_ids,
        data_inicio__lte=limite,
        data_fim__gte=hoje
    ).count()

    # Ponto de Check-in de hoje
    checkins_hoje = Escala.objects.filter(
        departamento_alocado__in=departamentos_liderados,
        data_escala=hoje,
        checkin_realizado=True
    ).order_by('-data_hora_checkin')

    ausentes_hoje = Escala.objects.filter(
        departamento_alocado__in=departamentos_liderados,
        data_escala=hoje,
        checkin_realizado=False
    ).order_by('horario_inicio')

    escalas_hoje_total = Escala.objects.filter(
        departamento_alocado__in=departamentos_liderados,
        data_escala=hoje
    ).count()

    return render(request, 'escalas/app/app_lider.html', {
        'is_lider': True,
        'departamentos_liderados': departamentos_liderados,
        'total_membros': total_membros,
        'ausencias_ativas': ausencias_ativas,
        'checkins_hoje': checkins_hoje,
        'ausentes_hoje': ausentes_hoje,
        'escalas_hoje_total': escalas_hoje_total
    })

@login_required
def app_motor_ia(request):
    if request.method == 'POST':
        if not is_lider_any_dept(request.user):
            messages.error(request, "Acesso Negado.")
            return redirect('app_home')

        depto_id = request.POST.get('departamento_id')
        if not depto_id:
            messages.error(request, "Departamento inválido.")
            return redirect('app_lider')

        depto = get_object_or_404(Departamento, id=depto_id)

        # Determinar Mês/Ano (Próximo mês)
        hoje = timezone.now().date()
        mes_alvo = hoje.month + 1 if hoje.day > 15 else hoje.month
        ano_alvo = hoje.year
        if mes_alvo > 12:
            mes_alvo = 1
            ano_alvo += 1

        mes_ano_str = f"{mes_alvo:02d}/{ano_alvo}"

        from escalas.models import CompetenciaEscala
        comp, created = CompetenciaEscala.objects.get_or_create(
            departamento=depto,
            mes_ano=mes_ano_str,
            defaults={'status': 'rascunho'}
        )

        # Chama a view de auto-escala passando o comp_id (Usamos a HTTP Request injetada ou chamamos a funcao direta)
        # Como as funcoes de auto escala dependem de request.POST.get('comp_id'), vamos injetar o comp_id no POST.
        request.POST._mutable = True
        request.POST['comp_id'] = comp.id
        request.POST._mutable = False

        from escalas.views import gerar_escala_automatica
        # O gerar_escala_automatica retorna um HttpResponseRedirect
        response = gerar_escala_automatica(request)

        messages.success(request, f"Motor de IA acionado para a competência {mes_ano_str} do departamento {depto.nome}!")

    return redirect('app_lider')
