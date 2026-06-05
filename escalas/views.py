from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse, FileResponse, HttpResponseForbidden
from .models import Escala, CompetenciaEscala, CultoEvento
from gestao_membros.models import Departamento, Indisponibilidade, Funcao
from core.models import Membro, ConfiguracaoSistema
from datetime import datetime, date, timedelta
import calendar
from django.db.models import Q

# Serviços externos
from intranet.services.google_calendar import criar_evento_escala
from intranet.services.gmail_service import enviar_email_html
from .pdf_generator import gerar_pdf_competencia

import openpyxl
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import csv

def is_lider(user):
    return user.nivel_hierarquico in ['super_admin', 'pastor_regente', 'pastor', 'missionario', 'lider', 'sub_lider']

def get_departamentos_permitidos(user):
    config = ConfiguracaoSistema.objects.first()
    is_global = False
    if config and config.lider_global_escalas == user:
        is_global = True

    if user.nivel_hierarquico == 'super_admin' or user.is_superuser or is_global:
        return Departamento.objects.all()
    else:
        lider = user.departamentos_liderados.all()
        sub = user.departamentos_subliderados.all()
        return (lider | sub).distinct()

def is_trabalhando(membro, data_atual, start_time_str, end_time_str):
    if not membro.dias_trabalho:
        return False

    dia_semana_str = str(data_atual.weekday())
    dias_trabalho_list = membro.dias_trabalho.split(',')

    if dia_semana_str not in dias_trabalho_list:
        return False

    if not membro.horario_trabalho_inicio or not membro.horario_trabalho_fim:
        return True

    try:
        from datetime import datetime
        ws = membro.horario_trabalho_inicio
        we = membro.horario_trabalho_fim
        es = datetime.strptime(start_time_str, '%H:%M').time()
        ee = datetime.strptime(end_time_str, '%H:%M').time()

        if es < we and ee > ws:
            return True
    except ValueError:
        pass

    return False

@login_required
def minhas_escalas(request):
    departamentos = request.user.departamentos_ativos.all() | request.user.departamentos_liderados.all() | request.user.departamentos_subliderados.all()
    departamentos = departamentos.distinct()

    # Filtro
    dept_id = request.GET.get('departamento_id')
    escalas = Escala.objects.filter(
        membro_escalado=request.user,
        competencia__status='publicada'
    ).order_by('data_escala', 'horario_inicio')

    if dept_id:
        escalas = escalas.filter(departamento_alocado_id=dept_id)

    dias_semana = [(str(i), nome) for i, nome in enumerate(['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'])]
    dias_trabalho_list = request.user.dias_trabalho.split(',') if request.user.dias_trabalho else []

    historico_indisponibilidades = Indisponibilidade.objects.filter(membro=request.user).order_by('-data_inicio')

    return render(request, 'escalas/minhas_escalas.html', {
        'escalas': escalas,
        'departamentos': departamentos,
        'dias_semana': dias_semana,
        'dias_trabalho_list': dias_trabalho_list,
        'historico_indisponibilidades': historico_indisponibilidades
    })

@login_required
@user_passes_test(is_lider)
def painel_escalas(request):
    departamentos = get_departamentos_permitidos(request.user)
    competencias = CompetenciaEscala.objects.filter(departamento__in=departamentos).order_by('-data_criacao')

    return render(request, 'escalas/painel.html', {
        'competencias': competencias,
        'departamentos': departamentos
    })

@login_required
@user_passes_test(is_lider)
def nova_competencia(request):
    if request.method == 'POST':
        departamento_id = request.POST.get('departamento_id')
        mes_ano = request.POST.get('mes_ano')

        dept = get_object_or_404(Departamento, id=departamento_id)

        # Validar permissão
        deps_permitidos = get_departamentos_permitidos(request.user)
        if dept not in deps_permitidos:
            messages.error(request, 'Sem permissão para este departamento.')
            return redirect('painel_escalas')

        try:
            comp = CompetenciaEscala.objects.create(
                departamento=dept,
                mes_ano=mes_ano,
                status='rascunho'
            )
            return redirect('editor_escala_manual', comp_id=comp.id)
        except IntegrityError:
            comp = CompetenciaEscala.objects.get(departamento=dept, mes_ano=mes_ano)
            messages.warning(request, 'Competência já existe. Você foi redirecionado para o editor.')
            return redirect('editor_escala_manual', comp_id=comp.id)

    return redirect('painel_escalas')

@login_required
@user_passes_test(is_lider)
def excluir_competencia(request, comp_id):
    comp = get_object_or_404(CompetenciaEscala, id=comp_id)

    deps_permitidos = get_departamentos_permitidos(request.user)
    if comp.departamento not in deps_permitidos:
        return HttpResponseForbidden("Sem permissão para excluir escalas deste departamento.")

    if request.method == 'POST':
        comp.delete()
        messages.success(request, 'Escala (Competência) excluída com sucesso!')

    return redirect('painel_escalas')

