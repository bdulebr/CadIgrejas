from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from .models import Casal, HistoricoAconselhamentoCasal, CursoCasal, MatriculaCursoCasal, EventoCasal, PresencaEventoCasal, TurmaCurso
import os
from django.conf import settings
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import render_to_string

def check_permission(user):
    is_global = user.nivel_hierarquico in ['super_admin', 'pastor_regente', 'pastor'] or user.is_superuser
    if is_global: return True
    try:
        depts_str = " ".join(user.departamentos_liderados.values_list('nome', flat=True)).lower()
        return 'casal' in depts_str or 'família' in depts_str
    except Exception:
        return False

@login_required
def dashboard_casais(request):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado. Este módulo contém informações confidenciais.", status=403)

    casais = Casal.objects.filter(arquivado=False).order_by('-data_cadastro')
    total_casais = casais.count()

    trinta_dias_atras = timezone.now() - timezone.timedelta(days=30)
    alertas_vermelhos = HistoricoAconselhamentoCasal.objects.filter(nivel_crise__gte=4, data_sessao__gte=trinta_dias_atras, casal__arquivado=False).values('casal').distinct().count()

    mes_atual = timezone.now().month
    bodas_mes = casais.filter(data_aniversario_casamento__month=mes_atual).count()

    total_cursos = CursoCasal.objects.count()
    noivos_na_trilha = casais.filter(status_relacionamento='Noivos', trilha_noivos_etapa__gt=0).count()

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
def matricular_casal(request, casal_id):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)
    casal = get_object_or_404(Casal, id=casal_id)
    if request.method == 'POST':
        turma_id = request.POST.get('turma_id')
        status_pagamento = request.POST.get('status_pagamento', 'Pendente')

        turma = get_object_or_404(TurmaCurso, id=turma_id)
        MatriculaCursoCasal.objects.create(
            turma=turma,
            casal=casal,
            status_pagamento=status_pagamento
        )

        # Disparar Email de Matrícula em Background
        import threading
        from intranet.services.gmail_service import enviar_email_html
        emails_destino = []
        if casal.email_1: emails_destino.append(casal.email_1)
        if casal.email_2: emails_destino.append(casal.email_2)

        if emails_destino:
            assunto = f"Você foi matriculado no curso: {turma.curso.nome}!"
            contexto_email = {'casal': casal, 'curso': turma.curso}

            def enviar_background(emails, ass, ctx):
                for e in emails:
                    try:
                        enviar_email_html(e, ass, 'ministerio_casais/email_matricula_curso.html', ctx)
                    except Exception as err:
                        print(f"Erro ao enviar email matricula: {err}")

            threading.Thread(target=enviar_background, args=(emails_destino, assunto, contexto_email)).start()

        from core.models import LogAuditoria
        LogAuditoria.objects.create(
            usuario_acao=request.user,
            acao_realizada="MATRICULAR_CURSO",
            tabela_afetada="MatriculaCursoCasal",
            diferenca_json={"registro_afetado_id": casal.id, "turma": turma.nome_turma, "curso": turma.curso.nome, "status_pagamento": status_pagamento}
        )

        messages.success(request, f'Casal matriculado na {turma.nome_turma} do curso {turma.curso.nome}. E-mail de notificação enviado!')
    return redirect('perfil_casal', casal_id=casal.id)

