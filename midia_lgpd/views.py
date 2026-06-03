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
from .models import TermoLGPD, AssinaturaLGPD, ArquivoMidia, DocumentoTemplate, DocumentoGerado, PastaVirtual, CompartilhamentoPasta
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

import json

@login_required
def portal_lgpd(request):
    # Encontrar a assinatura atual
    assinatura = AssinaturaLGPD.objects.filter(membro=request.user).order_by('-data_aceite').first()
    return render(request, 'midia_lgpd/portal_lgpd.html', {
        'assinatura': assinatura
    })

@login_required
def exportar_dados_pessoais(request):
    import io
    import zipfile
    from django.http import HttpResponse

    # Montar JSON com dados pessoais
    user = request.user
    dados = {
        'id': user.id,
        'username': user.username,
        'nome_completo': user.get_full_name(),
        'email': user.email,
        'cpf': user.cpf,
        'rg': user.rg,
        'data_nascimento': str(user.data_nascimento) if user.data_nascimento else None,
        'telefone': user.telefone,
        'cep': user.cep,
        'endereco': user.endereco,
        'bairro': user.bairro,
        'cidade': user.cidade,
        'estado': user.estado,
        'estado_civil': user.estado_civil,
        'habilidades': user.habilidades,
        'data_cadastro': str(user.data_cadastro),
    }
    json_data = json.dumps(dados, indent=4, ensure_ascii=False)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('meus_dados.json', json_data.encode('utf-8'))

    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="MeusDados_PVEnseada.zip"'
    return response

@login_required
def solicitar_esquecimento(request):
    if request.method == 'POST':
        # Enviar e-mail para o DPO/Admin
        enviar_email_html(
            destinatario=settings.DEFAULT_FROM_EMAIL, # E-mail do DPO
            assunto="LGPD: Solicitação de Esquecimento de Dados",
            template_name="generico.html",
            context={
                'content': f"<h2 style='color:#b91c1c;'>Solicitação LGPD (Deleção)</h2><p>O usuário <b>{request.user.get_full_name()}</b> (CPF: {request.user.cpf}, Email: {request.user.email}) solicitou a deleção definitiva de seus dados conforme a LGPD.</p><p>Ação manual necessária pelo DPO.</p>"
            }
        )
        messages.success(request, "Sua solicitação de esquecimento foi registrada e encaminhada ao DPO. Entraremos em contato em breve.")
        return redirect('portal_lgpd')
    return redirect('portal_lgpd')

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

        assinatura_base64 = request.POST.get('assinatura_base64', '')
        if assinatura_base64:
            dados['assinatura_base64'] = assinatura_base64

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