@login_required
@user_passes_test(is_lider)
def editor_escala_manual(request, comp_id):
    comp = get_object_or_404(CompetenciaEscala, id=comp_id)
    deps_permitidos = get_departamentos_permitidos(request.user)
    if comp.departamento not in deps_permitidos:
        messages.error(request, 'Acesso negado.')
        return redirect('painel_escalas')

    escalas = Escala.objects.filter(competencia=comp).order_by('data_escala', 'horario_inicio')
    funcoes = Funcao.objects.filter(departamento=comp.departamento)

    membros = Membro.objects.filter(
        Q(is_active=True) & (
            Q(departamentos_ativos=comp.departamento) |
            Q(departamentos_liderados=comp.departamento) |
            Q(departamentos_subliderados=comp.departamento)
        )
    ).distinct().order_by('first_name')

    import calendar
    import json

    # Calcular datas do mes
    mes, ano = map(int, comp.mes_ano.split('/'))
    num_days = calendar.monthrange(ano, mes)[1]

    # Obter configuração de slots do departamento
    from gestao_membros.models import ConfiguracaoSlotEscala
    configuracoes = ConfiguracaoSlotEscala.objects.filter(departamento=comp.departamento)

    DIAS_SEMANA_PT = {
        0: 'SEG',
        1: 'TER',
        2: 'QUA',
        3: 'QUI',
        4: 'SEX',
        5: 'SÁB',
        6: 'DOM'
    }

    dias_escala = []

    # Prepara o mapa de alocações atuais: {(data, tipo_evento, funcao_id): [escala1, escala2]}
    alocacoes_map = {}
    for escala in escalas:
        key = (escala.data_escala.strftime('%Y-%m-%d'), escala.tipo_evento, escala.funcao_alocada_id if escala.funcao_alocada else 0)
        if key not in alocacoes_map:
            alocacoes_map[key] = []
        alocacoes_map[key].append({
            'escala_id': escala.id,
            'membro_id': escala.membro_escalado.id,
            'membro_nome': escala.membro_escalado.get_full_name(),
            'membro_foto': escala.membro_escalado.foto_perfil.url if escala.membro_escalado.foto_perfil else None
        })

    for day in range(1, num_days + 1):
        d = date(ano, mes, day)
        dia_semana = d.weekday()

        # Buscar eventos recorrentes e extraordinários para este dia
        eventos_hoje = []

        # 1. Recorrentes
        recorrentes = CultoEvento.objects.filter(tipo='padrao', dia_semana=dia_semana)
        for ev in recorrentes:
            key_ev = ev.chave_slug if ev.chave_slug else str(ev.id)
            eventos_hoje.append((key_ev, ev.nome))

        # 2. Extraordinários
        extras = CultoEvento.objects.filter(tipo='extra', data_evento=d)
        for ev in extras:
            key_ev = ev.chave_slug if ev.chave_slug else str(ev.id)
            eventos_hoje.append((key_ev, ev.nome))

        for evento_id, evento_nome in eventos_hoje:
            # Pega as configs desse evento
            configs_evento = configuracoes.filter(tipo_evento=evento_id)
            data_str = d.strftime('%Y-%m-%d')
            funcoes_dia = []

            if configs_evento.exists():
                for config in configs_evento:
                    key = (data_str, evento_id, config.funcao.id)
                    alocados = alocacoes_map.get(key, [])

                    funcoes_dia.append({
                        'funcao_id': config.funcao.id,
                        'funcao_nome': config.funcao.nome,
                        'vagas': config.quantidade,
                        'alocados': alocados
                    })

            dias_escala.append({
                'data_str': data_str,
                'data_br': d.strftime('%d/%m'),
                'dia_semana_nome': DIAS_SEMANA_PT.get(dia_semana, ''),
                'evento_id': evento_id,
                'evento_nome': evento_nome,
                'funcoes': funcoes_dia,
                'sem_config': not configs_evento.exists()
            })

    return render(request, 'escalas/editor_manual.html', {
        'competencia': comp,
        'escalas': escalas,
        'funcoes': funcoes,
        'membros': membros,
        'dias_escala': dias_escala,
    })