@login_required
def perfil_casal(request, casal_id):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)

    casal = get_object_or_404(Casal, id=casal_id)
    historico = casal.historicos_aconselhamento.all().order_by('-data_sessao')
    matriculas = casal.matriculas_cursos.all()

    turmas_disponiveis = TurmaCurso.objects.exclude(matriculas__casal=casal).filter(status='Aberta').select_related('curso')

    context = {
        'casal': casal,
        'historico': historico,
        'matriculas': matriculas,
        'turmas_disponiveis': turmas_disponiveis,
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

        if request.FILES.get('foto_casal'):
            casal.foto_casal = request.FILES.get('foto_casal')
        if request.FILES.get('foto_conjuge_1'):
            casal.foto_conjuge_1 = request.FILES.get('foto_conjuge_1')
        if request.FILES.get('foto_conjuge_2'):
            casal.foto_conjuge_2 = request.FILES.get('foto_conjuge_2')

        if data_aniversario_casamento:
            casal.data_aniversario_casamento = data_aniversario_casamento

        casal.save()
        messages.success(request, 'Casal cadastrado com sucesso!')
        return redirect('dashboard_casais')

    return redirect('dashboard_casais')

@login_required
def exportar_relatorio_individual_casais(request, casal_id):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)

    casal = get_object_or_404(Casal, id=casal_id)
    historico = casal.historicos_aconselhamento.all().order_by('-data_sessao')
    matriculas = casal.matriculas_cursos.all().order_by('-data_matricula')

    from core.models import ConfiguracaoSistema
    sys_config = ConfiguracaoSistema.objects.first()
    if sys_config and sys_config.igreja_logo:
        logo_path = sys_config.igreja_logo.path
    else:
        logo_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'img', 'logo.jpg')

    html_str = render_to_string('ministerio_casais/pdf_relatorio_individual.html', {
        'casal': casal,
        'historico': historico,
        'matriculas': matriculas,
        'data_geracao': timezone.now(),
        'logo_path': logo_path
    })

    result = BytesIO()
    import xhtml2pdf.pisa as pisa
    pdf = pisa.pisaDocument(BytesIO(html_str.encode("UTF-8")), result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="dossie_casal_{casal.id}.pdf"'
        return response
    return HttpResponse("Erro ao gerar PDF", status=500)

@login_required
def upload_certificado(request, matricula_id):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)

    matricula = get_object_or_404(MatriculaCursoCasal, id=matricula_id)
    if request.method == 'POST' and request.FILES.get('certificado_arquivo'):
        matricula.certificado_arquivo = request.FILES.get('certificado_arquivo')
        matricula.aprovado = True
        matricula.percentual_conclusao = 100
        matricula.save()
        messages.success(request, 'Certificado anexado com sucesso!')
    return redirect('perfil_casal', casal_id=matricula.casal.id)


@login_required
def painel_pastoral_casais(request):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)

    # Busca casais por status para o Kanban (ignorando arquivados)
    casais_namorados = Casal.objects.filter(status_relacionamento='Namorados', arquivado=False).order_by('-data_cadastro')
    casais_noivos = Casal.objects.filter(status_relacionamento='Noivos', arquivado=False).order_by('-data_cadastro')
    casais_casados = Casal.objects.filter(status_relacionamento='Casados', arquivado=False).order_by('-data_cadastro')
    casais_crise = Casal.objects.filter(status_relacionamento='Em Crise', arquivado=False).order_by('-data_cadastro')

    context = {
        'casais_namorados': casais_namorados,
        'casais_noivos': casais_noivos,
        'casais_casados': casais_casados,
        'casais_crise': casais_crise,
    }
    return render(request, 'ministerio_casais/painel.html', context)

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
        data_sessao = request.POST.get('data_sessao')
        atendimento_para = request.POST.get('atendimento_para', 'Casal')

        historico = HistoricoAconselhamentoCasal.objects.create(
            casal=casal,
            pastor_conselheiro=pastor,
            nivel_crise=nivel,
            observacoes=obs,
            atendimento_para=atendimento_para
        )

        if data_sessao:
            historico.data_sessao = data_sessao
            historico.save()
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
        data_inicio = request.POST.get('data_inicio')
        dias_semana_list = request.POST.getlist('dias_semana')
        dias_semana_str = ", ".join(dias_semana_list) if dias_semana_list else ""

        curso = CursoCasal(
            nome=nome,
            descricao=descricao,
            valor_curso=valor,
            carga_horaria=carga,
            dias_semana=dias_semana_str,
            emite_certificado=request.POST.get('emite_certificado') == 'on',
            compra_camiseta=request.POST.get('compra_camiseta') == 'on'
        )
        if data_inicio:
            curso.data_inicio = data_inicio
        curso.save()
        messages.success(request, 'Curso adicionado com sucesso!')
    return redirect('cursos_casais')



@login_required
def aprovar_matricula(request, matricula_id):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)
    matricula = get_object_or_404(MatriculaCursoCasal, id=matricula_id)
    matricula.aprovado = True
    matricula.percentual_conclusao = 100
    matricula.save()

    # Disparar Email de Conclusão e Certificado em Background
    import threading
    from intranet.services.gmail_service import enviar_email_html
    casal = matricula.casal
    emails_destino = []
    if casal.email_1: emails_destino.append(casal.email_1)
    if casal.email_2: emails_destino.append(casal.email_2)

    if emails_destino:
        assunto = f"Parabéns! Curso Concluído: {matricula.curso.nome}"
        contexto_email = {'casal': casal, 'curso': matricula.curso}

        def enviar_background_conclusao(emails, ass, ctx):
            for e in emails:
                try:
                    enviar_email_html(e, ass, 'ministerio_casais/email_curso_concluido.html', ctx)
                except Exception as err:
                    print(f"Erro ao enviar email de conclusão: {err}")

        threading.Thread(target=enviar_background_conclusao, args=(emails_destino, assunto, contexto_email)).start()

    messages.success(request, 'Matrícula aprovada! E-mail de conclusão disparado e certificado já pode ser gerado.')
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

        if request.FILES.get('foto_casal'):
            casal.foto_casal = request.FILES.get('foto_casal')
        if request.FILES.get('foto_conjuge_1'):
            casal.foto_conjuge_1 = request.FILES.get('foto_conjuge_1')
        if request.FILES.get('foto_conjuge_2'):
            casal.foto_conjuge_2 = request.FILES.get('foto_conjuge_2')

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

