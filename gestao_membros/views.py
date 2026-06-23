"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: gestao_membros/views.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from permissoes.decorators import requer_permissao
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail

from .models import Departamento, Habilidade, Funcao, ConfiguracaoSlotEscala, AvisoMural, AvisoAnexo
from core.models import Membro
import csv, openpyxl, datetime

def is_super_admin(user):
    return user.nivel_hierarquico == 'super_admin'

def is_lider(user):
    return user.nivel_hierarquico in ['lider', 'super_admin']

def is_sysadmin_ou_lider_global(user):
    return user.nivel_hierarquico in ['super_admin', 'lider_global']

from intranet.services.gmail_service import enviar_email_html
from intranet.services.whatsapp_service import enviar_whatsapp_template

@login_required
@requer_permissao('membros', 'editar')
def listar_departamentos(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        categoria = request.POST.get('categoria')
        Departamento.objects.create(nome=nome, categoria=categoria)
        messages.success(request, f'Departamento {nome} criado.')
    departamentos = Departamento.objects.all()
    return render(request, 'gestao_membros/departamentos.html', {'departamentos': departamentos, 'is_master': is_super_admin(request.user)})

@login_required
@requer_permissao('membros', 'editar')
def painel_lider(request):
    if is_super_admin(request.user):
        departamentos = Departamento.objects.all()
    else:
        departamentos = request.user.departamentos_liderados.all() | request.user.departamentos_subliderados.all()
        departamentos = departamentos.distinct()

    depto_id = request.GET.get('depto_id') or request.GET.get('depto')
    if depto_id:
        departamento_ativo = get_object_or_404(
            Departamento.objects.prefetch_related(
                'membros_ativos',
                'vagas_abertas__candidaturas',
                'eventos_internos'
            ), id=depto_id)
    else:
        departamento_ativo = departamentos.prefetch_related(
            'membros_ativos',
            'vagas_abertas__candidaturas',
            'eventos_internos'
        ).first() if departamentos.exists() else None

    if departamento_ativo:
        membros_pendentes = departamento_ativo.membros_ativos.filter(status_conta='pendente', is_active=False)
        membros_aprovados = departamento_ativo.membros_ativos.filter(is_active=True)
    else:
        membros_pendentes = []
        membros_aprovados = []

    # Indisponibilidades reais
    from gestao_membros.models import Indisponibilidade, AvisoMural
    hoje = timezone.now().date()
    indisponibilidades = Indisponibilidade.objects.filter(
        membro__in=membros_aprovados,
        data_fim__gte=hoje
    ).order_by('data_inicio')

    # Avisos do departamento ativo
    from django.db.models import Q
    avisos = []
    if departamento_ativo:
        avisos = AvisoMural.objects.filter(
            departamento=departamento_ativo
        ).filter(
            Q(data_expiracao__isnull=True) | Q(data_expiracao__gte=timezone.now())
        ).order_by('-fixado', '-data_postagem')[:5]

    # Rascunhos pendentes e aniversariantes do mes
    try:
        from escalas.models import CompetenciaEscala, Escala, CultoEvento
        if departamento_ativo:
            escalas_rascunho = CompetenciaEscala.objects.filter(
                departamento=departamento_ativo,
                status='rascunho'
            )

            # Próximos cultos (escalas confirmadas do setor)
            proximos_cultos = Escala.objects.filter(
                departamento_alocado=departamento_ativo,
                data_escala__gte=hoje,
                status='confirmado'
            ).order_by('data_escala', 'horario_inicio')[:5]
        else:
            escalas_rascunho = []
            proximos_cultos = []
    except ImportError:
        escalas_rascunho = []
        proximos_cultos = []

    aniversariantes = []
    vagas = []
    ensaios = []
    analytics = {
        'total_membros': 0,
        'taxa_presenca': 100,
        'alertas_faltas': 0
    }

    if departamento_ativo:
        aniversariantes = departamento_ativo.membros_ativos.filter(
            data_nascimento__month=hoje.month,
            is_active=True
        ).order_by('data_nascimento__day')

        # Novas features
        from gestao_membros.models import VagaSetor, EventoInternoSetor
        vagas = departamento_ativo.vagas_abertas.all()
        ensaios = departamento_ativo.eventos_internos.filter(data_inicio__gte=timezone.now()).order_by('data_inicio')[:5]

        # Analytics
        analytics['total_membros'] = membros_aprovados.count()

        # Calcular taxa de presenca das ultimas 30 escalas do departamento
        try:
            from escalas.models import Escala
            ultimas_escalas = Escala.objects.filter(
                departamento_alocado=departamento_ativo,
                data_escala__lt=hoje,
                status__in=['presente', 'falta_justificada', 'substituido', 'confirmado']
            ).order_by('-data_escala')[:100]

            total_avaliado = 0
            presentes = 0
            for e in ultimas_escalas:
                # Se passou do dia e ficou 'confirmado', consideramos falta injustificada na matemática bruta,
                # mas o status que marca presenca é 'presente'
                total_avaliado += 1
                if e.status in ['presente', 'substituido', 'falta_justificada']:
                    presentes += 1

            if total_avaliado > 0:
                analytics['taxa_presenca'] = int((presentes / total_avaliado) * 100)

            from datetime import timedelta
            # Alertas de faltas (quem faltou recentemente)
            faltosos = Escala.objects.filter(
                departamento_alocado=departamento_ativo,
                data_escala__gte=hoje - timedelta(days=30),
                data_escala__lt=hoje,
                status='confirmado' # Significa que não fez check-in
            ).values('membro_escalado').distinct()
            analytics['alertas_faltas'] = faltosos.count()

        except Exception:
            pass

    return render(request, 'gestao_membros/painel_lider.html', {
        'departamentos': departamentos,
        'membros_pendentes': membros_pendentes,
        'departamento_ativo': departamento_ativo,
        'membros_aprovados': membros_aprovados,
        'indisponiveis': indisponibilidades, # The template expects `indisponiveis`
        'escalas_rascunho': escalas_rascunho,
        'proximos_cultos': proximos_cultos, # Passed to the template
        'avisos': avisos, # Passed to the template
        'aniversariantes': aniversariantes,
        'vagas': vagas,
        'ensaios': ensaios,
        'analytics': analytics
    })

import string
import random

@login_required
@requer_permissao('membros', 'editar')
def aprovar_membro(request, membro_id):
    membro = get_object_or_404(Membro, id=membro_id)

    # Gerar senha aleatória de 6 caracteres
    chars = string.ascii_letters + string.digits
    senha_gerada = ''.join(random.choice(chars) for _ in range(6))

    membro.set_password(senha_gerada)
    membro.is_active = True
    membro.status_conta = 'ativo'
    membro.save()

    try:
        from intranet.services.gmail_service import enviar_email_html
        from intranet.services.whatsapp_service import enviar_whatsapp_template
        from django.conf import settings
        context = {
            'nome': membro.first_name,
            'email': membro.email,
            'senha': senha_gerada,
            'link_acesso': settings.BASE_URL + '/'
        }
        enviar_email_html(
            destinatario=membro.email,
            assunto='Bem-vindo ao Sistema - Credenciais de Acesso',
            template_name='gestao_membros/email_boas_vindas.html',
            context=context
        )
        if getattr(membro, 'telefone', None):
            enviar_whatsapp_template(membro.telefone, 'membro_boas_vindas.txt', context)
        messages.success(request, f'Membro aprovado. E-mail com a senha foi enviado para {membro.email}.')
    except Exception as e:
        messages.warning(request, f'Membro aprovado, mas houve um erro ao enviar o e-mail: {e}')

    return redirect('painel_lider')

@login_required
@requer_permissao('membros', 'editar')
def rejeitar_membro(request, membro_id):
    membro = get_object_or_404(Membro, id=membro_id)
    membro.delete()
    messages.success(request, 'Membro rejeitado.')
    return redirect('painel_lider')

@login_required
@requer_permissao('membros', 'editar')
def evoluir_membro(request, membro_id):
    membro = get_object_or_404(Membro, id=membro_id)
    membro.nivel_hierarquico = 'lider'
    membro.save()
    messages.success(request, 'Membro evoluído para Líder.')
    return redirect('painel_lider')


@login_required
def criar_habilidade(request, dep_id):
    dep = get_object_or_404(Departamento, id=dep_id)
    if request.method == 'POST' and is_lider(request.user):
        nome = request.POST.get('nome')
        Habilidade.objects.create(departamento=dep, nome=nome)
        messages.success(request, 'Habilidade criada.')
    return redirect('detalhes_departamento', dep_id=dep.id)

@login_required
def criar_funcao(request, dep_id):
    dep = get_object_or_404(Departamento, id=dep_id)
    if request.method == 'POST' and is_lider(request.user):
        nome = request.POST.get('nome')
        Funcao.objects.create(departamento=dep, nome=nome)
        messages.success(request, 'Função criada.')
    return redirect('detalhes_departamento', dep_id=dep.id)

@login_required
def excluir_funcao(request, funcao_id):
    funcao = get_object_or_404(Funcao, id=funcao_id)
    dep_id = funcao.departamento.id
    if request.method == 'POST':
        if is_super_admin(request.user):
            funcao.delete()
            messages.success(request, 'Função excluída.')
        else:
            return HttpResponseForbidden("Apenas Sysadmin pode excluir.")
    return redirect('detalhes_departamento', dep_id=dep_id)

@login_required
def painel_avisos(request):
    avisos = AvisoMural.objects.all().order_by('-data_postagem')
    return render(request, 'gestao_membros/painel_avisos.html', {'avisos': avisos})

@login_required
def criar_aviso(request):
    if request.method == 'POST' and is_lider(request.user):
        titulo = request.POST.get('titulo')
        mensagem = request.POST.get('mensagem')
        dep_id = request.POST.get('departamento')
        if not dep_id:
            messages.error(request, 'Nenhum departamento selecionado ou você não lidera nenhum setor ainda.')
            return redirect('painel_avisos')

        duracao = request.POST.get('duracao')
        fixado = request.POST.get('fixado') == 'on'
        link_externo = request.POST.get('link_externo')

        dep = get_object_or_404(Departamento, id=dep_id)

        data_expiracao = None
        if duracao:
            from django.utils import timezone
            from datetime import timedelta
            data_expiracao = timezone.now() + timedelta(days=int(duracao))

        aviso = AvisoMural.objects.create(
            titulo=titulo,
            mensagem=mensagem,
            departamento=dep,
            autor=request.user,
            fixado=fixado,
            data_expiracao=data_expiracao,
            link_externo=link_externo if link_externo else None
        )

        anexos = request.FILES.getlist('anexos')
        for f in anexos:
            AvisoAnexo.objects.create(aviso=aviso, arquivo=f)

        messages.success(request, 'Aviso criado com sucesso.')
        return redirect('painel_avisos')

    # GET request - Render form
    if not is_lider(request.user):
        messages.error(request, 'Você não tem permissão para criar avisos.')
        return redirect('painel_avisos')

    departamentos = request.user.departamentos_liderados.all() | request.user.departamentos_subliderados.all()
    if request.user.nivel_hierarquico == 'super_admin':
        departamentos = Departamento.objects.all()

    return render(request, 'gestao_membros/criar_aviso.html', {'departamentos': departamentos.distinct(), 'acao': 'Criar'})

@login_required
def editar_aviso(request, aviso_id):
    aviso = get_object_or_404(AvisoMural, id=aviso_id)
    if request.method == 'POST' and is_lider(request.user):
        aviso.titulo = request.POST.get('titulo')
        aviso.mensagem = request.POST.get('mensagem')

        duracao = request.POST.get('duracao')
        if duracao:
            from django.utils import timezone
            from datetime import timedelta
            aviso.data_expiracao = timezone.now() + timedelta(days=int(duracao))
        else:
            aviso.data_expiracao = None

        aviso.fixado = request.POST.get('fixado') == 'on'
        aviso.link_externo = request.POST.get('link_externo') or None
        aviso.save()

        remover_anexos = request.POST.getlist('remover_anexos')
        if remover_anexos:
            AvisoAnexo.objects.filter(id__in=remover_anexos, aviso=aviso).delete()

        anexos = request.FILES.getlist('anexos')
        for f in anexos:
            AvisoAnexo.objects.create(aviso=aviso, arquivo=f)

        messages.success(request, 'Aviso editado com sucesso.')
        return redirect('painel_avisos')

    departamentos = request.user.departamentos_liderados.all() | request.user.departamentos_subliderados.all()
    if request.user.nivel_hierarquico == 'super_admin':
        departamentos = Departamento.objects.all()

    return render(request, 'gestao_membros/criar_aviso.html', {
        'departamentos': departamentos.distinct(),
        'acao': 'Editar',
        'aviso': aviso
    })

@login_required
def excluir_aviso(request, aviso_id):
    aviso = get_object_or_404(AvisoMural, id=aviso_id)
    if request.method == 'POST':
        if is_super_admin(request.user) or aviso.autor == request.user:
            aviso.delete()
            messages.success(request, 'Aviso excluído.')
        else:
            messages.error(request, 'Sem permissão. Apenas Sysadmin ou o autor podem excluir.')
    return redirect('painel_avisos')

@login_required
def exportar_aviso_pdf(request, aviso_id):
    aviso = get_object_or_404(AvisoMural, id=aviso_id)
    from django.template.loader import render_to_string
    import os

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Aviso_Mural_{aviso.id}.pdf"'

    # Gerador Básico via ReportLab
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch

    p = canvas.Canvas(response, pagesize=A4)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(1 * inch, 10.5 * inch, "INTRANET PV ENSEADA")
    p.setFont("Helvetica", 12)
    p.drawString(1 * inch, 10 * inch, f"Aviso Oficial: {aviso.titulo}")
    p.drawString(1 * inch, 9.5 * inch, f"Data de Publicacao: {aviso.data_postagem.strftime('%d/%m/%Y %H:%M')}")
    p.drawString(1 * inch, 9.0 * inch, "Conteudo:")

    # Strip HTML and write basic text
    from django.utils.html import strip_tags
    import textwrap
    text = strip_tags(aviso.mensagem)
    y_position = 8.5 * inch
    for line in textwrap.wrap(text, width=80):
        p.drawString(1 * inch, y_position, line)
        y_position -= 0.25 * inch

    p.showPage()
    p.save()
    return response

@login_required
def detalhes_departamento(request, dep_id):
    dep = get_object_or_404(
        Departamento.objects.prefetch_related(
            'membros_ativos',
            'lideres',
            'sub_lideres',
            'funcoes',
            'avisos',
            'avisos__autor',
            'configuracao_slots',
            'configuracao_slots__funcao',
            'vagas_abertas',
            'vagas_abertas__candidaturas',
            'vagas_abertas__candidaturas__membro',
            'eventos_internos'
        ),
        id=dep_id
    )
    is_super = is_super_admin(request.user)
    is_lider_master = request.user.departamentos_liderados.filter(id=dep.id).exists()

    if not (is_super or is_lider_master or request.user.departamentos_subliderados.filter(id=dep.id).exists()):
        return HttpResponseForbidden("Acesso Negado.")

    if request.method == 'POST' and request.POST.get('acao') == 'editar' and (is_super or is_lider_master):
        dep.nome = request.POST.get('nome', dep.nome)
        dep.categoria = request.POST.get('categoria', dep.categoria)
        if 'logo' in request.FILES:
            dep.logo = request.FILES['logo']
        dep.save()
        messages.success(request, 'Departamento atualizado.')
        return redirect('detalhes_departamento', dep_id=dep.id)

    from escalas.models import CultoEvento
    tipos_evento = []
    for c in CultoEvento.objects.all().order_by('tipo', 'dia_semana', 'data_evento'):
        key = c.chave_slug if c.chave_slug else str(c.id)
        tipos_evento.append((key, str(c)))

    context = {
        'dep': dep,
        'is_super': is_super,
        'is_lider_master': is_lider_master,
        'membros': dep.membros_ativos.all(),
        'todos_membros': Membro.objects.filter(is_active=True),
        'tipos_evento': tipos_evento,
        'config_slots': dep.configuracao_slots.all().order_by('tipo_evento', 'funcao__nome') if hasattr(dep, 'configuracao_slots') else []
    }
    return render(request, 'gestao_membros/detalhes_departamento.html', context)

@login_required
@requer_permissao('membros', 'editar')
def excluir_departamento(request, dep_id):
    dep = get_object_or_404(Departamento, id=dep_id)
    if request.method == 'POST':
        if dep.is_system:
            messages.error(request, 'Departamentos de sistema essenciais (como Almoxarifado, Escalas e CRM) não podem ser excluídos.')
        else:
            dep.delete()
            messages.success(request, 'Departamento excluído.')
    return redirect('departamentos')

@login_required
def atribuir_lideranca(request, dep_id):
    dep = get_object_or_404(Departamento, id=dep_id)
    is_super = is_super_admin(request.user)
    is_lider_master = request.user.departamentos_liderados.filter(id=dep.id).exists()

    if request.method == 'POST' and (is_super or is_lider_master):
        acao = request.POST.get('acao')
        membro_id = request.POST.get('membro_id')
        if not membro_id:
            messages.error(request, 'Membro não selecionado.')
            return redirect('detalhes_departamento', dep_id=dep.id)

        membro = get_object_or_404(Membro, id=membro_id)

        if acao == 'add_lider':
            dep.lideres.add(membro)
            dep.membros_ativos.add(membro)
            if membro.nivel_hierarquico == 'membro_voluntario':
                membro.nivel_hierarquico = 'lider'
                membro.save()
        elif acao == 'rem_lider':
            dep.lideres.remove(membro)
        elif acao == 'add_sub':
            dep.sub_lideres.add(membro)
            dep.membros_ativos.add(membro)
            if membro.nivel_hierarquico == 'membro_voluntario':
                membro.nivel_hierarquico = 'sub_lider'
                membro.save()
        elif acao == 'rem_sub':
            dep.sub_lideres.remove(membro)
        elif acao == 'add_membro':
            dep.membros_ativos.add(membro)
        elif acao == 'rem_membro':
            dep.membros_ativos.remove(membro)
            dep.lideres.remove(membro)
            dep.sub_lideres.remove(membro)

        messages.success(request, 'Equipe atualizada.')
    return redirect('detalhes_departamento', dep_id=dep.id)

@login_required
def painel_membros(request):
    if is_super_admin(request.user):
        membros = Membro.objects.all()
    else:
        membros = Membro.objects.filter(departamentos_ativos__in=request.user.departamentos_liderados.all()).distinct()
    return render(request, 'gestao_membros/gerenciador_membros.html', {'membros': membros, 'is_master': is_super_admin(request.user)})

@login_required
def exportar_membros_excel(request):
    import csv
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="membros.csv"'

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Nome Completo', 'Email', 'Telefone', 'Nivel Hierarquico', 'Data de Nascimento'])

    membros = Membro.objects.all().order_by('first_name', 'last_name')
    for m in membros:
        writer.writerow([m.get_full_name(), m.email, m.telefone, m.get_nivel_hierarquico_display(), m.data_nascimento.strftime('%d/%m/%Y') if m.data_nascimento else 'N/A'])

    return response

@login_required
def importar_membros_excel(request):
    return redirect('painel_membros')

@login_required
def baixar_modelo_importacao(request):
    return HttpResponse("Função de baixar modelo será implementada em breve.")

@login_required
@requer_permissao('membros', 'editar')
def adicionar_membro(request):
    if request.method == 'POST':
        membro = Membro()
        membro.first_name = request.POST.get('first_name', '')
        membro.last_name = request.POST.get('last_name', '')
        membro.email = request.POST.get('email', '')
        membro.username = request.POST.get('email', '')
        membro.nivel_hierarquico = request.POST.get('nivel_hierarquico', 'membro_voluntario')
        membro.is_active = True

        # Senha padrão
        nova_senha = request.POST.get('nova_senha', '123456789')
        if not nova_senha: nova_senha = '123456789'
        membro.set_password(nova_senha)

        # Trata campos sensíveis
        cpf_val = request.POST.get('cpf', '').strip()
        membro.cpf = cpf_val if cpf_val else None

        rg_val = request.POST.get('rg', '').strip()
        membro.rg = rg_val if rg_val else None

        tel_val = request.POST.get('telefone', '').strip()
        membro.telefone = tel_val if tel_val else None



        data_nascimento = request.POST.get('data_nascimento')
        membro.data_nascimento = data_nascimento if data_nascimento else None

        data_casamento = request.POST.get('data_casamento')
        membro.data_casamento = data_casamento if data_casamento else None

        membro.horario_trabalho_inicio = request.POST.get('horario_trabalho_inicio') or None
        membro.horario_trabalho_fim = request.POST.get('horario_trabalho_fim') or None

        dias_trabalho_lista = request.POST.getlist('dias_trabalho')
        membro.dias_trabalho = ",".join(dias_trabalho_lista)
        membro.dias_folga = request.POST.get('dias_folga', '')

        foto_perfil = request.FILES.get('foto_perfil')
        if foto_perfil: membro.foto_perfil = foto_perfil

        conjuge_id = request.POST.get('conjuge_id')
        if conjuge_id:
            membro.conjuge_id = conjuge_id
        else:
            membro.conjuge = None

        membro.filhos = request.POST.get('filhos', '')

        # Salva o membro primeiro para poder adicionar relações ManyToMany
        membro.save()

        departamentos_ids = request.POST.getlist('departamentos')
        membro.departamentos_ativos.set(departamentos_ids)

        habilidades_ids = request.POST.getlist('habilidades')
        membro.habilidades.set(habilidades_ids)

        messages.success(request, 'Novo membro cadastrado com sucesso!')
        return redirect('painel_membros')

    dias_semana = [(str(i), nome) for i, nome in enumerate(['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'])]
    todos_departamentos = Departamento.objects.all()
    todas_habilidades = Habilidade.objects.all()

    return render(request, 'gestao_membros/form_membro.html', {
        'acao': 'Novo',
        'todos_departamentos': todos_departamentos,
        'todas_habilidades': todas_habilidades,
        'dias_semana': dias_semana,
        'dias_trabalho_list': [],
        'habilidades_membro': [],
        'departamentos_membro': []
    })

@login_required
def gerir_membro_lider(request, membro_id):
    return redirect('rh_dossie_membro', membro_id=membro_id)

@login_required
@requer_permissao('membros', 'editar')
def editar_membro(request, membro_id):
    membro = get_object_or_404(Membro, id=membro_id)
    if request.method == 'POST':
        membro.first_name = request.POST.get('first_name', '')
        membro.last_name = request.POST.get('last_name', '')
        membro.apelido = request.POST.get('apelido', '')
        membro.email = request.POST.get('email', '')
        membro.username = request.POST.get('email', '')

        nivel = request.POST.get('nivel_hierarquico', membro.nivel_hierarquico)
        membro.nivel_hierarquico = nivel

        status = request.POST.get('status_conta')
        if status:
            membro.status_conta = status

        departamentos_ids = request.POST.getlist('departamentos')
        if membro.status_conta == 'ativo':
            membro.departamentos_ativos.set(departamentos_ids)
        else:
            membro.departamentos_ativos.clear()
            membro.departamentos_liderados.clear()
            membro.departamentos_subliderados.clear()

        # CPF needs to be None if empty to avoid UNIQUE constraint violations
        cpf_val = request.POST.get('cpf', '').strip()
        membro.cpf = cpf_val if cpf_val else None

        rg_val = request.POST.get('rg', '').strip()
        membro.rg = rg_val if rg_val else None

        tel_val = request.POST.get('telefone', '').strip()
        membro.telefone = tel_val if tel_val else None


        data_nascimento = request.POST.get('data_nascimento')
        membro.data_nascimento = data_nascimento if data_nascimento else None

        data_casamento = request.POST.get('data_casamento')
        membro.data_casamento = data_casamento if data_casamento else None

        membro.horario_trabalho_inicio = request.POST.get('horario_trabalho_inicio') or None
        membro.horario_trabalho_fim = request.POST.get('horario_trabalho_fim') or None

        dias_trabalho_lista = request.POST.getlist('dias_trabalho')
        membro.dias_trabalho = ",".join(dias_trabalho_lista)
        membro.dias_folga = request.POST.get('dias_folga', '')

        foto_perfil = request.FILES.get('foto_perfil')
        if foto_perfil: membro.foto_perfil = foto_perfil

        conjuge_id = request.POST.get('conjuge_id')
        if conjuge_id:
            membro.conjuge_id = conjuge_id
        else:
            membro.conjuge = None

        membro.filhos = request.POST.get('filhos', '')

        habilidades_ids = request.POST.getlist('habilidades')
        membro.habilidades.set(habilidades_ids)

        if 'foto_perfil' in request.FILES:
            membro.foto_perfil = request.FILES['foto_perfil']

        nova_senha = request.POST.get('nova_senha')
        if nova_senha:
            membro.set_password(nova_senha)

        membro.save()

        messages.success(request, 'Membro atualizado!')
        return redirect('painel_membros')

    dias_semana = [(str(i), nome) for i, nome in enumerate(['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'])]
    dias_trabalho_list = membro.dias_trabalho.split(',') if membro.dias_trabalho else []
    todos_departamentos = Departamento.objects.all()
    todas_habilidades = Habilidade.objects.all()

    return render(request, 'gestao_membros/form_membro.html', {
        'acao': 'Editar',
        'membro': membro,
        'todos_departamentos': todos_departamentos,
        'todas_habilidades': todas_habilidades,
        'dias_semana': dias_semana,
        'dias_trabalho_list': dias_trabalho_list,
        'habilidades_membro': membro.habilidades.all(),
        'departamentos_membro': membro.departamentos_ativos.all()
    })

@login_required
@requer_permissao('membros', 'editar')
def excluir_membro(request, membro_id):
    if request.method == 'POST':
        if not request.user.is_superuser:
            messages.error(request, 'Blindagem Zero-Trust: Apenas o Super Administrador do sistema pode excluir um membro definitivamente. Inative o perfil invés de apagar.')
            return redirect('painel_membros')

        membro = get_object_or_404(Membro, id=membro_id)
        nome = membro.get_full_name() or membro.username
        membro.delete()
        messages.success(request, f'Membro {nome} foi EXCLUÍDO definitivamente do sistema.')
    return redirect('painel_membros')

@login_required
def salvar_instrucoes_escala(request, dep_id):
    dep = get_object_or_404(Departamento, id=dep_id)
    if not (is_sysadmin_ou_lider_global(request.user) or request.user.departamentos_liderados.filter(id=dep.id).exists()):
        return HttpResponseForbidden("Sem permissão.")

    if request.method == 'POST':
        texto = request.POST.get('instrucoes_padrao_escala', '').strip()
        dep.instrucoes_padrao_escala = texto
        dep.save()
        messages.success(request, f'Instruções de escala salvas com sucesso para o departamento {dep.nome}.')

    return redirect('detalhes_departamento', dep_id=dep_id)

@login_required
def salvar_configuracao_slot(request, dep_id):
    dep = get_object_or_404(Departamento, id=dep_id)
    if not (is_sysadmin_ou_lider_global(request.user) or request.user.departamentos_liderados.filter(id=dep.id).exists()):
        return HttpResponseForbidden("Sem permissão.")

    if request.method == 'POST':
        tipos_eventos = request.POST.getlist('tipo_evento')
        funcao_id = request.POST.get('funcao_id')
        quantidade = request.POST.get('quantidade')

        funcao = get_object_or_404(Funcao, id=funcao_id)

        try:
            for tipo_evento in tipos_eventos:
                ConfiguracaoSlotEscala.objects.update_or_create(
                    departamento=dep,
                    tipo_evento=tipo_evento,
                    funcao=funcao,
                    defaults={'quantidade': quantidade}
                )
            messages.success(request, 'Slot(s) configurado(s) com sucesso.')
        except Exception as e:
            messages.error(request, f'Erro ao salvar configuração: {str(e)}')

    return redirect('detalhes_departamento', dep_id=dep.id)

@login_required
def remover_configuracao_slot(request, config_id):
    from django.contrib import messages
    from django.shortcuts import redirect

    try:
        config = ConfiguracaoSlotEscala.objects.get(id=config_id)
    except ConfiguracaoSlotEscala.DoesNotExist:
        messages.error(request, f'A configuração de slot com ID {config_id} não foi encontrada ou já foi removida.')
        return redirect('painel_lider')
    dep_id = config.departamento.id

    if not is_super_admin(request.user):
        return HttpResponseForbidden("Apenas administradores de sistema podem excluir slots.")

    if request.method == 'POST':
        config.delete()
        messages.success(request, 'Configuração de slot removida.')

    return redirect('detalhes_departamento', dep_id=dep_id)

# ==============================================================================
# MÓDULO DE RECURSOS HUMANOS (RH LIDERANÇA)
# ==============================================================================
from .models import AvaliacaoMembro, Ocorrencia, AcaoDisciplinar
import json
from django.template import Context, Template
from intranet.services.pdf_service import gerar_pdf

@login_required
def rh_painel(request):
    """Painel principal do RH mostrando todos os voluntários sob gestão do líder ou todos para admin"""
    from permissoes.utils import obter_escopo_acesso
    from django.core.exceptions import PermissionDenied

    escopo_rh = obter_escopo_acesso(request.user, 'rh')

    if is_super_admin(request.user) or escopo_rh == 'global':
        membros = Membro.objects.filter(is_active=True).order_by('first_name')
        departamentos = Departamento.objects.all()
    else:
        # Pega todos os membros dos departamentos que este líder lidera ou sublidera
        deps_liderados = request.user.departamentos_liderados.all() | request.user.departamentos_subliderados.all()

        if not deps_liderados.exists() and escopo_rh == 'nenhum':
            raise PermissionDenied("Você não tem autorização para acessar o painel de Recursos Humanos.")

        departamentos = deps_liderados.distinct()
        membros = Membro.objects.filter(departamentos_ativos__in=departamentos, is_active=True).distinct().order_by('first_name')

    query = request.GET.get('q', '').strip()
    if query:
        from django.db.models import Q
        membros = membros.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query) |
            Q(email__icontains=query)
        )

    return render(request, 'gestao_membros/rh_painel.html', {
        'membros': membros,
        'departamentos': departamentos,
        'query': query
    })