@login_required
@user_passes_test(is_lider)
def salvar_slot_escala(request, comp_id):
    if request.method == 'POST':
        comp = get_object_or_404(CompetenciaEscala, id=comp_id)

        membro_id = request.POST.get('membro_id')
        funcao_id = request.POST.get('funcao_id')
        data_escala = request.POST.get('data_escala')
        horario_inicio = request.POST.get('horario_inicio')
        horario_fim = request.POST.get('horario_fim')
        tipo_evento = request.POST.get('tipo_evento')

        # Validação Anti-Conflito e Burnout
        is_indisponivel = Indisponibilidade.objects.filter(
            membro_id=membro_id, data_inicio__lte=data_escala, data_fim__gte=data_escala
        ).exists()
        if is_indisponivel:
            messages.error(request, 'Membro está marcado como indisponível nesta data.')
            return redirect('editor_escala_manual', comp_id=comp.id)

        escalas_mesmo_dia = Escala.objects.filter(membro_escalado_id=membro_id, data_escala=data_escala)
        for esc in escalas_mesmo_dia:
            if esc.departamento_alocado != comp.departamento:
                messages.error(request, f'Conflito! O voluntário já está escalado neste dia no departamento: {esc.departamento_alocado.nome}.')
                return redirect('editor_escala_manual', comp_id=comp.id)

        membro_obj = get_object_or_404(Membro, id=membro_id)
        data_obj = datetime.strptime(data_escala, '%Y-%m-%d')

        if is_trabalhando(membro_obj, data_obj, horario_inicio, horario_fim):
            messages.error(request, 'Aviso de Expediente: O voluntário está trabalhando/estudando neste dia/horário.')
            return redirect('editor_escala_manual', comp_id=comp.id)

        escalas_mes = Escala.objects.filter(
            membro_escalado_id=membro_id,
            data_escala__year=data_obj.year,
            data_escala__month=data_obj.month
        ).count()
        if escalas_mes >= 5:
            messages.warning(request, 'Aviso (Burnout): Este voluntário já atingiu 5 escalas no mês. Escala forçada salva.')

        try:
            nova = Escala.objects.create(
                competencia=comp,
                membro_escalado_id=membro_id,
                departamento_alocado=comp.departamento,
                funcao_alocada_id=funcao_id if funcao_id else None,
                data_escala=data_escala,
                horario_inicio=horario_inicio,
                horario_fim=horario_fim,
                tipo_evento=tipo_evento,
                status='confirmado'
            )
            # Se for publicada, re-gera o pdf e avisa a pessoa (escala_atualizada)
            if comp.status == 'publicada':
                gerar_pdf_competencia(comp.id)
                membro = Membro.objects.get(id=membro_id)
                if membro.email:
                    enviar_email_html(membro.email, f"Atualização de Escala - {comp.departamento.nome}", "escala_atualizada.html", {
                        'nome': membro.first_name,
                        'departamento': comp.departamento.nome,
                        'departamento_logo': '',
                        'link_painel': f"{settings.BASE_URL}/minhas-escalas/"
                    })
            messages.success(request, 'Slot salvo com sucesso.')
        except IntegrityError:
            messages.error(request, 'Conflito! A mesma pessoa já está alocada neste exato dia/horário.')

    return redirect('editor_escala_manual', comp_id=comp_id)

@login_required
@user_passes_test(is_lider)
def deletar_slot_escala(request, escala_id):
    escala = get_object_or_404(Escala, id=escala_id)
    comp_id = escala.competencia.id

    membro = escala.membro_escalado
    departamento = escala.departamento_alocado.nome
    data_escala = escala.data_escala.strftime('%d/%m/%Y')
    horario_inicio = escala.horario_inicio.strftime('%H:%M')
    horario_fim = escala.horario_fim.strftime('%H:%M')
    is_publicada = escala.competencia.status == 'publicada'

    escala.delete()

    if is_publicada:
        gerar_pdf_competencia(comp_id)
        if membro.email:
            enviar_email_html(membro.email, f"Cancelamento de Escala - {departamento}", "escala_cancelada.html", {
                'nome': membro.first_name,
                'departamento': departamento,
                'departamento_logo': '',
                'data': data_escala,
                'horario_inicio': horario_inicio,
                'horario_fim': horario_fim,
                'link_painel': f"{settings.BASE_URL}/minhas-escalas/"
            })

    messages.success(request, 'Slot removido.')
    return redirect('editor_escala_manual', comp_id=comp_id)

@login_required
@user_passes_test(is_lider)
def publicar_competencia(request, comp_id):
    comp = get_object_or_404(CompetenciaEscala, id=comp_id)

    if not Escala.objects.filter(competencia=comp).exists():
        messages.error(request, 'Não há escalas neste rascunho para publicar.')
        return redirect('editor_escala_manual', comp_id=comp.id)

    comp.status = 'publicada'
    comp.save()

    # Gera o PDF via ReportLab
    sucesso = gerar_pdf_competencia(comp.id)
    if not sucesso:
        messages.warning(request, 'Erro ao gerar o PDF da escala.')

    # Enviar emails para todos os alocados
    membros = Membro.objects.filter(escalas_individuais__competencia=comp).distinct()
    for membro in membros:
        if membro.email:
            enviar_email_html(membro.email, f"Nova Escala Oficial - {comp.departamento.nome}", "nova_escala.html", {
                'nome': membro.first_name,
                'departamento': comp.departamento.nome,
                'departamento_logo': '',
                'data': comp.mes_ano,
                'horario_inicio': "Vários",
                'horario_fim': "Vários",
                'link_painel': f"{settings.BASE_URL}/minhas-escalas/"
            })

    messages.success(request, f'A Escala de {comp.mes_ano} foi publicada e emails enviados!')
    return redirect('painel_escalas')


@login_required
def registrar_indisponibilidade(request):
    if request.method == 'POST':
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')
        motivo = request.POST.get('motivo')

        try:
            Indisponibilidade.objects.create(
                membro=request.user,
                data_inicio=data_inicio,
                data_fim=data_fim,
                motivo=motivo
            )
            messages.success(request, 'Período de indisponibilidade registrado.')
        except Exception as e:
            messages.error(request, 'Erro ao registrar ausência.')

    return redirect('minhas_escalas')

@login_required
def remover_indisponibilidade(request, ind_id):
    if request.method == 'POST':
        from gestao_membros.models import Indisponibilidade
        try:
            indisp = Indisponibilidade.objects.get(id=ind_id, membro=request.user)
            indisp.delete()
            messages.success(request, 'Registro de ausência removido com sucesso.')
        except Indisponibilidade.DoesNotExist:
            messages.error(request, 'Registro não encontrado ou sem permissão.')
    return redirect('minhas_escalas')