@login_required
def editar_curso(request, curso_id):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)
    curso = get_object_or_404(CursoCasal, id=curso_id)
    if request.method == 'POST':
        curso.nome = request.POST.get('nome', curso.nome)
        curso.descricao = request.POST.get('descricao', curso.descricao)
        curso.valor_curso = request.POST.get('valor_curso', curso.valor_curso)
        curso.carga_horaria = request.POST.get('carga_horaria', curso.carga_horaria)

        data_inicio = request.POST.get('data_inicio')
        if data_inicio:
            curso.data_inicio = data_inicio

        dias_semana_list = request.POST.getlist('dias_semana')
        if 'dias_semana' in request.POST:
            curso.dias_semana = ", ".join(dias_semana_list)

        curso.emite_certificado = request.POST.get('emite_certificado') == 'on'
        curso.compra_camiseta = request.POST.get('compra_camiseta') == 'on'

        curso.save()
        messages.success(request, 'Curso editado com sucesso!')
    return redirect('cursos_casais')

@login_required
def excluir_curso(request, curso_id):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)
    curso = get_object_or_404(CursoCasal, id=curso_id)
    if request.method == 'POST':
        curso.delete()
        messages.success(request, 'Curso excluído com sucesso!')
    return redirect('cursos_casais')

@login_required
def arquivar_casal(request, casal_id):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)
    casal = get_object_or_404(Casal, id=casal_id)
    if request.method == 'POST':
        casal.arquivado = True
        casal.save()

        from core.models import LogAuditoria
        LogAuditoria.objects.create(
            usuario_acao=request.user,
            acao_realizada="ARQUIVAR_CASAL",
            tabela_afetada="Casal",
            diferenca_json={"registro_afetado_id": casal.id, "status": "Arquivado (Saiu da Igreja/Foi Embora)"}
        )

        messages.success(request, 'Casal arquivado com sucesso.')
    return redirect('dashboard_casais')

@login_required
def excluir_casal(request, casal_id):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)
    casal = get_object_or_404(Casal, id=casal_id)
    if request.method == 'POST':
        casal_id_bkp = casal.id
        casal_nome = casal.nomes_juntos
        casal.delete()

        from core.models import LogAuditoria
        LogAuditoria.objects.create(
            usuario_acao=request.user,
            acao_realizada="EXCLUIR_CASAL",
            tabela_afetada="Casal",
            diferenca_json={"registro_afetado_id": casal_id_bkp, "nomes": casal_nome, "status": "Excluido definitivamente"}
        )

        messages.success(request, 'Casal excluído permanentemente da base de dados.')
    return redirect('dashboard_casais')

@login_required
def desfazer_aprovacao_matricula(request, matricula_id):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)
    matricula = get_object_or_404(MatriculaCursoCasal, id=matricula_id)
    if request.method == 'POST':
        matricula.aprovado = False
        matricula.percentual_conclusao = 0
        matricula.save()
        messages.success(request, 'Aprovação desfeita com sucesso.')
    return redirect('perfil_casal', casal_id=matricula.casal.id)

from django.db.models import Sum, F
from .models import PagamentoCursoCasal

@login_required
def gestao_financeira_cursos(request):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)

    cursos = CursoCasal.objects.all().prefetch_related('turmas__matriculas', 'turmas__matriculas__casal')

    # Resumo Geral
    total_esperado = sum(t.valor_curso * t.matriculas.count() for c in cursos for t in c.turmas.all())
    total_arrecadado = PagamentoCursoCasal.objects.aggregate(total=Sum('valor_pago'))['total'] or 0
    inadimplencia = total_esperado - total_arrecadado

    # Detalhamento por matricula
    matriculas = MatriculaCursoCasal.objects.select_related('turma__curso', 'casal').prefetch_related('historico_pagamentos').order_by('-data_matricula')

    for m in matriculas:
        m.total_pago = sum(p.valor_pago for p in m.historico_pagamentos.all())
        # Proteção caso a turma não esteja selecionada em dados sujos antigos
        curso_valor = m.turma.valor_curso if m.turma else 0
        m.saldo_devedor = curso_valor - m.total_pago
        if m.saldo_devedor <= 0:
            m.status_calc = 'Pago'
        elif m.total_pago > 0:
            m.status_calc = 'Parcial'
        else:
            m.status_calc = 'Pendente'

    context = {
        'total_esperado': total_esperado,
        'total_arrecadado': total_arrecadado,
        'inadimplencia': inadimplencia,
        'matriculas': matriculas,
    }
    return render(request, 'ministerio_casais/gestao_financeira_cursos.html', context)