@login_required
def rh_dossie_membro(request, membro_id):
    """Visualiza o histórico completo do membro (Avaliações, Ocorrências, Ações Disciplinares, Anotações RH)"""
    membro = get_object_or_404(Membro, id=membro_id)

    from permissoes.utils import obter_escopo_acesso
    from django.core.exceptions import PermissionDenied

    escopo_rh = obter_escopo_acesso(request.user, 'rh')

    # Validação de Segurança Zero-Trust
    if not is_super_admin(request.user) and escopo_rh != 'global':
        deps_membro = membro.departamentos_ativos.all()
        deps_liderados = request.user.departamentos_liderados.all() | request.user.departamentos_subliderados.all()

        # O usuário logado lidera algum departamento onde o membro serve?
        is_lider_direto = any(d in deps_liderados for d in deps_membro)

        if not is_lider_direto and escopo_rh == 'nenhum':
            raise PermissionDenied("Você não tem autorização para ver o Dossiê RH deste membro.")

    if request.method == 'POST':
        nova_anotacao = request.POST.get('nova_anotacao')
        if nova_anotacao:
            from gestao_membros.models import AnotacaoRH
            AnotacaoRH.objects.create(
                membro=membro,
                autor=request.user,
                anotacao=nova_anotacao
            )
            messages.success(request, 'Anotação adicionada ao dossiê com sucesso.')
            return redirect('rh_dossie_membro', membro_id=membro.id)

    avaliacoes = membro.avaliacoes_recebidas.all().order_by('-data')
    acoes = membro.acoes_disciplinares.all().order_by('-data_aplicacao')
    ocorrencias = Ocorrencia.objects.filter(envolvidos=membro).order_by('-data_ocorrencia')

    from gestao_membros.models import AnotacaoRH
    anotacoes = AnotacaoRH.objects.filter(membro=membro)

    return render(request, 'gestao_membros/rh_dossie.html', {
        'membro': membro,
        'avaliacoes': avaliacoes,
        'acoes': acoes,
        'ocorrencias': ocorrencias,
        'anotacoes': anotacoes
    })

