import os
import re

file_path = r'c:\Users\MarcosLira\Desktop\Marcos\Projeto\midia_lgpd\views.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace criar_template_documento to also handle edits and saves
criar_view_code = """
@login_required
@user_passes_test(is_super_admin)
def criar_template_documento(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao', '')
        tipo_documento = request.POST.get('tipo_documento', 'pdf_lgpd')
        identificador = request.POST.get('identificador_sistema', '')
        conteudo = request.POST.get('conteudo_base', '')
        campos_raw = request.POST.get('campos_json')
        
        html_canva = request.POST.get('html_canva', '')
        css_canva = request.POST.get('css_canva', '')
        
        try:
            campos_json = json.loads(campos_raw) if campos_raw else []
        except:
            campos_json = []
            
        DocumentoTemplate.objects.create(
            titulo=titulo,
            descricao=descricao,
            tipo_documento=tipo_documento,
            identificador_sistema=identificador,
            conteudo_base=conteudo,
            campos_json=campos_json,
            html_canva=html_canva,
            css_canva=css_canva,
            criado_por=request.user
        )
        messages.success(request, 'Template Visual criado com sucesso!')
        return redirect('painel_documentos')
        
    return render(request, 'midia_lgpd/criador_templates.html', {'is_edit': False})

@login_required
@user_passes_test(is_super_admin)
def editar_template_documento(request, id):
    template = get_object_or_404(DocumentoTemplate, id=id)
    if request.method == 'POST':
        template.titulo = request.POST.get('titulo')
        template.descricao = request.POST.get('descricao', '')
        template.tipo_documento = request.POST.get('tipo_documento', 'pdf_lgpd')
        template.identificador_sistema = request.POST.get('identificador_sistema', '')
        template.conteudo_base = request.POST.get('conteudo_base', '')
        
        template.html_canva = request.POST.get('html_canva', '')
        template.css_canva = request.POST.get('css_canva', '')
        
        campos_raw = request.POST.get('campos_json')
        try:
            template.campos_json = json.loads(campos_raw) if campos_raw else []
        except:
            pass
            
        template.save()
        messages.success(request, 'Template Visual atualizado com sucesso!')
        return redirect('painel_documentos')
        
    return render(request, 'midia_lgpd/criador_templates.html', {'template': template, 'is_edit': True})

@login_required
@user_passes_test(is_super_admin)
def excluir_template_documento(request, id):
    template = get_object_or_404(DocumentoTemplate, id=id)
    template.ativo = False
    template.save()
    messages.success(request, 'Template arquivado/excluído com sucesso!')
    return redirect('painel_documentos')
"""

# replace the old criar_template_documento block
old_criar = r"""@login_required
@user_passes_test\(is_super_admin\)
def criar_template_documento\(request\):
    if request\.method == 'POST':
        titulo = request\.POST\.get\('titulo'\)
        descricao = request\.POST\.get\('descricao', ''\)
        conteudo = request\.POST\.get\('conteudo_base', ''\)
        campos_raw = request\.POST\.get\('campos_json'\)
        
        html_canva = request\.POST\.get\('html_canva', ''\)
        css_canva = request\.POST\.get\('css_canva', ''\)
        
        try:
            campos_json = json\.loads\(campos_raw\) if campos_raw else \[\]
        except:
            campos_json = \[\]
            
        DocumentoTemplate\.objects\.create\(
            titulo=titulo,
            descricao=descricao,
            conteudo_base=conteudo,
            campos_json=campos_json,
            html_canva=html_canva,
            css_canva=css_canva,
            criado_por=request\.user
        \)
        messages\.success\(request, 'Template Visual criado com sucesso!'\)
        return redirect\('painel_documentos'\)
        
    return render\(request, 'midia_lgpd/criador_templates\.html'\)"""

new_content = re.sub(old_criar, criar_view_code.strip(), content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)
