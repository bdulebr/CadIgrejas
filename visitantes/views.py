"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: visitantes/views.py
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
from django.http import JsonResponse, HttpResponse
from .models import Visitante, VisitaCulto, RegistroAcompanhamento
from gestao_membros.models import Departamento
from core.models import Membro
from django.db.models import Count, Q
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.conf import settings
import threading
import os
from io import BytesIO
from xhtml2pdf import pisa

def enviar_email_boas_vindas_background(nome, email, base_url):
    try:
        from core.models import ConfiguracaoSistema
        sys_config = ConfiguracaoSistema.objects.first()
        logo_url = base_url + sys_config.igreja_logo.url if sys_config and sys_config.igreja_logo else base_url + '/static/img/logo.jpg'

        html_message = render_to_string('visitantes/email_boas_vindas.html', {'nome': nome, 'base_url': base_url, 'logo_url': logo_url})
        plain_message = strip_tags(html_message)
        send_mail(
            subject='Bem-vindo(a) à Palavra de Vida!',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception as e:
        print(f"Erro ao enviar email para {email}: {e}")

def enviar_email_novo_membro_background(nome, email, base_url):
    try:
        from core.models import ConfiguracaoSistema
        sys_config = ConfiguracaoSistema.objects.first()
        logo_url = base_url + sys_config.igreja_logo.url if sys_config and sys_config.igreja_logo else base_url + '/static/img/logo.jpg'

        html_message = render_to_string('visitantes/email_novo_membro.html', {'nome': nome, 'base_url': base_url, 'logo_url': logo_url})
        plain_message = strip_tags(html_message)
        send_mail(
            subject='Bem-vindo à Família Palavra de Vida Sede!',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception as e:
        print(f"Erro ao enviar email de novo membro para {email}: {e}")

@login_required
@requer_permissao('visitantes', 'ver')
def visitantes_dashboard(request):
    """
    Dashboard principal de visitantes. Mostra todos os visitantes ativos,
    estatísticas rápidas e permite busca.
    """
    if request.user.nivel_hierarquico == 'membro_voluntario':
        messages.error(request, "Acesso Negado. Apenas líderes podem gerenciar visitantes.")
        return redirect('dashboard')

    query = request.GET.get('q', '')
    filtro_tipo = request.GET.get('tipo', '')

    # Exibir apenas os que NÃO se tornaram membros E NÃO desistiram
    visitantes = Visitante.objects.filter(em_acompanhamento=True, tornou_se_membro=False, desistiu=False).annotate(
        total_visitas=Count('visitas', distinct=True),
        total_contatos=Count('registros_acompanhamento', distinct=True)
    ).order_by('-data_cadastro')

    if query:
        visitantes = visitantes.filter(
            Q(nome_completo__icontains=query) |
            Q(telefone__icontains=query) |
            Q(email__icontains=query)
        )

    if filtro_tipo:
        visitantes = visitantes.filter(tipo=filtro_tipo)

    # Estatísticas
    total_ativos = Visitante.objects.filter(em_acompanhamento=True, tornou_se_membro=False, desistiu=False).count()
    total_novos_mes = Visitante.objects.filter(data_cadastro__month=timezone.now().month, data_cadastro__year=timezone.now().year, tornou_se_membro=False, desistiu=False).count()

    todos_visitantes_para_vinculo = Visitante.objects.filter(tornou_se_membro=False, desistiu=False).order_by('nome_completo')

    context = {
        'visitantes': visitantes,
        'total_ativos': total_ativos,
        'total_novos_mes': total_novos_mes,
        'query': query,
        'filtro_tipo': filtro_tipo,
        'todos_visitantes_para_vinculo': todos_visitantes_para_vinculo,
    }
    return render(request, 'visitantes/dashboard.html', context)


@login_required
@requer_permissao('visitantes', 'ver')
def visitante_perfil(request, visitante_id):
    """
    Perfil detalhado do visitante, mostrando timeline de visitas e acompanhamentos.
    """
    if request.user.nivel_hierarquico == 'membro_voluntario':
        messages.error(request, "Acesso Negado.")
        return redirect('dashboard')

    visitante = get_object_or_404(Visitante, id=visitante_id)
    visitas = visitante.visitas.all()
    acompanhamentos = visitante.registros_acompanhamento.all()

    # Combinar visitas e acompanhamentos em uma timeline unificada
    timeline = []
    for v in visitas:
        timeline.append({
            'tipo': 'visita',
            'data': v.data_culto,
            'obj': v
        })
    for a in acompanhamentos:
        timeline.append({
            'tipo': 'acompanhamento',
            'data': a.data_contato.date() if isinstance(a.data_contato, timezone.datetime) else a.data_contato,
            'obj': a
        })

    # Ordenar do mais recente para o mais antigo
    timeline.sort(key=lambda x: x['data'], reverse=True)

    departamentos = Departamento.objects.all()

    context = {
        'visitante': visitante,
        'timeline': timeline,
        'departamentos': departamentos,
    }
    return render(request, 'visitantes/perfil.html', context)


@login_required
@requer_permissao('visitantes', 'ver')
def cadastrar_visitante(request):
    """
    Modal/Página para cadastrar um novo visitante rapidamente.
    """
    if request.method == 'POST':
        nome_completo = request.POST.get('nome_completo')
        telefone = request.POST.get('telefone')
        email = request.POST.get('email')
        tipo = request.POST.get('tipo', 'Visitante')
        endereco = request.POST.get('endereco')
        familiar_vinculado_id = request.POST.get('familiar_vinculado_id')

        familiar = None
        if familiar_vinculado_id:
            familiar = Visitante.objects.filter(id=familiar_vinculado_id).first()

        visitante = Visitante.objects.create(
            nome_completo=nome_completo,
            telefone=telefone,
            email=email,
            tipo=tipo,
            endereco=endereco,
            familiar_vinculado=familiar,
            cadastrado_por=request.user
        )

        # Removido o cadastro automático (mock) de Visita Culto,
        # as visitas devem ser registradas manualmente no perfil.

        # Enviar e-mail de boas-vindas assíncrono se possuir e-mail
        if email:
            base_url = request.build_absolute_uri('/')[:-1]
            threading.Thread(target=enviar_email_boas_vindas_background, args=(nome_completo, email, base_url)).start()

        messages.success(request, f"{tipo} {nome_completo} cadastrado com sucesso!")
        return redirect('visitante_perfil', visitante_id=visitante.id)

    return redirect('visitantes_dashboard')


@login_required
@requer_permissao('visitantes', 'ver')
def editar_visitante(request, visitante_id):
    visitante = get_object_or_404(Visitante, id=visitante_id)
    if request.method == 'POST':
        visitante.nome_completo = request.POST.get('nome_completo')
        visitante.telefone = request.POST.get('telefone')
        visitante.email = request.POST.get('email')
        visitante.tipo = request.POST.get('tipo', visitante.tipo)
        visitante.endereco = request.POST.get('endereco')

        familiar_vinculado_id = request.POST.get('familiar_vinculado_id')
        if familiar_vinculado_id:
            visitante.familiar_vinculado = Visitante.objects.filter(id=familiar_vinculado_id).first()
        else:
            visitante.familiar_vinculado = None

        visitante.save()
        messages.success(request, "Perfil atualizado com sucesso!")

    return redirect('visitante_perfil', visitante_id=visitante.id)


@login_required
@requer_permissao('visitantes', 'ver')
def tornar_membro(request, visitante_id):
    visitante = get_object_or_404(Visitante, id=visitante_id)
    if request.method == 'POST':
        visitante.em_acompanhamento = False
        visitante.tornou_se_membro = True
        visitante.save()

        # Registrar o marco no CRM
        RegistroAcompanhamento.objects.create(
            visitante=visitante,
            meio_contato='Presencial',
            resumo_conversa='[SISTEMA] O visitante concluiu o acompanhamento e tornou-se um membro integrado da igreja.',
            proximo_passo='Nenhum',
            responsavel=request.user,
            data_contato=timezone.now()
        )

        # Enviar e-mail de Novo Membro / Baixar App assincronamente se houver email
        if visitante.email:
            base_url = request.build_absolute_uri('/')[:-1]
            threading.Thread(target=enviar_email_novo_membro_background, args=(visitante.nome_completo, visitante.email, base_url)).start()

        messages.success(request, f"{visitante.nome_completo} agora é membro e foi movido para o Arquivo de Novos Membros!")
        return redirect('visitantes_dashboard')

    return redirect('visitante_perfil', visitante_id=visitante.id)


@login_required
@requer_permissao('visitantes', 'ver')
def visitantes_arquivo(request):
    """
    Dashboard secundário que lista pessoas que se tornaram membros ou desistiram.
    """
    if request.user.nivel_hierarquico == 'membro_voluntario':
        messages.error(request, "Acesso Negado.")
        return redirect('dashboard')

    query = request.GET.get('q', '')

    visitantes = Visitante.objects.filter(Q(tornou_se_membro=True) | Q(desistiu=True)).annotate(
        total_visitas=Count('visitas', distinct=True),
        total_contatos=Count('registros_acompanhamento', distinct=True)
    ).order_by('-data_cadastro')

    if query:
        visitantes = visitantes.filter(
            Q(nome_completo__icontains=query) |
            Q(telefone__icontains=query) |
            Q(email__icontains=query)
        )

    total_arquivados = Visitante.objects.filter(Q(tornou_se_membro=True) | Q(desistiu=True)).count()

    context = {
        'visitantes': visitantes,
        'total_arquivados': total_arquivados,
        'query': query,
    }
    return render(request, 'visitantes/arquivo_membros.html', context)

@login_required
@requer_permissao('visitantes', 'ver')
def desistencia_visitante(request, visitante_id):
    visitante = get_object_or_404(Visitante, id=visitante_id)
    if request.method == 'POST':
        visitante.em_acompanhamento = False
        visitante.desistiu = True
        visitante.save()

        # Registrar o marco no CRM
        RegistroAcompanhamento.objects.create(
            visitante=visitante,
            meio_contato='Outro',
            resumo_conversa='[SISTEMA] O visitante desistiu ou parou de frequentar. Acompanhamento finalizado.',
            proximo_passo='Nenhum',
            responsavel=request.user,
            data_contato=timezone.now()
        )

        messages.warning(request, f"{visitante.nome_completo} foi marcado como desistente e movido para o arquivo.")
        return redirect('visitantes_dashboard')

    return redirect('visitante_perfil', visitante_id=visitante.id)

@login_required
@requer_permissao('visitantes', 'ver')
def excluir_visitante(request, visitante_id):
    visitante = get_object_or_404(Visitante, id=visitante_id)
    if request.method == 'POST':
        nome = visitante.nome_completo
        visitante.delete()
        messages.error(request, f"O cadastro de {nome} foi excluído permanentemente.")
        return redirect('visitantes_dashboard')

    return redirect('visitante_perfil', visitante_id=visitante_id)

@login_required
@requer_permissao('visitantes', 'ver')
def adicionar_acompanhamento(request, visitante_id):
    visitante = get_object_or_404(Visitante, id=visitante_id)
    if request.method == 'POST':
        meio = request.POST.get('meio_contato')
        resumo = request.POST.get('resumo_conversa')
        proximo_passo = request.POST.get('proximo_passo')
        data_contato = request.POST.get('data_contato')

        registro = RegistroAcompanhamento.objects.create(
            visitante=visitante,
            meio_contato=meio,
            resumo_conversa=resumo,
            proximo_passo=proximo_passo,
            responsavel=request.user
        )
        if data_contato:
            registro.data_contato = data_contato
            registro.save()

        messages.success(request, "Registro de acompanhamento adicionado!")
    return redirect('visitante_perfil', visitante_id=visitante.id)


@login_required
@requer_permissao('visitantes', 'ver')
def adicionar_visita(request, visitante_id):
    visitante = get_object_or_404(Visitante, id=visitante_id)
    if request.method == 'POST':
        data_culto = request.POST.get('data_culto')
        nome_culto = request.POST.get('nome_culto')
        modalidade = request.POST.get('modalidade', 'Presencial')
        observacoes = request.POST.get('observacoes', '')

        VisitaCulto.objects.create(
            visitante=visitante,
            data_culto=data_culto,
            nome_culto=nome_culto,
            modalidade=modalidade,
            observacoes=observacoes
        )
        messages.success(request, "Visita ao culto registrada!")
    return redirect('visitante_perfil', visitante_id=visitante.id)


@login_required
@requer_permissao('visitantes', 'ver')
def exportar_relatorio_geral_pdf(request):
    if request.user.nivel_hierarquico == 'membro_voluntario':
        return HttpResponse("Acesso Negado", status=403)

    visitantes = Visitante.objects.all().order_by('-data_cadastro')

    from core.models import ConfiguracaoSistema
    sys_config = ConfiguracaoSistema.objects.first()
    if sys_config and sys_config.igreja_logo:
        logo_path = sys_config.igreja_logo.path
    else:
        logo_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'img', 'logo.jpg')

    html_str = render_to_string('visitantes/pdf_relatorio_geral.html', {'visitantes': visitantes, 'data_geracao': timezone.now(), 'logo_path': logo_path})

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_str.encode("UTF-8")), result)

    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="relatorio_geral_visitantes.pdf"'
        return response
    return HttpResponse("Erro ao gerar PDF", status=500)


@login_required
@requer_permissao('visitantes', 'ver')
def exportar_relatorio_individual_pdf(request, visitante_id):
    if request.user.nivel_hierarquico == 'membro_voluntario':
        return HttpResponse("Acesso Negado", status=403)

    visitante = get_object_or_404(Visitante, id=visitante_id)
    visitas = visitante.visitas.all().order_by('-data_culto')
    acompanhamentos = visitante.registros_acompanhamento.all().order_by('-data_contato')

    from core.models import ConfiguracaoSistema
    sys_config = ConfiguracaoSistema.objects.first()
    if sys_config and sys_config.igreja_logo:
        logo_path = sys_config.igreja_logo.path
    else:
        logo_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'img', 'logo.jpg')

    html_str = render_to_string('visitantes/pdf_relatorio_individual.html', {
        'visitante': visitante,
        'visitas': visitas,
        'acompanhamentos': acompanhamentos,
        'data_geracao': timezone.now(),
        'logo_path': logo_path
    })

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_str.encode("UTF-8")), result)

    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="dossie_{visitante.nome_completo.replace(" ", "_")}.pdf"'
        return response
    return HttpResponse("Erro ao gerar PDF", status=500)