@login_required
def salvar_disponibilidade_fixa(request):
    if request.method == 'POST':
        user = request.user

        user.horario_trabalho_inicio = request.POST.get('horario_trabalho_inicio') or None
        user.horario_trabalho_fim = request.POST.get('horario_trabalho_fim') or None

        dias_trabalho_lista = request.POST.getlist('dias_trabalho')
        user.dias_trabalho = ",".join(dias_trabalho_lista)

        user.save()
        messages.success(request, 'Disponibilidade de Trabalho/Estudo salva com sucesso!')

    return redirect('minhas_escalas')

def baixar_escala_publica(request):
    if request.method == 'POST':
        departamento_id = request.POST.get('departamento_id')
        if not departamento_id:
            messages.error(request, 'Selecione um departamento.')
            return redirect('login')

        ultima_comp = CompetenciaEscala.objects.filter(
            departamento_id=departamento_id,
            status='publicada'
        ).order_by('-data_criacao').first()

        if ultima_comp and ultima_comp.pdf_gerado:
            try:
                return FileResponse(ultima_comp.pdf_gerado.open(), as_attachment=True, filename=f"Escala_{ultima_comp.departamento.nome}_{ultima_comp.mes_ano.replace('/', '_')}.pdf")
            except Exception as e:
                messages.error(request, f'Erro ao acessar o arquivo da escala: {str(e)}')
                return redirect('login')
        else:
            messages.warning(request, 'Ainda não há uma escala publicada para este departamento ou o PDF não foi gerado.')
            return redirect('login')

    return redirect('login')


# As outras views de exportação (excel, csv) continuam, só adaptá-las para aceitar comp_id se o cliente pedir.
@login_required
@user_passes_test(is_lider)
def exportar_escalas_pdf(request):
    return redirect('painel_escalas')

@login_required
@user_passes_test(is_lider)
def exportar_escalas_excel(request):
    return redirect('painel_escalas')

@login_required
@user_passes_test(is_lider)
def exportar_escalas_csv(request):
    return redirect('painel_escalas')


@login_required
@user_passes_test(is_lider)
def gerar_escala_automatica(request):
    if request.method == 'POST':
        comp_id = request.POST.get('comp_id')
        comp = get_object_or_404(CompetenciaEscala, id=comp_id)
        deps_permitidos = get_departamentos_permitidos(request.user)
        if comp.departamento not in deps_permitidos:
            messages.error(request, 'Sem permissão.')
            return redirect('painel_escalas')

        from gestao_membros.models import ConfiguracaoSlotEscala
        from django.db.models import Q
        import calendar
        from datetime import date

        configuracoes = ConfiguracaoSlotEscala.objects.filter(departamento=comp.departamento)
        if not configuracoes.exists():
            messages.error(request, 'O Motor falhou: Este departamento não possui nenhuma Configuração de Slot definida.')
            return redirect('editor_escala_manual', comp_id=comp.id)

        mes, ano = map(int, comp.mes_ano.split('/'))
        num_days = calendar.monthrange(ano, mes)[1]

        from core.models import Membro
        from escalas.models import CultoEvento, Escala
        from gestao_membros.models import Indisponibilidade, Funcao

        membros_elegiveis = Membro.objects.filter(
            Q(is_active=True) &
            (Q(departamentos_ativos=comp.departamento) | Q(departamentos_liderados=comp.departamento) | Q(departamentos_subliderados=comp.departamento))
        ).distinct()

        # 1. Coletar dados para o Groq
        membros_data = []
        for m in membros_elegiveis:
            indisp = Indisponibilidade.objects.filter(membro=m, data_inicio__year=ano, data_inicio__month=mes)
            datas_indisp = []
            for i in indisp:
                delta = (i.data_fim - i.data_inicio).days
                for d in range(delta + 1):
                    datas_indisp.append((i.data_inicio.replace(day=i.data_inicio.day + d)).strftime('%Y-%m-%d'))

            membros_data.append({
                'id': m.id,
                'nome': f"{m.first_name} {m.last_name} ({m.apelido})" if m.apelido else f"{m.first_name} {m.last_name}",
                'habilidades_ids': list(m.habilidades.values_list('id', flat=True)),
                'datas_indisponiveis': datas_indisp
            })

        eventos_data = []
        for day in range(1, num_days + 1):
            data_atual = date(ano, mes, day)
            dia_semana = data_atual.weekday()

            recorrentes = CultoEvento.objects.filter(tipo='padrao', dia_semana=dia_semana)
            extras = CultoEvento.objects.filter(tipo='extra', data_evento=data_atual)

            for ev in list(recorrentes) + list(extras):
                key_ev = ev.chave_slug if ev.chave_slug else str(ev.id)
                configs = configuracoes.filter(tipo_evento=key_ev)
                for config in configs:
                    for _ in range(config.quantidade):
                        eventos_data.append({
                            'evento_id': key_ev,
                            'data': data_atual.strftime('%Y-%m-%d'),
                            'horario_inicio': ev.horario_inicio.strftime('%H:%M'),
                            'horario_fim': ev.horario_fim.strftime('%H:%M'),
                            'funcao_id': config.funcao.id,
                            'funcao_nome': config.funcao.nome,
                            'requisitos_habilidades': list(config.funcao.requisitos.values_list('id', flat=True))
                        })

        if not eventos_data:
            messages.warning(request, 'Não há eventos neste mês para serem escalados com as configurações atuais.')
            return redirect('editor_escala_manual', comp_id=comp.id)

        try:
            from intranet.services.groq_ai import gerar_escala_inteligente_groq

            regras = {'limite_mensal': 4}
            resultado = gerar_escala_inteligente_groq(
                departamento_nome=comp.departamento.nome,
                mes=mes,
                ano=ano,
                membros=membros_data,
                eventos=eventos_data,
                regras=regras
            )

            alocacoes = resultado.get('alocacoes', [])
            slots_criados = 0

            for aloc in alocacoes:
                try:
                    membro_id = int(aloc.get('membro_id'))
                    data_obj = date.fromisoformat(aloc.get('data'))
                    funcao_obj = Funcao.objects.get(id=int(aloc.get('funcao_id')))
                    membro_obj = Membro.objects.get(id=membro_id)

                    # Trava Anti-Hallucination: Se a IA errar e tentar escalar duas vezes no mesmo dia
                    if Escala.objects.filter(membro_escalado=membro_obj, data_escala=data_obj).exists():
                        continue

                    Escala.objects.create(
                        competencia=comp,
                        membro_escalado=membro_obj,
                        departamento_alocado=comp.departamento,
                        funcao_alocada=funcao_obj,
                        data_escala=data_obj,
                        horario_inicio=aloc.get('horario_inicio', '19:30'),
                        horario_fim=aloc.get('horario_fim', '21:30'),
                        tipo_evento=aloc.get('evento_id'),
                        status='confirmado'
                    )
                    slots_criados += 1
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Erro no Motor Groq ao alocar: {e}")

            messages.success(request, f'✨ Motor LPU Groq finalizado! A IA analisou as restrições e alocou {slots_criados} voluntários com precisão matemática.')

        except Exception as e:
            messages.warning(request, f'Motor Groq AI falhou ({str(e)}). Acionando Motor Offline de emergência...')
            return gerar_escala_automatica_fallback(request)

        return redirect('editor_escala_manual', comp_id=comp.id)
    return redirect('painel_escalas')

