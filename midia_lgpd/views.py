"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: midia_lgpd/views.py
* DESCRIÇÃO: Views de assinatura de LGPD e repositório de arquivos.
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 25/05/2026 14:15
* LOG DE ALTERAÇÕES:
* - 25/05/2026 14:15: Criação inicial das views
"""

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .models import TermoLGPD, AssinaturaLGPD, ArquivoMidia, DocumentoTemplate, DocumentoGerado
from gestao_membros.models import Departamento
import json

# Serviço de Nuvem e E-mail
from intranet.services.google_drive import upload_arquivo_drive
from intranet.services.gmail_service import enviar_email_html
from intranet.services.pdf_generator import gerar_pdf_contrato

def is_super_admin(user):
    return user.nivel_hierarquico == 'super_admin' or user.is_superuser

@login_required
def ler_assinar_termo(request):
    termo_ativo = TermoLGPD.objects.filter(is_ativo=True).first()
    
    if not termo_ativo:
        messages.warning(request, 'Nenhum termo ativo configurado no sistema no momento.')
        return redirect('dashboard')
        
    ja_assinou = AssinaturaLGPD.objects.filter(membro=request.user, termo=termo_ativo).exists()
    
    if request.method == 'POST' and not ja_assinou:
        # Obter IP do usuário (básico)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
            
        AssinaturaLGPD.objects.create(
            membro=request.user,
            termo=termo_ativo,
            ip_registro=ip
        )
        
        # Hook para Envio de E-mail com Cópia do PDF
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        import io
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        c.drawString(50, 800, f"Termo de LGPD Assinado: {termo_ativo.titulo}")
        c.drawString(50, 770, f"Assinado por: {request.user.get_full_name()}")
        c.drawString(50, 750, f"E-mail: {request.user.email}")
        c.drawString(50, 730, f"IP de Registro: {ip}")
        c.drawString(50, 710, "Este documento prova o aceite digital do termo.")
        c.showPage()
        c.save()
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        enviar_email_html(
            destinatario=request.user.email,
            assunto="Cópia - Termo LGPD Assinado com Sucesso",
            template_name="generico.html",
            context={
                'content': f"<h2 style='color:#14532d;'>Obrigado, {request.user.first_name}!</h2><p>Confirmamos o aceite digital do termo: <strong>{termo_ativo.titulo}</strong>.</p><p>Segue em anexo a via assinada do seu termo para sua segurança.</p>"
            },
            anexos=[(f"Termo_LGPD_{request.user.first_name}.pdf", pdf_bytes, 'application/pdf')]
        )
        
        messages.success(request, 'Obrigado! O Termo de Uso de Imagem e LGPD foi assinado digitalmente. Uma cópia em PDF foi enviada para o seu e-mail.')
        return redirect('dashboard')
        
    return render(request, 'midia_lgpd/termo_aceite.html', {
        'termo': termo_ativo,
        'ja_assinou': ja_assinou
    })

@login_required
@user_passes_test(is_super_admin)
def painel_midia(request):
    if request.user.nivel_hierarquico == 'super_admin' or request.user.is_superuser:
        departamentos = Departamento.objects.all()
    else:
        lider = request.user.departamentos_liderados.all()
        sub = request.user.departamentos_subliderados.all()
        departamentos = (lider | sub).distinct()

    arquivos = ArquivoMidia.objects.filter(departamento__in=departamentos).order_by('-data_envio')
    
    # Estatística básica da LGPD
    termo_ativo = TermoLGPD.objects.filter(is_ativo=True).first()
    total_assinaturas = AssinaturaLGPD.objects.filter(termo=termo_ativo).count() if termo_ativo else 0
    
    return render(request, 'midia_lgpd/painel.html', {
        'arquivos': arquivos,
        'departamentos': departamentos,
        'termo_ativo': termo_ativo,
        'total_assinaturas': total_assinaturas
    })

@login_required
@user_passes_test(is_super_admin)
def upload_arquivo(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        dept_id = request.POST.get('departamento_id')
        is_publico = request.POST.get('is_publico') == 'on'
        arquivo = request.FILES.get('arquivo')
        
        if arquivo:
            novo_arquivo = ArquivoMidia.objects.create(
                titulo=titulo,
                arquivo=arquivo,
                departamento_id=dept_id,
                enviado_por=request.user,
                is_publico_para_membros=is_publico
            )
            
            # Hook para upload secundário no Google Drive (Cloud Backup)
            upload_arquivo_drive(novo_arquivo.arquivo.path, titulo)
            
            messages.success(request, 'Arquivo enviado para o repositório local e sincronizado com Google Drive.')
        else:
            messages.error(request, 'Nenhum arquivo anexado.')
            
    return redirect('painel_midia')

@login_required
@user_passes_test(is_super_admin)
def painel_documentos(request):
    templates = DocumentoTemplate.objects.filter(ativo=True).order_by('-data_criacao')
    documentos = DocumentoGerado.objects.order_by('-data_solicitacao')
    
    if request.user.nivel_hierarquico not in ['super_admin', 'pastor_regente']:
        documentos = documentos.filter(solicitado_por=request.user)
        
    return render(request, 'midia_lgpd/painel_documentos.html', {
        'templates': templates,
        'documentos': documentos
    })

@login_required
@user_passes_test(is_super_admin)
def criar_template_documento(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao', '')
        conteudo = request.POST.get('conteudo_base', '')
        campos_raw = request.POST.get('campos_json')
        
        try:
            campos_json = json.loads(campos_raw) if campos_raw else []
        except:
            campos_json = []
            
        DocumentoTemplate.objects.create(
            titulo=titulo,
            descricao=descricao,
            conteudo_base=conteudo,
            campos_json=campos_json,
            criado_por=request.user
        )
        messages.success(request, 'Template criado com sucesso!')
        return redirect('painel_documentos')
        
    return render(request, 'midia_lgpd/criador_templates.html')

@login_required
@user_passes_test(is_super_admin)
def enviar_documento(request):
    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        email = request.POST.get('email_destino')
        nome = request.POST.get('nome_destino')
        
        template = get_object_or_404(DocumentoTemplate, id=template_id)
        
        doc = DocumentoGerado.objects.create(
            template=template,
            email_destino=email,
            nome_destino=nome,
            solicitado_por=request.user
        )
        
        link = f"{settings.BASE_URL}/midia_lgpd/documentos/assinar/{doc.token_acesso}/"
        
        enviar_email_html(
            destinatario=email,
            assunto=f"Solicitação de Assinatura: {template.titulo}",
            template_name="generico.html",
            context={
                'content': f"<p>Olá {nome or ''}, você foi solicitado a assinar um documento.</p><br><a href='{link}' style='padding: 10px 20px; background: #22c55e; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;'>Acessar e Assinar</a>"
            }
        )
        
        messages.success(request, f'Link de assinatura enviado para {email}.')
    return redirect('painel_documentos')

def assinar_documento_externo(request, token):
    doc = get_object_or_404(DocumentoGerado, token_acesso=token)
    
    if doc.status == 'assinado':
        return render(request, 'midia_lgpd/sucesso_assinatura.html', {'doc': doc})
        
    if request.method == 'POST':
        # Captura todos os campos
        dados = {}
        for campo in doc.template.campos_json:
            dados[campo['nome']] = request.POST.get(campo['nome'], '')
            
        doc.dados_preenchidos = dados
        doc.nome_destino = request.POST.get('assinatura_nome_completo', doc.nome_destino)
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        doc.ip_assinatura = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
        doc.data_assinatura = timezone.now()
        doc.status = 'assinado'
        
        # Gera o PDF
        gerar_pdf_contrato(doc)
        
        # Se enviou anexo
        if 'anexo_scan' in request.FILES:
            doc.anexo_fisico_escaneado = request.FILES['anexo_scan']
            
        doc.save()
        
        # Envia e-mail de confirmação com recibo
        link_pdf = f"{settings.BASE_URL}{doc.arquivo_pdf_final.url}"
        enviar_email_html(
            destinatario=doc.email_destino,
            assunto=f"Cópia do Contrato: {doc.template.titulo}",
            template_name="generico.html",
            context={
                'content': f"<p>Obrigado! Seu documento foi assinado digitalmente e imutável.</p><br><a href='{link_pdf}' style='padding: 10px 20px; background: #2563eb; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;'>Baixar PDF Original</a>"
            }
        )
        
        # Notifica quem solicitou
        if doc.solicitado_por:
            enviar_email_html(
                destinatario=doc.solicitado_por.email,
                assunto=f"Documento Assinado por {doc.nome_destino}",
                template_name="generico.html",
                context={
                    'content': f"<p>O contato {doc.email_destino} acabou de assinar o documento <b>{doc.template.titulo}</b>.</p><br><a href='{link_pdf}' style='padding: 10px 20px; background: #14532d; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;'>Baixar PDF Assinado</a>"
                }
            )
            
        return render(request, 'midia_lgpd/sucesso_assinatura.html', {'doc': doc})
        
    return render(request, 'midia_lgpd/assinatura_externa.html', {'doc': doc})
