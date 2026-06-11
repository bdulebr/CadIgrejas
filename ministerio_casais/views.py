from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from .models import Casal, HistoricoAconselhamentoCasal, CursoCasal, MatriculaCursoCasal, EventoCasal, PresencaEventoCasal
import os
from django.conf import settings
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import render_to_string

def check_permission(user):
    # Regra Zero-Trust: Apenas Super Admin ou líder do ministério de casais pode ver
    return user.nivel_hierarquico == 'super_admin' or user.departamento_responsavel and 'casal' in user.departamento_responsavel.nome.lower()

@login_required
def dashboard_casais(request):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado. Este módulo contém informações confidenciais.", status=403)

    casais = Casal.objects.all().order_by('-data_cadastro')

    # Termômetro (Crise vs Saudável)
    # Vamos contar quantos aconselhamentos tiveram nivel >= 4 nos ultimos 30 dias
    trinta_dias_atras = timezone.now() - timezone.timedelta(days=30)
    alertas_vermelhos = HistoricoAconselhamentoCasal.objects.filter(nivel_crise__gte=4, data_sessao__gte=trinta_dias_atras).values('casal').distinct().count()

    # Aniversários de Casamento (Bodas) no mês atual
    mes_atual = timezone.now().month
    bodas_mes = Casal.objects.filter(data_aniversario_casamento__month=mes_atual).count()

    # Cursos e Eventos
    total_cursos = CursoCasal.objects.count()
    total_casais = casais.count()

    # Trilha de Noivos ativos
    noivos_na_trilha = Casal.objects.filter(status_relacionamento='Noivos', trilha_noivos_etapa__gt=0).count()

    context = {
        'casais': casais,
        'total_casais': total_casais,
        'alertas_vermelhos': alertas_vermelhos,
        'bodas_mes': bodas_mes,
        'total_cursos': total_cursos,
        'noivos_na_trilha': noivos_na_trilha,
    }
    return render(request, 'ministerio_casais/dashboard.html', context)

@login_required
def perfil_casal(request, casal_id):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)

    casal = get_object_or_404(Casal, id=casal_id)
    historico = casal.historicos_aconselhamento.all().order_by('-data_sessao')
    matriculas = casal.matriculas_cursos.all()

    cursos_disponiveis = CursoCasal.objects.exclude(matriculas__casal=casal)

    context = {
        'casal': casal,
        'historico': historico,
        'matriculas': matriculas,
        'cursos_disponiveis': cursos_disponiveis,
    }
    return render(request, 'ministerio_casais/perfil.html', context)

@login_required
def cadastrar_casal(request):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)

    if request.method == 'POST':
        nome_conjuge_1 = request.POST.get('nome_conjuge_1')
        nome_conjuge_2 = request.POST.get('nome_conjuge_2')
        status_relacionamento = request.POST.get('status_relacionamento')
        data_aniversario_casamento = request.POST.get('data_aniversario_casamento')
        email_1 = request.POST.get('email_1')
        email_2 = request.POST.get('email_2')
        telefone_1 = request.POST.get('telefone_1')
        telefone_2 = request.POST.get('telefone_2')

        casal = Casal(
            nome_conjuge_1=nome_conjuge_1,
            nome_conjuge_2=nome_conjuge_2,
            status_relacionamento=status_relacionamento,
            email_1=email_1,
            email_2=email_2,
            telefone_1=telefone_1,
            telefone_2=telefone_2
        )
        if data_aniversario_casamento:
            casal.data_aniversario_casamento = data_aniversario_casamento

        casal.save()
        messages.success(request, 'Casal cadastrado com sucesso!')
        return redirect('dashboard_casais')

    return redirect('dashboard_casais')

@login_required
def exportar_certificados(request, matricula_id):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)

    matricula = get_object_or_404(MatriculaCursoCasal, id=matricula_id)

    from core.models import ConfiguracaoSistema
    sys_config = ConfiguracaoSistema.objects.first()
    if sys_config and sys_config.igreja_logo:
        logo_path = sys_config.igreja_logo.path
    else:
        logo_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'img', 'logo.jpg')

    html_str = render_to_string('ministerio_casais/pdf_certificado.html', {
        'matricula': matricula,
        'data_geracao': timezone.now(),
        'logo_path': logo_path
    })

    result = BytesIO()
    import xhtml2pdf.pisa as pisa
    pdf = pisa.pisaDocument(BytesIO(html_str.encode("UTF-8")), result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="certificado_{matricula.casal.id}.pdf"'
        return response
    return HttpResponse("Erro ao gerar PDF", status=500)


@login_required
def kanban_casais(request):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)

    # Busca casais por status para o Kanban
    casais_namorados = Casal.objects.filter(status_relacionamento='Namorados').order_by('-data_cadastro')
    casais_noivos = Casal.objects.filter(status_relacionamento='Noivos').order_by('-data_cadastro')
    casais_casados = Casal.objects.filter(status_relacionamento='Casados').order_by('-data_cadastro')
    casais_crise = Casal.objects.filter(status_relacionamento='Em Crise').order_by('-data_cadastro')

    context = {
        'casais_namorados': casais_namorados,
        'casais_noivos': casais_noivos,
        'casais_casados': casais_casados,
        'casais_crise': casais_crise,
    }
    return render(request, 'ministerio_casais/kanban.html', context)

