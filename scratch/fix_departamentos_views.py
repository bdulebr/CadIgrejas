import os
import re

file_path = r'C:\Users\MarcosLira\Desktop\Marcos\Projeto\gestao_membros\views.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# REWRITE detalhes_departamento
new_detalhes = """@login_required
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
        
    from .models import ConfiguracaoSlotEscala
    tipos_evento = ConfiguracaoSlotEscala.TIPO_EVENTO_CHOICES if hasattr(ConfiguracaoSlotEscala, 'TIPO_EVENTO_CHOICES') else []
    
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
"""

content = re.sub(
    r'@login_required\s*\ndef detalhes_departamento.*?return render\(request, \'gestao_membros/detalhes_departamento\.html\', {\'dep\': dep}\)\n',
    new_detalhes,
    content,
    flags=re.DOTALL
)

# REWRITE atribuir_lideranca
new_atribuir = """@login_required
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
"""

content = re.sub(
    r'@login_required\s*\ndef atribuir_lideranca.*?return redirect\(\'detalhes_departamento\', dep_id=dep\.id\)\n',
    new_atribuir,
    content,
    flags=re.DOTALL
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updates applied to views.py")
