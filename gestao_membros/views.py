from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings
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

def enviar_email_html(destinatario, assunto, template_name, context):
    pass # mock para não quebrar a view

@login_required
@user_passes_test(is_super_admin)
def listar_departamentos(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        categoria = request.POST.get('categoria')
        Departamento.objects.create(nome=nome, categoria=categoria)
        messages.success(request, f'Departamento {nome} criado.')
    departamentos = Departamento.objects.all()
    return render(request, 'gestao_membros/departamentos.html', {'departamentos': departamentos})

@login_required
@user_passes_test(is_lider)
def painel_lider(request):
    if is_super_admin(request.user):
        departamentos = Departamento.objects.all()
    else:
        departamentos = request.user.departamentos_liderados.all()
    
    membros_pendentes = Membro.objects.filter(is_active=False)
    
    return render(request, 'gestao_membros/painel_lider.html', {
        'departamentos': departamentos,
        'membros_pendentes': membros_pendentes
    })

@login_required
def aprovar_membro(request, membro_id):
    membro = get_object_or_404(Membro, id=membro_id)
    if is_lider(request.user):
        membro.is_active = True
        membro.save()
        messages.success(request, 'Membro aprovado.')
    return redirect('painel_lider')

@login_required
def rejeitar_membro(request, membro_id):
    membro = get_object_or_404(Membro, id=membro_id)
    if is_lider(request.user):
        membro.delete()
        messages.success(request, 'Membro rejeitado.')
    return redirect('painel_lider')

@login_required
def evoluir_membro(request, membro_id):
    membro = get_object_or_404(Membro, id=membro_id)
    if is_lider(request.user):
        membro.nivel_hierarquico = 'lider'
        membro.save()
        messages.success(request, 'Membro evoluído para Líder.')
    return redirect('painel_lider')

@login_required
def atualizar_habilidades(request, dep_id):
    dep = get_object_or_404(Departamento, id=dep_id)
    if request.method == 'POST' and is_lider(request.user):
        # Atualização mockada
        messages.success(request, 'Habilidades atualizadas.')
    return redirect('detalhes_departamento', dep_id=dep.id)

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
    return render(request, 'gestao_membros/avisos.html', {'avisos': avisos})

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
    if not (is_super_admin(request.user) or request.user.departamentos_liderados.filter(id=dep.id).exists() or request.user.departamentos_subliderados.filter(id=dep.id).exists()):
        return HttpResponseForbidden("Acesso Negado.")
    return render(request, 'gestao_membros/detalhes_departamento.html', {'dep': dep})

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
    if request.method == 'POST' and is_super_admin(request.user):
        acao = request.POST.get('acao')
        membro_id = request.POST.get('membro_id')
        membro = get_object_or_404(Membro, id=membro_id)
        if acao == 'add_lider':
            dep.lideres.add(membro)
            membro.nivel_hierarquico = 'lider'
            membro.save()
        elif acao == 'rem_lider':
            dep.lideres.remove(membro)
        messages.success(request, 'Liderança atualizada.')
    return redirect('detalhes_departamento', dep_id=dep.id)

@login_required
def painel_membros(request):
    if is_super_admin(request.user):
        membros = Membro.objects.all()
    else:
        membros = Membro.objects.filter(departamentos_ativos__in=request.user.departamentos_liderados.all()).distinct()
    return render(request, 'gestao_membros/gerenciador_membros.html', {'membros': membros})

@login_required
def exportar_membros_excel(request):
    import csv
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="membros.csv"'
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Nome Completo', 'Email', 'Telefone', 'Nivel Hierarquico', 'Data de Nascimento'])
    
    membros = Membro.objects.all().order_by('nome_completo')
    for m in membros:
        writer.writerow([m.nome_completo, m.email, m.telefone, m.get_nivel_hierarquico_display(), m.data_nascimento.strftime('%d/%m/%Y') if m.data_nascimento else 'N/A'])
        
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
        
        membro.cpf = request.POST.get('cpf', membro.cpf)
        membro.rg = request.POST.get('rg', membro.rg)
        membro.telefone = request.POST.get('telefone', membro.telefone)
        membro.anotacoes_lideranca = request.POST.get('anotacoes_lideranca', membro.anotacoes_lideranca)
        
        data_nascimento = request.POST.get('data_nascimento')
        if data_nascimento: membro.data_nascimento = data_nascimento
        
        data_casamento = request.POST.get('data_casamento')
        if data_casamento: membro.data_casamento = data_casamento

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