@login_required
def pv_drive(request, modo='pessoal', alvo_id=None, pasta_id=None):
    # Lógica de Permissões Básicas
    # Qualquer membro logado tem acesso.
    departamentos = []
    if request.user.nivel_hierarquico in ['super_admin', 'pastor_regente']:
        departamentos = Departamento.objects.all()
    else:
        departamentos = (request.user.departamentos_liderados.all() | request.user.departamentos_subliderados.all()).distinct()

    dep_atual = None
    pasta_atual = None

    q = request.GET.get('q', '').strip()

    # 1. Determinar a pasta_atual raiz do contexto
    if modo == 'departamento' and alvo_id:
        dep_atual = get_object_or_404(Departamento, id=alvo_id)
        if dep_atual not in departamentos:
            messages.error(request, 'Você não tem permissão para gerenciar o Drive deste departamento.')
            return redirect('pv_drive_pessoal')

        pasta_raiz = PastaVirtual.objects.filter(tipo_pasta='departamento', departamento=dep_atual).first()
    else:
        # Pessoal
        modo = 'pessoal'
        pasta_raiz = PastaVirtual.objects.filter(tipo_pasta='usuario', dono_membro=request.user).first()
        if not pasta_raiz:
            messages.error(request, 'Seu Drive Pessoal ainda não foi gerado pelo sistema.')
            return redirect('dashboard')

    if pasta_id:
        pasta_atual = get_object_or_404(PastaVirtual, id=pasta_id, is_excluida=False)
        # Garantir que a pasta_atual pertence à raiz (evita ID forjado)
        # Uma verificação real exigiria subir todos os parents.
        # Como o departamento e dono_membro limitam, podemos checar:
        if modo == 'departamento' and pasta_atual.departamento != dep_atual:
            return redirect('pv_drive_home')
        if modo == 'pessoal' and pasta_atual.dono_membro != request.user:
            return redirect('pv_drive_home')
    else:
        pasta_atual = pasta_raiz

    # 2. Resolução de Busca ou Listagem
    if q:
        if modo == 'departamento':
            pastas = PastaVirtual.objects.filter(departamento=dep_atual, nome__icontains=q, is_excluida=False).order_by('nome')
            arquivos = ArquivoMidia.objects.filter(departamento=dep_atual, titulo__icontains=q, is_excluido=False).order_by('-data_envio')
        else:
            pastas = PastaVirtual.objects.filter(dono_membro=request.user, nome__icontains=q, is_excluida=False).order_by('nome')
            arquivos = ArquivoMidia.objects.filter(dono_membro=request.user, titulo__icontains=q, is_excluido=False).order_by('-data_envio')
        breadcrumbs = []
    else:
        # Se for a pasta Compartilhados Comigo, a lógica muda (Mostra os shortcuts ou permissoes)
        if pasta_atual.tipo_pasta == 'compartilhados':
            pastas = PastaVirtual.objects.none() # Atalhos de pastas poderiam ser mostrados aqui, mas por agora arquivos:
            # Buscar arquivos onde eu tenho Permissao
            if modo == 'departamento':
                # Arquivos compartilhados com meu departamento
                permissoes = PermissaoPVDrive.objects.filter(alvo_departamento=dep_atual, is_ativo=True)
            else:
                # Arquivos compartilhados comigo
                permissoes = PermissaoPVDrive.objects.filter(alvo_membro=request.user, is_ativo=True)

            pastas_ids = permissoes.values_list('pasta_id', flat=True)
            pastas = PastaVirtual.objects.filter(id__in=pastas_ids, is_excluida=False)
            arquivos = ArquivoMidia.objects.none()
        else:
            pastas = PastaVirtual.objects.filter(parent=pasta_atual, is_excluida=False).order_by('nome')
            arquivos = ArquivoMidia.objects.filter(pasta=pasta_atual, is_excluido=False).order_by('-data_envio')

        # Breadcrumbs
        breadcrumbs = []
        p = pasta_atual
        while p:
            # Não mostrar as raízes ocultas do sistema (PV Drive, Departamentos)
            if p.tipo_pasta not in ['raiz', 'raiz_deptos', 'raiz_usuarios']:
                breadcrumbs.insert(0, p)
            p = p.parent

    # Contexto final
    return render(request, 'midia_lgpd/pv_drive.html', {
        'departamentos_menu': departamentos,
        'modo_atual': modo,
        'dep_atual': dep_atual,
        'pasta_atual': pasta_atual,
        'pastas': pastas,
        'arquivos': arquivos,
        'breadcrumbs': breadcrumbs,
        'search_query': q,
    })

from intranet.services.google_drive import get_drive_service
from googleapiclient.http import MediaIoBaseUpload
from django.http import HttpResponse
import mimetypes

