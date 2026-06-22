import os

# Append URLs
urls_content = """
    # Módulo de Gestão de Voluntários (RH)
    path('painel-lider/rh/', views.rh_painel, name='rh_painel'),
    path('painel-lider/rh/dossie/<int:membro_id>/', views.rh_dossie_membro, name='rh_dossie_membro'),
    path('painel-lider/rh/avaliar/<int:membro_id>/', views.rh_avaliar_membro, name='rh_avaliar_membro'),
    path('painel-lider/rh/ocorrencia/nova/', views.rh_nova_ocorrencia, name='rh_nova_ocorrencia'),
    path('painel-lider/rh/disciplina/<int:membro_id>/', views.rh_aplicar_disciplina, name='rh_aplicar_disciplina'),
    path('painel-lider/rh/disciplina/pdf/<int:acao_id>/', views.rh_gerar_pdf_disciplina, name='rh_gerar_pdf_disciplina'),
]"""

with open(r'c:\Users\MarcosLira\Desktop\Marcos\Projeto\gestao_membros\urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the last closing bracket ']' and append the new urls
content = content.rstrip().rsplit(']', 1)[0] + urls_content

with open(r'c:\Users\MarcosLira\Desktop\Marcos\Projeto\gestao_membros\urls.py', 'w', encoding='utf-8') as f:
    f.write(content)


# Append Views
views_content = """
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
    \"\"\"Painel principal do RH mostrando todos os voluntários sob gestão do líder ou todos para admin\"\"\"
    if is_super_admin(request.user):
        membros = Membro.objects.filter(is_active=True).order_by('first_name')
        departamentos = Departamento.objects.all()
    else:
        # Pega todos os membros dos departamentos que este líder lidera ou sublidera
        deps_liderados = request.user.departamentos_liderados.all() | request.user.departamentos_subliderados.all()
        departamentos = deps_liderados.distinct()
        membros = Membro.objects.filter(departamentos_ativos__in=departamentos, is_active=True).distinct().order_by('first_name')
        
    return render(request, 'gestao_membros/rh_painel.html', {
        'membros': membros,
        'departamentos': departamentos
    })

@login_required
@user_passes_test(is_lider)
def rh_dossie_membro(request, membro_id):
    \"\"\"Visualiza o histórico completo do membro (Avaliações, Ocorrências, Ações Disciplinares)\"\"\"
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
"""

with open(r'c:\Users\MarcosLira\Desktop\Marcos\Projeto\gestao_membros\views.py', 'a', encoding='utf-8') as f:
    f.write(views_content)