@login_required
@requer_permissao('membros', 'editar')
def rh_avaliar_membro(request, membro_id):
    membro = get_object_or_404(Membro, id=membro_id)
    if request.method == 'POST':
        nota = request.POST.get('nota')
        comentarios = request.POST.get('comentarios')
        AvaliacaoMembro.objects.create(
            membro=membro,
            avaliador=request.user,
            nota=nota,
            comentarios=comentarios
        )
        messages.success(request, 'Avaliação registrada com sucesso.')
        return redirect('rh_dossie_membro', membro_id=membro.id)
    return redirect('rh_painel')

@login_required
@requer_permissao('membros', 'editar')
def rh_nova_ocorrencia(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        data_ocorrencia = request.POST.get('data_ocorrencia')
        envolvidos_ids = request.POST.getlist('envolvidos')
        anexo = request.FILES.get('anexo')

        ocorrencia = Ocorrencia.objects.create(
            titulo=titulo,
            descricao=descricao,
            data_ocorrencia=data_ocorrencia,
            autor=request.user,
            anexo=anexo
        )

        if envolvidos_ids:
            envolvidos = Membro.objects.filter(id__in=envolvidos_ids)
            ocorrencia.envolvidos.set(envolvidos)

        messages.success(request, 'Ocorrência registrada no Livro com sucesso.')

    membros_disponiveis = Membro.objects.filter(is_active=True).order_by('first_name')
    return render(request, 'gestao_membros/rh_nova_ocorrencia.html', {'membros': membros_disponiveis})

@login_required
@requer_permissao('membros', 'editar')
def rh_aplicar_disciplina(request, membro_id):
    membro = get_object_or_404(Membro, id=membro_id)
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        motivo = request.POST.get('motivo')
        data_fim_suspensao = request.POST.get('data_fim_suspensao') or None
        enviar_email = request.POST.get('enviar_email') == 'on'

        acao = AcaoDisciplinar.objects.create(
            membro=membro,
            tipo=tipo,
            motivo=motivo,
            data_fim_suspensao=data_fim_suspensao,
            autor=request.user,
            enviado_email=enviar_email
        )

        # Lógica Automática para Expulsão
        if tipo == 'expulsao':
            # Remove o membro de todos os departamentos
            for dep in membro.departamentos_ativos.all():
                dep.membros_ativos.remove(membro)
            for dep in membro.departamentos_liderados.all():
                dep.lideres.remove(membro)
            for dep in membro.departamentos_subliderados.all():
                dep.sub_lideres.remove(membro)

            # Bloqueia a conta do membro na Intranet
            membro.status_conta = 'bloqueado'
            membro.save()
            messages.warning(request, f'O membro {membro.first_name} foi desconectado de todos os departamentos e teve a conta bloqueada.')

        messages.success(request, f'Ação Disciplinar ({acao.get_tipo_display()}) aplicada com sucesso.')
        return redirect('rh_dossie_membro', membro_id=membro.id)

    return render(request, 'gestao_membros/rh_aplicar_disciplina.html', {'membro': membro})

@login_required
@requer_permissao('membros', 'editar')
def rh_gerar_pdf_disciplina(request, acao_id):
    acao = get_object_or_404(AcaoDisciplinar, id=acao_id)

    # Try to fetch template based on type
    nome_acao = f"carta_{acao.tipo}"
    template_doc = None

    if not template_doc:
        messages.error(request, 'O Template de PDF para esta ação não está cadastrado no sistema (SysAdmin).')
        return redirect('rh_dossie_membro', membro_id=acao.membro.id)

    # Render template using Django's template engine
    t = Template(template_doc.html_canva)
    c = Context({'acao': acao, 'membro': acao.membro})
    html_final = t.render(c)

    # Generate PDF
    pdf_file = gerar_pdf(html_final, footer_text="Gestão Administrativa - Palavra de Vida")
    if pdf_file:
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Disciplina_{acao.membro.first_name}_{acao.tipo}.pdf"'
        return response

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from intranet.services.gemini_ai import extrair_dados_membro_texto

@login_required
@csrf_exempt
def api_autofill_membro(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            texto = body.get('texto', '')
            if not texto:
                return JsonResponse({'error': 'Texto vazio'}, status=400)

            dados = extrair_dados_membro_texto(texto)
            return JsonResponse(dados)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Apenas POST'}, status=405)


# --- RECRUTAMENTO (Vagas) ---

@login_required
def criar_vaga_setor(request, dep_id):
    dep = get_object_or_404(Departamento, id=dep_id)
    is_super = is_super_admin(request.user)
    is_lider_master = request.user.departamentos_liderados.filter(id=dep.id).exists()

    if not (is_super or is_lider_master):
        return HttpResponseForbidden("Apenas líderes podem abrir vagas.")

    if request.method == 'POST':
        from .models import VagaSetor
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        quantidade = int(request.POST.get('quantidade', 1))

        VagaSetor.objects.create(
            departamento=dep,
            titulo=titulo,
            descricao=descricao,
            quantidade=quantidade
        )
        messages.success(request, f'Vaga "{titulo}" aberta com sucesso para o departamento!')
        return redirect('detalhes_departamento', dep_id=dep.id)
    return redirect('detalhes_departamento', dep_id=dep.id)

@login_required
def excluir_vaga_setor(request, vaga_id):
    from .models import VagaSetor
    vaga = get_object_or_404(VagaSetor, id=vaga_id)
    is_super = is_super_admin(request.user)
    is_lider_master = request.user.departamentos_liderados.filter(id=vaga.departamento.id).exists()

    if not (is_super or is_lider_master):
        return HttpResponseForbidden("Apenas líderes podem excluir vagas.")

    dep_id = vaga.departamento.id
    vaga.delete()
    messages.success(request, 'Vaga excluída.')
    return redirect('detalhes_departamento', dep_id=dep_id)

@login_required
def painel_vagas_publico(request):
    from .models import VagaSetor
    vagas_abertas = VagaSetor.objects.filter(ativa=True).order_by('-data_criacao')
    minhas_candidaturas = request.user.minhas_candidaturas.all() if not request.user.is_anonymous else []

    return render(request, 'gestao_membros/painel_vagas.html', {
        'vagas': vagas_abertas,
        'minhas_candidaturas': minhas_candidaturas
    })

@login_required
def candidatar_vaga(request, vaga_id):
    from .models import VagaSetor, CandidaturaVaga
    vaga = get_object_or_404(VagaSetor, id=vaga_id, ativa=True)

    if CandidaturaVaga.objects.filter(vaga=vaga, membro=request.user).exists():
        messages.warning(request, 'Você já se candidatou para esta vaga.')
        return redirect('painel_vagas_publico')

    if request.method == 'POST':
        mensagem = request.POST.get('mensagem', '')
        CandidaturaVaga.objects.create(
            vaga=vaga,
            membro=request.user,
            mensagem=mensagem
        )
        messages.success(request, 'Candidatura enviada ao líder do setor! Aguarde a avaliação.')
        return redirect('painel_vagas_publico')

    return redirect('painel_vagas_publico')

@login_required
def avaliar_candidatura(request, candidatura_id, acao):
    from .models import CandidaturaVaga
    from django.utils import timezone
    candidatura = get_object_or_404(CandidaturaVaga, id=candidatura_id)
    dep = candidatura.vaga.departamento
    is_super = is_super_admin(request.user)
    is_lider_master = request.user.departamentos_liderados.filter(id=dep.id).exists()

    if not (is_super or is_lider_master):
        return HttpResponseForbidden("Apenas líderes podem avaliar candidaturas.")

    if acao == 'aprovar':
        candidatura.status = 'aprovado'
        candidatura.data_resposta = timezone.now()
        candidatura.save()
        # Adiciona o membro ao departamento
        dep.membros_ativos.add(candidatura.membro)
        messages.success(request, f'{candidatura.membro.first_name} foi aprovado e adicionado ao departamento!')
    elif acao == 'rejeitar':
        candidatura.status = 'rejeitado'
        candidatura.data_resposta = timezone.now()
        candidatura.save()
        messages.warning(request, f'Candidatura de {candidatura.membro.first_name} foi rejeitada.')

    return redirect('detalhes_departamento', dep_id=dep.id)

# --- AGENDA DO SETOR (Eventos Internos) ---

@login_required
def criar_evento_setor(request, dep_id):
    dep = get_object_or_404(Departamento, id=dep_id)
    is_super = is_super_admin(request.user)
    is_lider_master = request.user.departamentos_liderados.filter(id=dep.id).exists()

    if not (is_super or is_lider_master):
        return HttpResponseForbidden("Apenas líderes podem criar eventos.")

    if request.method == 'POST':
        from .models import EventoInternoSetor
        from datetime import datetime
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao', '')
        local = request.POST.get('local', '')
        data_inicio_str = request.POST.get('data_inicio')
        data_fim_str = request.POST.get('data_fim')

        try:
            data_inicio = datetime.fromisoformat(data_inicio_str)
            data_fim = datetime.fromisoformat(data_fim_str) if data_fim_str else None

            EventoInternoSetor.objects.create(
                departamento=dep,
                titulo=titulo,
                descricao=descricao,
                local=local,
                data_inicio=data_inicio,
                data_fim=data_fim
            )
            messages.success(request, 'Evento interno criado para a equipe!')
        except ValueError:
            messages.error(request, 'Formato de data inválido.')

    return redirect('detalhes_departamento', dep_id=dep.id)

@login_required
def excluir_evento_setor(request, evento_id):
    from .models import EventoInternoSetor
    evento = get_object_or_404(EventoInternoSetor, id=evento_id)
    is_super = is_super_admin(request.user)
    is_lider_master = request.user.departamentos_liderados.filter(id=evento.departamento.id).exists()

    if not (is_super or is_lider_master):
        return HttpResponseForbidden("Acesso negado.")

    dep_id = evento.departamento.id
    evento.delete()
    messages.success(request, 'Evento interno excluído.')
    return redirect('detalhes_departamento', dep_id=dep_id)