@login_required
def registrar_pagamento_curso(request, matricula_id):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)

    if request.method == 'POST':
        matricula = get_object_or_404(MatriculaCursoCasal, id=matricula_id)
        valor = request.POST.get('valor_pago')
        forma = request.POST.get('forma_pagamento')
        obs = request.POST.get('observacoes', '')

        if valor and forma:
            try:
                valor_decimal = float(valor.replace(',', '.'))
                PagamentoCursoCasal.objects.create(
                    matricula=matricula,
                    valor_pago=valor_decimal,
                    forma_pagamento=forma,
                    observacoes=obs
                )

                # Atualizar o valor_pago na model MatriculaCursoCasal tambem
                matricula.valor_pago = sum(p.valor_pago for p in matricula.historico_pagamentos.all())

                curso_valor = matricula.turma.valor_curso if matricula.turma else 0
                if matricula.valor_pago >= curso_valor:
                    matricula.status_pagamento = 'Pago'
                elif matricula.valor_pago > 0:
                    matricula.status_pagamento = 'Pendente' # parcial

                matricula.save()

                messages.success(request, 'Pagamento registrado com sucesso!')
            except ValueError:
                messages.error(request, 'Valor de pagamento inválido.')

    return redirect('gestao_financeira_cursos')

@login_required
def disparar_cobranca_curso(request, matricula_id):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)

    if request.method == 'POST':
        matricula = get_object_or_404(MatriculaCursoCasal, id=matricula_id)

        curso_valor = matricula.turma.valor_curso if matricula.turma else 0
        saldo_devedor = curso_valor - sum(p.valor_pago for p in matricula.historico_pagamentos.all())

        if saldo_devedor > 0:
            import threading
            from intranet.services.gmail_service import enviar_email_html

            casal = matricula.casal
            emails_destino = []
            if casal.email_1: emails_destino.append(casal.email_1)
            if casal.email_2: emails_destino.append(casal.email_2)

            if emails_destino and matricula.turma:
                assunto = f"Lembrete de Pagamento: Curso {matricula.turma.curso.nome}"
                contexto_email = {'casal': casal, 'curso': matricula.turma.curso, 'saldo_devedor': saldo_devedor}

                for email in emails_destino:
                    thread = threading.Thread(
                        target=enviar_email_html,
                        args=(assunto, email, 'ministerio_casais/email_cobranca_curso.html', contexto_email)
                    )
                    thread.start()

                messages.success(request, f'Cobrança enviada para {", ".join(emails_destino)}')
            else:
                messages.warning(request, 'O casal não possui e-mails cadastrados ou a matrícula não tem turma vinculada.')
        else:
            messages.info(request, 'Esta matrícula não possui saldo devedor.')

    return redirect('gestao_financeira_cursos')

@login_required
def pdf_relatorio_financeiro_cursos(request):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)

    cursos = CursoCasal.objects.all().prefetch_related('turmas__matriculas', 'turmas__matriculas__casal')

    # Resumo
    total_esperado = sum(t.valor_curso * t.matriculas.count() for c in cursos for t in c.turmas.all())
    total_arrecadado = PagamentoCursoCasal.objects.aggregate(total=Sum('valor_pago'))['total'] or 0
    inadimplencia = total_esperado - total_arrecadado

    matriculas = MatriculaCursoCasal.objects.select_related('turma__curso', 'casal').prefetch_related('historico_pagamentos').order_by('-data_matricula')

    for m in matriculas:
        m.total_pago = sum(p.valor_pago for p in m.historico_pagamentos.all())
        curso_valor = m.turma.valor_curso if m.turma else 0
        m.saldo_devedor = curso_valor - m.total_pago
        if m.saldo_devedor <= 0:
            m.status_calc = 'Pago'
        elif m.total_pago > 0:
            m.status_calc = 'Parcial'
        else:
            m.status_calc = 'Pendente'

    html_str = render_to_string('ministerio_casais/pdf_financeiro_cursos.html', {
        'total_esperado': total_esperado,
        'total_arrecadado': total_arrecadado,
        'inadimplencia': inadimplencia,
        'matriculas': matriculas,
        'hoje': timezone.now()
    })

    from io import BytesIO
    import xhtml2pdf.pisa as pisa

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_str.encode("UTF-8")), result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="relatorio_financeiro_cursos.pdf"'
        return response
    return HttpResponse("Erro ao gerar PDF", status=500)