def gerar_escala_automatica_fallback(request):
    if request.method == 'POST':
        comp_id = request.POST.get('comp_id')
        comp = get_object_or_404(CompetenciaEscala, id=comp_id)

        # Verificar permissao
        deps_permitidos = get_departamentos_permitidos(request.user)
        if comp.departamento not in deps_permitidos:
            messages.error(request, 'Sem permissão.')
            return redirect('painel_escalas')

        from gestao_membros.models import ConfiguracaoSlotEscala
        from django.db.models import Q
        import random
        import calendar

        # Obter todas as regras do departamento
        configuracoes = ConfiguracaoSlotEscala.objects.filter(departamento=comp.departamento)
        if not configuracoes.exists():
            messages.error(request, 'O Motor falhou: Este departamento não possui nenhuma Configuração de Slot definida.')
            return redirect('editor_escala_manual', comp_id=comp.id)

        mes, ano = map(int, comp.mes_ano.split('/'))
        num_days = calendar.monthrange(ano, mes)[1]

        # Busca todos os membros elegíveis do departamento
        membros_elegiveis = Membro.objects.filter(
            Q(is_active=True) & (
                Q(departamentos_ativos=comp.departamento) |
                Q(departamentos_liderados=comp.departamento) |
                Q(departamentos_subliderados=comp.departamento)
            )
        ).distinct()

        slots_criados = 0

        # Para cada dia do mês, aplicar as regras de configuração de slots
        for day in range(1, num_days + 1):
            data_atual = date(ano, mes, day)
            dia_semana = data_atual.weekday()

            # Buscar eventos recorrentes e extraordinários para este dia
            eventos_hoje = []

            # 1. Recorrentes
            recorrentes = CultoEvento.objects.filter(tipo='padrao', dia_semana=dia_semana)
            for ev in recorrentes:
                key_ev = ev.chave_slug if ev.chave_slug else str(ev.id)
                eventos_hoje.append((key_ev, ev.horario_inicio.strftime('%H:%M'), ev.horario_fim.strftime('%H:%M')))

            # 2. Extraordinários
            extras = CultoEvento.objects.filter(tipo='extra', data_evento=data_atual)
            for ev in extras:
                key_ev = ev.chave_slug if ev.chave_slug else str(ev.id)
                eventos_hoje.append((key_ev, ev.horario_inicio.strftime('%H:%M'), ev.horario_fim.strftime('%H:%M')))

            for evento, start_time, end_time in eventos_hoje:
                configs_evento = configuracoes.filter(tipo_evento=evento)

                for config in configs_evento:
                    # Se a função não tiver requisitos (habilidades configuradas), ignoramos para não alocar pessoas erradas
                    if not config.funcao.requisitos.exists():
                        continue

                    for _ in range(config.quantidade):
                        # Filtra membros que tem a habilidade exigida
                        membros_funcao = membros_elegiveis.filter(habilidades__in=config.funcao.requisitos.all()).distinct()

                        membros_disponiveis = []
                        for m in membros_funcao:
                            is_indisponivel = Indisponibilidade.objects.filter(
                                membro=m, data_inicio__lte=data_atual, data_fim__gte=data_atual
                            ).exists()

                            count_mes = Escala.objects.filter(
                                membro_escalado=m,
                                data_escala__year=ano,
                                data_escala__month=mes
                            ).count()

                            # Trava Global de Dia Único: Previne burnout impedindo 2 cultos no MESMO DIA, em qualquer departamento
                            ja_escalado_hoje = Escala.objects.filter(
                                membro_escalado=m,
                                data_escala=data_atual
                            ).exists()

                            is_trabalho = is_trabalhando(m, data_atual, start_time, end_time)

                            import datetime
                            ja_escalado_recentemente = Escala.objects.filter(
                                membro_escalado=m,
                                data_escala__gte=data_atual - datetime.timedelta(days=6),
                                data_escala__lt=data_atual
                            ).exists()

                            # Intelligent Load Balancing: Try to avoid if scheduled recently
                            # We can just put them in a secondary list and use them only if primary is empty
                            if not is_indisponivel and count_mes < 4 and not ja_escalado_hoje and not is_trabalho:
                                if not ja_escalado_recentemente:
                                    membros_disponiveis.append(m)

                        # If strict cooldown leaves no one available, relax the cooldown
                        if not membros_disponiveis:
                            for m in membros_funcao:
                                is_indisponivel = Indisponibilidade.objects.filter(
                                    membro=m, data_inicio__lte=data_atual, data_fim__gte=data_atual
                                ).exists()
                                count_mes = Escala.objects.filter(
                                    membro_escalado=m, data_escala__year=ano, data_escala__month=mes
                                ).count()
                                ja_escalado_hoje = Escala.objects.filter(
                                    membro_escalado=m, data_escala=data_atual
                                ).exists()
                                is_trabalho = is_trabalhando(m, data_atual, start_time, end_time)

                                if not is_indisponivel and count_mes < 4 and not ja_escalado_hoje and not is_trabalho:
                                    membros_disponiveis.append(m)

                        if membros_disponiveis:
                            escolhido = random.choice(membros_disponiveis)

                            Escala.objects.create(
                                competencia=comp,
                                membro_escalado=escolhido,
                                departamento_alocado=comp.departamento,
                                funcao_alocada=config.funcao,
                                data_escala=data_atual,
                                horario_inicio=start_time,
                                horario_fim=end_time,
                                tipo_evento=evento,
                                status='rascunho'
                            )
                            slots_criados += 1

        messages.success(request, f'Motor Automático finalizado! {slots_criados} voluntários alocados inteligentemente. Funções sem requisitos não foram preenchidas.')
        return redirect('editor_escala_manual', comp_id=comp.id)

    return redirect('painel_escalas')