@login_required
def criar_pasta(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        modo_atual = request.POST.get('modo_atual')
        parent_id = request.POST.get('parent_id')

        if not parent_id:
            messages.error(request, 'Erro: Pasta de destino não identificada.')
            return redirect('pv_drive_home')

        pasta_mae = get_object_or_404(PastaVirtual, id=parent_id)

        if pasta_mae.tipo_pasta == 'compartilhados':
            messages.error(request, 'Você não pode criar pastas aqui.')
            return redirect('pv_drive_home')

        service = get_drive_service()
        gdrive_folder_id = None
        gdrive_url = None

        if service and pasta_mae.gdrive_folder_id:
            try:
                file_metadata = {
                    'name': nome,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [pasta_mae.gdrive_folder_id]
                }
                file = service.files().create(body=file_metadata, fields='id, webViewLink', supportsAllDrives=True).execute()
                gdrive_folder_id = file.get('id')
                gdrive_url = file.get('webViewLink')
            except Exception as e:
                messages.error(request, f'Aviso GDrive: {e}')

        PastaVirtual.objects.create(
            nome=nome,
            tipo_pasta='normal',
            departamento=pasta_mae.departamento,
            dono_membro=pasta_mae.dono_membro,
            parent=pasta_mae,
            criado_por=request.user,
            gdrive_folder_id=gdrive_folder_id,
            gdrive_url=gdrive_url
        )
        messages.success(request, 'Pasta criada com sucesso.')

        if modo_atual == 'departamento':
            return redirect('pv_drive_pasta', alvo_id=pasta_mae.departamento.id, pasta_id=pasta_mae.id)
        else:
            return redirect('pv_drive_pessoal_pasta', pasta_id=pasta_mae.id)

    return redirect('pv_drive_home')

@login_required
def upload_drive(request):
    if request.method == 'POST':
        modo_atual = request.POST.get('modo_atual')
        pasta_id = request.POST.get('parent_id')
        arquivos = request.FILES.getlist('arquivos')

        if not pasta_id:
            messages.error(request, 'Erro: Pasta de destino não identificada.')
            return redirect('pv_drive_home')

        pasta_mae = get_object_or_404(PastaVirtual, id=pasta_id)
        if pasta_mae.tipo_pasta == 'compartilhados':
            messages.error(request, 'Você não pode fazer upload aqui.')
            return redirect('pv_drive_home')

        service = get_drive_service()

        for arquivo in arquivos:
            import hashlib
            hasher = hashlib.sha256()
            for chunk in arquivo.chunks():
                hasher.update(chunk)

            ext = arquivo.name.split('.')[-1] if '.' in arquivo.name else ''
            gdrive_file_id = None
            gdrive_url = None

            if service and pasta_mae.gdrive_folder_id:
                try:
                    file_metadata = {
                        'name': arquivo.name,
                        'parents': [pasta_mae.gdrive_folder_id]
                    }
                    mime_type, _ = mimetypes.guess_type(arquivo.name)
                    media = MediaIoBaseUpload(arquivo.file, mimetype=mime_type or 'application/octet-stream', resumable=True)
                    file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink', supportsAllDrives=True).execute()

                    gdrive_file_id = file.get('id')
                    gdrive_url = file.get('webViewLink')
                except Exception as e:
                    messages.error(request, f'Falha GDrive ({arquivo.name}): {e}')

            ArquivoMidia.objects.create(
                titulo=arquivo.name,
                departamento=pasta_mae.departamento,
                dono_membro=pasta_mae.dono_membro,
                pasta=pasta_mae,
                enviado_por=request.user,
                tamanho_bytes=arquivo.size,
                extensao=ext.lower(),
                hash_sha256=hasher.hexdigest(),
                gdrive_file_id=gdrive_file_id,
                gdrive_url=gdrive_url
            )

        messages.success(request, f'{len(arquivos)} arquivo(s) enviado(s).')

        if modo_atual == 'departamento':
            return redirect('pv_drive_pasta', alvo_id=pasta_mae.departamento.id, pasta_id=pasta_mae.id)
        else:
            return redirect('pv_drive_pessoal_pasta', pasta_id=pasta_mae.id)

    return redirect('pv_drive_home')

@login_required
def visualizar_arquivo(request, arquivo_id):
    arquivo = get_object_or_404(ArquivoMidia, id=arquivo_id, is_excluido=False)

    if not arquivo.gdrive_file_id:
        if arquivo.arquivo:
            return redirect(arquivo.arquivo.url)
        messages.error(request, "Arquivo não encontrado no Google Drive.")
        return redirect('pv_drive_home')

    service = get_drive_service()
    try:
        req = service.files().get_media(fileId=arquivo.gdrive_file_id, supportsAllDrives=True)
        file_content = req.execute()

        mime_type, _ = mimetypes.guess_type(arquivo.titulo)
        response = HttpResponse(file_content, content_type=mime_type or 'application/octet-stream')
        response['Content-Disposition'] = f'inline; filename="{arquivo.titulo}"'
        return response
    except Exception as e:
        messages.error(request, f"Erro ao acessar arquivo: {e}")
        return redirect('pv_drive_home')

@login_required
def baixar_arquivo(request, arquivo_id):
    arquivo = get_object_or_404(ArquivoMidia, id=arquivo_id, is_excluido=False)

    if not arquivo.gdrive_file_id:
        if arquivo.arquivo:
            response = HttpResponse(arquivo.arquivo.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{arquivo.titulo}"'
            return response
        messages.error(request, "Arquivo não encontrado.")
        return redirect('pv_drive_home')

    service = get_drive_service()
    try:
        req = service.files().get_media(fileId=arquivo.gdrive_file_id, supportsAllDrives=True)
        file_content = req.execute()

        mime_type, _ = mimetypes.guess_type(arquivo.titulo)
        response = HttpResponse(file_content, content_type=mime_type or 'application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{arquivo.titulo}"'
        return response
    except Exception as e:
        messages.error(request, f"Erro ao baixar arquivo: {e}")
        return redirect('pv_drive_home')

import zipfile
import io
from django.http import HttpResponse

@login_required
def download_pasta_zip(request, pasta_id):
    if not (request.user.nivel_hierarquico in ['super_admin', 'pastor_regente', 'pastor', 'lider']):
        messages.error(request, 'Acesso restrito.')
        return redirect('dashboard')

    pasta = get_object_or_404(PastaVirtual, id=pasta_id, is_excluida=False)

    # Validar se o usuário tem acesso ao departamento da pasta
    if request.user.nivel_hierarquico not in ['super_admin', 'pastor_regente']:
        deps_permitidos = (request.user.departamentos_liderados.all() | request.user.departamentos_subliderados.all()).distinct()
        if pasta.departamento not in deps_permitidos:
            messages.error(request, 'Você não tem acesso a esta pasta.')
            return redirect('dashboard')

    # Criar um arquivo zip em memória
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        arquivos = ArquivoMidia.objects.filter(pasta=pasta, is_excluido=False)
        for arq in arquivos:
            if arq.arquivo and hasattr(arq.arquivo, 'path'):
                import os
                if os.path.exists(arq.arquivo.path):
                    zip_file.write(arq.arquivo.path, arcname=arq.arquivo.name.split('/')[-1])

    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{pasta.nome}_backup.zip"'
    return response

@login_required
def pv_drive_lixeira(request):
    if not (request.user.nivel_hierarquico in ['super_admin', 'pastor_regente', 'pastor', 'lider']):
        return redirect('dashboard')

    if request.user.nivel_hierarquico in ['super_admin', 'pastor_regente']:
        departamentos = Departamento.objects.all()
    else:
        departamentos = (request.user.departamentos_liderados.all() | request.user.departamentos_subliderados.all()).distinct()

    arquivos = ArquivoMidia.objects.filter(departamento__in=departamentos, is_excluido=True).order_by('-data_exclusao')

    return render(request, 'midia_lgpd/pv_drive_lixeira.html', {
        'arquivos': arquivos
    })

@login_required
def restaurar_arquivo(request, arquivo_id):
    if request.method == 'POST':
        arq = get_object_or_404(ArquivoMidia, id=arquivo_id)
        arq.is_excluido = False
        arq.data_exclusao = None
        arq.save()
        messages.success(request, 'Arquivo restaurado.')
    return redirect('pv_drive_lixeira')

from .models import PermissaoPVDrive
from django.utils.dateparse import parse_datetime

@login_required
def compartilhar_pasta(request, pasta_id):
    if request.method == 'POST':
        pasta = get_object_or_404(PastaVirtual, id=pasta_id, is_excluida=False)

        if request.user.nivel_hierarquico not in ['super_admin', 'pastor_regente'] and pasta.dono_membro != request.user and pasta.criado_por != request.user:
            messages.error(request, "Você não tem permissão para compartilhar esta pasta.")
            return redirect('pv_drive_home')

        tipo_alvo = request.POST.get('tipo_alvo')
        alvo_id = request.POST.get('alvo_id')
        nivel = request.POST.get('nivel', 'leitor')
        validade_str = request.POST.get('validade')

        validade = None
        if validade_str:
            validade = parse_datetime(validade_str)

        service = get_drive_service()
        pasta_compartilhados = None

        if tipo_alvo == 'departamento':
            alvo = get_object_or_404(Departamento, id=alvo_id)
            PermissaoPVDrive.objects.create(
                pasta=pasta, alvo_departamento=alvo, nivel=nivel,
                concedido_por=request.user, validade=validade
            )
            pasta_compartilhados = PastaVirtual.objects.filter(tipo_pasta='compartilhados', departamento=alvo).first()
            msg = f"Pasta compartilhada com o departamento {alvo.nome}."
        elif tipo_alvo == 'membro':
            from core.models import Membro
            alvo = get_object_or_404(Membro, id=alvo_id)
            PermissaoPVDrive.objects.create(
                pasta=pasta, alvo_membro=alvo, nivel=nivel,
                concedido_por=request.user, validade=validade
            )
            pasta_compartilhados = PastaVirtual.objects.filter(tipo_pasta='compartilhados', dono_membro=alvo).first()
            msg = f"Pasta compartilhada com {alvo.get_full_name()}."

        # Cria atalho no GDrive dentro de Compartilhados Comigo
        if pasta_compartilhados and pasta_compartilhados.gdrive_folder_id and pasta.gdrive_folder_id:
            try:
                shortcut_metadata = {
                    'name': pasta.nome,
                    'mimeType': 'application/vnd.google-apps.shortcut',
                    'shortcutDetails': {
                        'targetId': pasta.gdrive_folder_id
                    },
                    'parents': [pasta_compartilhados.gdrive_folder_id]
                }
                service.files().create(body=shortcut_metadata, fields='id', supportsAllDrives=True).execute()
            except Exception as e:
                print(f"Erro ao criar atalho no gdrive: {e}")

        messages.success(request, msg)
        return redirect('pv_drive_home')

    return redirect('pv_drive_home')
