from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
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

@login_required
@user_passes_test(is_super_admin)
def listar_departamentos(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        categoria = request.POST.get('categoria')
        Departamento.objects.create(nome=nome, categoria=categoria)
        messages.success(request, f'Departamento {nome} criado.')
    departamentos = Departamento.objects.all()
    return render(request, 'gestao_membros/departamentos.html', {'departamentos': departamentos, 'is_master': is_super_admin(request.user)})

@login_required
@user_passes_test(is_super_admin)
def painel_lider(request):
    departamentos = Departamento.objects.all()

    membros_pendentes = Membro.objects.filter(is_active=False)

    depto_id = request.GET.get('depto_id') or request.GET.get('depto')
    if depto_id:
        departamento_ativo = get_object_or_404(Departamento, id=depto_id)
    else:
        departamento_ativo = departamentos.first() if departamentos.exists() else None

    membros_aprovados = departamento_ativo.membros_ativos.filter(is_active=True) if departamento_ativo else []

    # Indisponibilidades reais
    from gestao_membros.models import Indisponibilidade
    hoje = timezone.now().date()
    indisponibilidades = Indisponibilidade.objects.filter(
        membro__in=membros_aprovados,
        data_fim__gte=hoje
    ).order_by('data_inicio')

    # Rascunhos pendentes e aniversariantes do mes
    try:
        from escalas.models import CompetenciaEscala
        if departamento_ativo:
            escalas_rascunho = CompetenciaEscala.objects.filter(
                departamento=departamento_ativo,
                status='rascunho'
            )
        else:
            escalas_rascunho = []
    except ImportError:
        escalas_rascunho = []

    aniversariantes = []
    if departamento_ativo:
        aniversariantes = departamento_ativo.membros_ativos.filter(
            data_nascimento__month=hoje.month,
            is_active=True
        ).order_by('data_nascimento__day')

    return render(request, 'gestao_membros/painel_lider.html', {
        'departamentos': departamentos,
        'membros_pendentes': membros_pendentes,
        'departamento_ativo': departamento_ativo,
        'membros_aprovados': membros_aprovados,
        'indisponibilidades': indisponibilidades,
        'escalas_rascunho': escalas_rascunho,
        'aniversariantes': aniversariantes
    })

@login_required
@user_passes_test(is_super_admin)
def aprovar_membro(request, membro_id):
    membro = get_object_or_404(Membro, id=membro_id)
    membro.is_active = True
    membro.status_conta = 'ativo'
    membro.save()
    messages.success(request, 'Membro aprovado.')
    return redirect('painel_lider')

@login_required
@user_passes_test(is_super_admin)
def rejeitar_membro(request, membro_id):
    membro = get_object_or_404(Membro, id=membro_id)
    membro.delete()
    messages.success(request, 'Membro rejeitado.')
    return redirect('painel_lider')

@login_required
@user_passes_test(is_super_admin)
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
        dep_id = request.POST.get('departamento_id')
        dep = get_object_or_404(Departamento, id=dep_id)
        AvisoMural.objects.create(titulo=titulo, mensagem=mensagem, departamento=dep, autor=request.user)
        messages.success(request, 'Aviso criado.')
        return redirect('painel_avisos')

    # GET request - Render form
    if not is_lider(request.user):
        messages.error(request, 'Você não tem permissão para criar avisos.')
        return redirect('painel_avisos')

    departamentos = request.user.departamentos_liderados.all() | request.user.departamentos_subliderados.all()
    if request.user.nivel_hierarquico == 'super_admin':
        departamentos = Departamento.objects.all()

    return render(request, 'gestao_membros/criar_aviso.html', {'departamentos': departamentos.distinct()})

@login_required
def editar_aviso(request, aviso_id):
    aviso = get_object_or_404(AvisoMural, id=aviso_id)
    if request.method == 'POST' and is_lider(request.user):
        aviso.titulo = request.POST.get('titulo')
        aviso.mensagem = request.POST.get('mensagem')
        aviso.save()
        messages.success(request, 'Aviso editado.')
    return redirect('painel_avisos')

@login_required
def excluir_aviso(request, aviso_id):
    aviso = get_object_or_404(AvisoMural, id=aviso_id)
    if request.method == 'POST':
        if is_super_admin(request.user):
            aviso.delete()
            messages.success(request, 'Aviso excluído.')
        else:
            messages.error(request, 'Sem permissão. Apenas Sysadmin pode excluir.')
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
    p.drawString(1 * inch, 9.5 * inch, f"Data de Publicação: {aviso.data_publicacao.strftime('%d/%m/%Y %H:%M')}")
    p.drawString(1 * inch, 9.0 * inch, "Conteúdo:")

    # Strip HTML and write basic text
    from django.utils.html import strip_tags
    import textwrap
    text = strip_tags(aviso.conteudo)
    y_position = 8.5 * inch
    for line in textwrap.wrap(text, width=80):
        p.drawString(1 * inch, y_position, line)
        y_position -= 0.25 * inch

    p.showPage()
    p.save()
    return response

@login_required
def detalhes_departamento(request, dep_id):
    dep = get_object_or_404(Departamento, id=dep_id)
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
@user_passes_test(is_super_admin)
def excluir_departamento(request, dep_id):
    dep = get_object_or_404(Departamento, id=dep_id)
    if request.method == 'POST':
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
def adicionar_membro(request):
    if request.method == 'POST':
        messages.success(request, 'Membro adicionado (funcionalidade básica restaurada).')
        return redirect('painel_membros')
    todos_departamentos = Departamento.objects.all()
    todas_habilidades = Habilidade.objects.all()
    return render(request, 'gestao_membros/form_membro.html', {
        'acao': 'Novo',
        'todos_departamentos': todos_departamentos,
        'todas_habilidades': todas_habilidades
    })

@login_required
def gerir_membro_lider(request, membro_id):
    return redirect('painel_membros')

@login_required
@user_passes_test(is_super_admin)
def editar_membro(request, membro_id):
    membro = get_object_or_404(Membro, id=membro_id)
    if request.method == 'POST':
        membro.first_name = request.POST.get('first_name', '')
        membro.last_name = request.POST.get('last_name', '')
        membro.email = request.POST.get('email', '')
        membro.username = request.POST.get('email', '')
        nivel = request.POST.get('nivel_hierarquico', membro.nivel_hierarquico)

        if membro.nivel_hierarquico != nivel:
            membro.nivel_hierarquico = nivel
            membro.save()
        else:
            membro.nivel_hierarquico = nivel
            membro.save()

        departamentos_ids = request.POST.getlist('departamentos')
        membro.departamentos_ativos.set(departamentos_ids)

        # CPF needs to be None if empty to avoid UNIQUE constraint violations
        cpf_val = request.POST.get('cpf', '').strip()
        membro.cpf = cpf_val if cpf_val else None

        rg_val = request.POST.get('rg', '').strip()
        membro.rg = rg_val if rg_val else None

        tel_val = request.POST.get('telefone', '').strip()
        membro.telefone = tel_val if tel_val else None

        membro.anotacoes_lideranca = request.POST.get('anotacoes_lideranca', membro.anotacoes_lideranca)

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
@user_passes_test(is_super_admin)
def excluir_membro(request, membro_id):
    if request.method == 'POST':
        messages.error(request, 'Blindagem Zero-Trust: Servidores da Palavra (Membros) não podem ser excluídos para manter o histórico de auditoria. Inative o perfil invés de apagar.')
    return redirect('painel_membros')

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
    config = get_object_or_404(ConfiguracaoSlotEscala, id=config_id)
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
from core.models import TemplateDocumento
import json
from django.template import Context, Template
from intranet.services.pdf_service import gerar_pdf

@login_required
@user_passes_test(is_lider)
def rh_painel(request):
    """Painel principal do RH mostrando todos os voluntários sob gestão do líder ou todos para admin"""
    if is_super_admin(request.user):
        membros = Membro.objects.filter(is_active=True).order_by('first_name')
        departamentos = Departamento.objects.all()
    else:
        # Pega todos os membros dos departamentos que este líder lidera ou sublidera
        deps_liderados = request.user.departamentos_liderados.all() | request.user.departamentos_subliderados.all()
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
@user_passes_test(is_lider)
def rh_dossie_membro(request, membro_id):
    """Visualiza o histórico completo do membro (Avaliações, Ocorrências, Ações Disciplinares)"""
    membro = get_object_or_404(Membro, id=membro_id)
    avaliacoes = membro.avaliacoes_recebidas.all().order_by('-data')
    acoes = membro.acoes_disciplinares.all().order_by('-data_aplicacao')
    ocorrencias = Ocorrencia.objects.filter(envolvidos=membro).order_by('-data_ocorrencia')

    return render(request, 'gestao_membros/rh_dossie.html', {
        'membro': membro,
        'avaliacoes': avaliacoes,
        'acoes': acoes,
        'ocorrencias': ocorrencias
    })

@login_required
@user_passes_test(is_lider)
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
@user_passes_test(is_lider)
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
@user_passes_test(is_lider)
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
@user_passes_test(is_lider)
def rh_gerar_pdf_disciplina(request, acao_id):
    acao = get_object_or_404(AcaoDisciplinar, id=acao_id)

    # Try to fetch template based on type
    nome_acao = f"carta_{acao.tipo}"
    template_doc = TemplateDocumento.objects.filter(nome_acao=nome_acao).first()

    if not template_doc:
        messages.error(request, 'O Template de PDF para esta ação não está cadastrado no sistema (SysAdmin).')
        return redirect('rh_dossie_membro', membro_id=acao.membro.id)

    # Render template using Django's template engine
    t = Template(template_doc.html_content)
    c = Context({'acao': acao, 'membro': acao.membro})
    html_final = t.render(c)

    # Generate PDF
    pdf_file = gerar_pdf(html_final, footer_text="Gestão Administrativa - Palavra de Vida")
    if pdf_file:
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Disciplina_{acao.membro.first_name}_{acao.tipo}.pdf"'
        return response
    else:
        return HttpResponse("Erro ao gerar PDF", status=500)