from django.views.decorators.http import require_POST
import json

@login_required
@user_passes_test(is_lider)
@require_POST
def alocar_slot_api(request):
    try:
        data = json.loads(request.body)
        comp_id = data.get('comp_id')
        membro_id = data.get('membro_id')
        funcao_id = data.get('funcao_id')
        data_escala = data.get('data_escala')
        tipo_evento = data.get('tipo_evento')

        comp = get_object_or_404(CompetenciaEscala, id=comp_id)
        if comp.departamento not in get_departamentos_permitidos(request.user):
            return JsonResponse({'success': False, 'error': 'Acesso negado'}, status=403)

        membro = get_object_or_404(Membro, id=membro_id)
        funcao = get_object_or_404(Funcao, id=funcao_id)

        is_indisp = Indisponibilidade.objects.filter(membro=membro, data_inicio__lte=data_escala, data_fim__gte=data_escala).exists()
        if is_indisp:
            return JsonResponse({'success': False, 'error': 'Voluntário está indisponível nesta data (Período de ausência).'})

        escalas_mesmo_dia = Escala.objects.filter(membro_escalado=membro, data_escala=data_escala)
        for esc in escalas_mesmo_dia:
            if esc.departamento_alocado != comp.departamento:
                return JsonResponse({'success': False, 'error': f'Conflito de Departamento! O voluntário já está escalado neste dia no departamento: {esc.departamento_alocado.nome}.'})

        if tipo_evento.isdigit():
            evento_obj = CultoEvento.objects.filter(id=int(tipo_evento)).first()
        else:
            evento_obj = CultoEvento.objects.filter(chave_slug=tipo_evento).first()

        if evento_obj:
            start = evento_obj.horario_inicio.strftime('%H:%M')
            end = evento_obj.horario_fim.strftime('%H:%M')
        else:
            start, end = ('19:30', '21:30')

        data_obj = datetime.strptime(data_escala, '%Y-%m-%d')
        if is_trabalhando(membro, data_obj, start, end):
            return JsonResponse({'success': False, 'error': 'Aviso de Expediente: Voluntário trabalha/estuda neste horário.'})

        escala = Escala.objects.create(
            competencia=comp,
            membro_escalado=membro,
            departamento_alocado=comp.departamento,
            funcao_alocada=funcao,
            data_escala=data_escala,
            horario_inicio=start,
            horario_fim=end,
            tipo_evento=tipo_evento,
            status='confirmado'
        )

        if comp.status == 'publicada':
            gerar_pdf_competencia(comp.id)
            if membro.email:
                enviar_email_html(membro.email, f"Atualização de Escala - {comp.departamento.nome}", "escala_atualizada.html", {
                    'nome': membro.first_name,
                    'departamento': comp.departamento.nome,
                    'departamento_logo': '',
                    'link_painel': f"{settings.BASE_URL}/minhas-escalas/"
                })

        return JsonResponse({
            'success': True,
            'escala_id': escala.id,
            'membro_nome': membro.get_full_name(),
            'foto_url': membro.foto_perfil.url if membro.foto_perfil else ''
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@user_passes_test(is_lider)
@require_POST
def remover_slot_api(request):
    try:
        data = json.loads(request.body)
        escala_id = data.get('escala_id')
        escala = get_object_or_404(Escala, id=escala_id)

        if escala.competencia.departamento not in get_departamentos_permitidos(request.user):
            return JsonResponse({'success': False, 'error': 'Acesso negado'}, status=403)

        comp = escala.competencia
        membro = escala.membro_escalado
        departamento_nome = escala.departamento_alocado.nome
        data_escala_str = escala.data_escala.strftime('%d/%m/%Y')
        hora_inicio_str = escala.horario_inicio.strftime('%H:%M')
        hora_fim_str = escala.horario_fim.strftime('%H:%M')
        is_publicada = comp.status == 'publicada'

        escala.delete()

        if is_publicada:
            gerar_pdf_competencia(comp.id)
            if membro.email:
                enviar_email_html(membro.email, f"Cancelamento de Escala - {departamento_nome}", "escala_cancelada.html", {
                    'nome': membro.first_name,
                    'departamento': departamento_nome,
                    'departamento_logo': '',
                    'data': data_escala_str,
                    'horario_inicio': hora_inicio_str,
                    'horario_fim': hora_fim_str,
                    'link_painel': f"{settings.BASE_URL}/minhas-escalas/"
                })

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def is_super_admin_escala(user):
    return user.nivel_hierarquico == 'super_admin'

@login_required
@user_passes_test(is_super_admin_escala)
def gerenciar_cultos(request):
    cultos = CultoEvento.objects.all().order_by('tipo', 'dia_semana', 'data_evento')
    dias_map = {0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira', 3: 'Quinta-feira', 4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo'}
    dias_semana = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo')
    ]
    return render(request, 'escalas/gerenciar_cultos.html', {
        'cultos': cultos,
        'dias_map': dias_map,
        'dias_semana': dias_semana
    })

@login_required
@user_passes_test(is_super_admin_escala)
def criar_culto(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        tipo = request.POST.get('tipo', 'padrao')
        horario_inicio = request.POST.get('horario_inicio')
        horario_fim = request.POST.get('horario_fim')

        try:
            novo = CultoEvento(nome=nome, tipo=tipo, horario_inicio=horario_inicio, horario_fim=horario_fim)
            if tipo == 'padrao':
                dia = request.POST.get('dia_semana')
                if dia != '':
                    novo.dia_semana = int(dia)
            else:
                data_ev = request.POST.get('data_evento')
                if data_ev:
                    novo.data_evento = datetime.strptime(data_ev, '%Y-%m-%d').date()
            novo.save()
            messages.success(request, f'Culto/Evento "{nome}" criado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao criar Culto/Evento: {str(e)}')

    return redirect('gerenciar_cultos')

@login_required
@user_passes_test(is_super_admin_escala)
def editar_culto(request, culto_id):
    culto = get_object_or_404(CultoEvento, id=culto_id)
    if request.method == 'POST':
        culto.nome = request.POST.get('nome')
        culto.horario_inicio = request.POST.get('horario_inicio')
        culto.horario_fim = request.POST.get('horario_fim')
        if culto.tipo == 'padrao':
            dia = request.POST.get('dia_semana')
            if dia != '':
                culto.dia_semana = int(dia)
        else:
            data_ev = request.POST.get('data_evento')
            if data_ev:
                culto.data_evento = datetime.strptime(data_ev, '%Y-%m-%d').date()
        try:
            culto.save()
            messages.success(request, 'Culto/Evento atualizado!')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar: {str(e)}')

    return redirect('gerenciar_cultos')

@login_required
@user_passes_test(is_super_admin_escala)
def excluir_culto(request, culto_id):
    if request.method == 'POST':
        culto = get_object_or_404(CultoEvento, id=culto_id)
        nome = culto.nome
        culto.delete()
        messages.success(request, f'Culto/Evento "{nome}" excluído.')
    return redirect('gerenciar_cultos')


@login_required
def importar_escala_ocr(request):
    if request.method == 'POST':
        arquivo = request.FILES.get('arquivo_escala')
        if not arquivo:
            messages.error(request, 'Você deve selecionar um arquivo PDF, Excel ou CSV.')
            return redirect('painel_escalas')

        try:
            from intranet.services.groq_ai import analisar_planilha_escalas_groq
            dados = analisar_planilha_escalas_groq(arquivo)

            if not dados or not isinstance(dados, dict) or 'escalas' not in dados:
                messages.warning(request, 'O Groq não conseguiu extrair os dados no formato esperado.')
                return redirect('painel_escalas')

            dept_nome = dados.get('departamento', '')
            mes = str(dados.get('mes', '')).strip().lower()
            ano = str(dados.get('ano', '')).strip()

            # Map month name to number
            mes_map = {'janeiro': '01', 'fevereiro': '02', 'março': '03', 'marco': '03',
                       'abril': '04', 'maio': '05', 'junho': '06', 'julho': '07',
                       'agosto': '08', 'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'}

            mes_num = mes_map.get(mes, mes.zfill(2))
            if not ano:
                from django.utils import timezone
                ano = str(timezone.now().year)

            mes_ano_str = f"{mes_num}/{ano}"

            # Find department
            from gestao_membros.models import Departamento
            departamento = Departamento.objects.filter(nome__icontains=dept_nome).first()
            if not departamento:
                # Tentar achar algum que ocupe pelo menos metade das palavras
                departamentos_all = Departamento.objects.all()
                from thefuzz import process
                nomes_deptos = {d.id: d.nome for d in departamentos_all}
                best_match = process.extractOne(dept_nome, nomes_deptos)
                if best_match and best_match[1] >= 65:
                    departamento = Departamento.objects.get(id=best_match[2])
                else:
                    messages.error(request, f'Departamento "{dept_nome}" não encontrado no sistema. Crie o departamento primeiro.')
                    return redirect('painel_escalas')

            from .models import CompetenciaEscala, Escala

            competencia, created = CompetenciaEscala.objects.get_or_create(
                departamento=departamento,
                mes_ano=mes_ano_str,
                defaults={'status': 'rascunho'}
            )

            # Fuzzy match setup for Members
            from core.models import Membro
            membros_dept = Membro.objects.filter(is_active=True)
            # Para aumentar a precisão, priorizamos membros do sistema com o Apelido
            membros_dict = {m.id: f"{m.first_name} {m.last_name} {m.apelido or ''}" for m in membros_dept}

            escalas_lidas = dados.get('escalas', [])
            count_sucesso = 0
            count_fallback = 0

            from datetime import datetime
            from thefuzz import process

            for esc in escalas_lidas:
                data_str = esc.get('dia', '')
                try:
                    # try to parse DD/MM/YYYY
                    data_obj = datetime.strptime(data_str, '%d/%m/%Y').date()
                except ValueError:
                    continue

                turno = esc.get('turno', '').lower()
                horario_inicio = "19:30" if turno == "noite" else "09:00"
                horario_fim = "21:30" if turno == "noite" else "11:30"

                nomes = esc.get('membros_nomes', [])
                if isinstance(nomes, str):
                    nomes = [nomes]

                for nome in nomes:
                    nome = nome.strip()
                    if not nome: continue

                    # Limpar títulos comuns
                    nome_limpo = nome.lower().replace('miss ', '').replace('miss. ', '').replace('pr ', '').replace('pr. ', '').replace('ev ', '').strip()

                    # Fuzzy match
                    membro_escalado = None
                    best_match_id = None

                    if len(nome_limpo) > 2:
                        match = process.extractOne(nome_limpo, membros_dict)
                        if match and match[1] >= 75: # Tolerância alta (ex: Kauãzinho vs Kauã)
                            best_match_id = match[2]
                            membro_escalado = Membro.objects.get(id=best_match_id)

                    # Fuzzy match para Funcao
                    funcao_str = esc.get('funcao', '').strip()
                    funcao_obj = None
                    if funcao_str and funcao_str.lower() != 'geral':
                        from gestao_membros.models import Funcao
                        funcoes_dept = Funcao.objects.filter(departamento=departamento)
                        if funcoes_dept.exists():
                            funcoes_dict = {f.id: f.nome for f in funcoes_dept}
                            match_func = process.extractOne(funcao_str, funcoes_dict)
                            if match_func and match_func[1] >= 65:
                                funcao_obj = Funcao.objects.get(id=match_func[2])

                    if membro_escalado:
                        try:
                            # Previne crash cortando para 200 caracteres caso ainda venha algo enorme
                            obs_text = str(esc.get('observacao', '') or esc.get('funcao', ''))[:199]
                            Escala.objects.create(
                                competencia=competencia,
                                membro_escalado=membro_escalado,
                                departamento_alocado=departamento,
                                funcao_alocada=funcao_obj,
                                data_escala=data_obj,
                                horario_inicio=horario_inicio,
                                horario_fim=horario_fim,
                                tipo_evento=obs_text
                            )
                            count_sucesso += 1
                        except IntegrityError:
                            # Ignora erro de constraint única no BD
                            pass
                    else:
                        count_fallback += 1
                        # Adicionar slot fantasma (se possivel) ou apenas ignorar
                        # Como Escala exige membro_escalado, vamos apenas ignorar e incrementar contador

            msg = f"Escalas extraídas para {departamento.nome} ({mes_ano_str}). Inseridas: {count_sucesso}."
            if count_fallback > 0:
                msg += f" {count_fallback} nomes não foram reconhecidos com precisão (Fuzzy Matching)."
                messages.warning(request, msg)
            else:
                messages.success(request, msg)

        except Exception as e:
            messages.error(request, f'Erro no processamento OCR (Groq): {str(e)}')

    return redirect('painel_escalas')