@login_required
def atualizar_status_casal(request, casal_id):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)
    if request.method == 'POST':
        novo_status = request.POST.get('status')
        casal = get_object_or_404(Casal, id=casal_id)
        if novo_status in dict(Casal.STATUS_CHOICES).keys():
            casal.status_relacionamento = novo_status
            casal.save()
            return HttpResponse(status=200)
    return HttpResponse(status=400)

@login_required
def nova_sessao_aconselhamento(request, casal_id):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)
    casal = get_object_or_404(Casal, id=casal_id)
    if request.method == 'POST':
        pastor = request.POST.get('pastor_conselheiro')
        nivel = request.POST.get('nivel_crise')
        obs = request.POST.get('observacoes')

        HistoricoAconselhamentoCasal.objects.create(
            casal=casal,
            pastor_conselheiro=pastor,
            nivel_crise=nivel,
            observacoes=obs
        )
        # Se nivel de crise for alto (4 ou 5), muda o status do casal para 'Em Crise'
        if int(nivel) >= 4 and casal.status_relacionamento != 'Em Crise':
            casal.status_relacionamento = 'Em Crise'
            casal.save()

        messages.success(request, 'Sessão de aconselhamento registrada com sucesso!')
    return redirect('perfil_casal', casal_id=casal.id)

@login_required
def cursos_dashboard(request):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)
    cursos = CursoCasal.objects.all().order_by('-id')
    return render(request, 'ministerio_casais/cursos_dashboard.html', {'cursos': cursos})

@login_required
def adicionar_curso(request):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao')
        valor = request.POST.get('valor_curso', 0.00)
        carga = request.POST.get('carga_horaria', 10)

        CursoCasal.objects.create(
            nome=nome,
            descricao=descricao,
            valor_curso=valor,
            carga_horaria=carga
        )
        messages.success(request, 'Curso adicionado com sucesso!')
    return redirect('cursos_casais')

@login_required
def matricular_casal(request, casal_id):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)
    casal = get_object_or_404(Casal, id=casal_id)
    if request.method == 'POST':
        curso_id = request.POST.get('curso_id')
        status_pagamento = request.POST.get('status_pagamento', 'Pendente')

        curso = get_object_or_404(CursoCasal, id=curso_id)
        MatriculaCursoCasal.objects.create(
            curso=curso,
            casal=casal,
            status_pagamento=status_pagamento
        )
        messages.success(request, f'Casal matriculado em {curso.nome}.')
    return redirect('perfil_casal', casal_id=casal.id)

@login_required
def aprovar_matricula(request, matricula_id):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)
    matricula = get_object_or_404(MatriculaCursoCasal, id=matricula_id)
    matricula.aprovado = True
    matricula.percentual_conclusao = 100
    matricula.save()
    messages.success(request, 'Matrícula aprovada! Certificado já pode ser gerado.')
    return redirect('perfil_casal', casal_id=matricula.casal.id)

@login_required
def editar_casal(request, casal_id):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)
    casal = get_object_or_404(Casal, id=casal_id)
    if request.method == 'POST':
        casal.nome_conjuge_1 = request.POST.get('nome_conjuge_1')
        casal.nome_conjuge_2 = request.POST.get('nome_conjuge_2')
        casal.status_relacionamento = request.POST.get('status_relacionamento')
        bodas = request.POST.get('data_aniversario_casamento')
        if bodas:
            casal.data_aniversario_casamento = bodas
        casal.email_1 = request.POST.get('email_1')
        casal.email_2 = request.POST.get('email_2')
        casal.telefone_1 = request.POST.get('telefone_1')
        casal.telefone_2 = request.POST.get('telefone_2')
        casal.save()
        messages.success(request, 'Casal atualizado com sucesso!')
    return redirect('perfil_casal', casal_id=casal.id)

@login_required
def relatorio_geral_casais(request):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)

    casais = Casal.objects.all().order_by('-data_cadastro')

    from core.models import ConfiguracaoSistema
    sys_config = ConfiguracaoSistema.objects.first()
    if sys_config and sys_config.igreja_logo:
        logo_path = sys_config.igreja_logo.path
    else:
        logo_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'img', 'logo.jpg')

    html_str = render_to_string('ministerio_casais/pdf_relatorio_geral.html', {
        'casais': casais,
        'data_geracao': timezone.now(),
        'logo_path': logo_path
    })

    result = BytesIO()
    import xhtml2pdf.pisa as pisa
    pdf = pisa.pisaDocument(BytesIO(html_str.encode("UTF-8")), result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="relatorio_geral_casais.pdf"'
        return response
    return HttpResponse("Erro ao gerar PDF", status=500)
