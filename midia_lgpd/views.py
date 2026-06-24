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
from django.contrib.auth.decorators import login_required
from permissoes.decorators import requer_permissao
from django.contrib import messages
from django.utils import timezone
from .models import TermoLGPD, AssinaturaLGPD, ArquivoMidia, PastaVirtual, CompartilhamentoPasta, PermissaoPVDrive
from gestao_membros.models import Departamento
import json

# Serviço de Nuvem e E-mail
from intranet.services.google_drive import upload_arquivo_drive
from intranet.services.gmail_service import enviar_email_html
from intranet.services.whatsapp_service import enviar_whatsapp_template

def is_super_admin(user):
    return user.nivel_hierarquico == 'super_admin' or user.is_superuser

@login_required
@requer_permissao('midia', 'ver')
def ler_assinar_termo(request):
    termo_ativo = TermoLGPD.objects.filter(tipo='membro', is_ativo=True).first()

    if not termo_ativo:
        messages.warning(request, 'Nenhum termo ativo para membros configurado no sistema no momento.')
        return redirect('dashboard')

    ja_assinou = RegistroAceiteLGPD.objects.filter(membro=request.user, status='aceito', termo=termo_ativo).exists()

    if request.method == 'POST' and not ja_assinou:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        user_agent = request.META.get('HTTP_USER_AGENT', 'Intranet IPVE')
        data_atual = timezone.now()

        historico = [{
            'data': data_atual.isoformat(),
            'acao': 'aceito',
            'ip': ip,
            'user_agent': user_agent
        }]

        registro = RegistroAceiteLGPD.objects.create(
            membro=request.user,
            nome_completo=request.user.get_full_name() or request.user.username,
            email=request.user.email,
            cpf=request.user.cpf,
            termo=termo_ativo,
            status='aceito',
            data_resposta=data_atual,
            ip_registro=ip,
            user_agent=user_agent,
            historico_alteracoes=historico
        )

        # Gerar PDF via xhtml2pdf
        from django.template.loader import render_to_string
        from xhtml2pdf import pisa
        import io
        from django.core.files.base import ContentFile

        template_path = 'midia_lgpd/pdfs/termo_assinado.html'
        texto_termo = termo_ativo.conteudo_juridico
        texto_termo = texto_termo.replace('{{ NOME }}', registro.nome_completo)
        texto_termo = texto_termo.replace('{{ CPF }}', registro.cpf or 'NÃO INFORMADO')
        texto_termo = texto_termo.replace('{{ NOME_CRIANCA }}', '')
        texto_termo = texto_termo.replace('{{ DATA }}', registro.data_resposta.strftime('%d/%m/%Y às %H:%M'))

        context = {'registro': registro, 'texto_termo': texto_termo}
        html = render_to_string(template_path, context)

        result = io.BytesIO()
        pdf = pisa.pisaDocument(io.BytesIO(html.encode("utf-8")), result)
        if not pdf.err:
            registro.arquivo_pdf.save(f'aceite_lgpd_{registro.id}.pdf', ContentFile(result.getvalue()))
            pdf_bytes = result.getvalue()
        else:
            pdf_bytes = None
        registro.save()

        # Integração PV Drive (Regra 4)
        if registro.arquivo_pdf:
            from midia_lgpd.models import PastaVirtual, ArquivoMidia
            pasta_destino, _ = PastaVirtual.objects.get_or_create(
                dono_membro=request.user,
                tipo_pasta='usuario',
                defaults={'nome': f'Pasta de {request.user.get_full_name()}', 'is_sistema': True}
            )
            ArquivoMidia.objects.create(
                titulo=f'Comprovante LGPD - Aceito - {registro.nome_completo}',
                arquivo=registro.arquivo_pdf,
                pasta=pasta_destino,
                dono_membro=request.user,
                tamanho_bytes=registro.arquivo_pdf.size,
                extensao='pdf'
            )

        if pdf_bytes:
            enviar_email_html(
                destinatario=request.user.email,
                assunto="Cópia - Termo LGPD Assinado com Sucesso",
                template_name="generico.html",
                context={
                    'content': f"<h2 style='color:#14532d;'>Obrigado, {request.user.first_name}!</h2><p>Confirmamos o aceite digital do termo: <strong>{termo_ativo.titulo}</strong>.</p><p>Segue em anexo a via assinada do seu termo para sua segurança.</p>"
                },
                anexos=[(f"Termo_LGPD_{request.user.first_name}.pdf", pdf_bytes, 'application/pdf')]
            )

        messages.success(request, 'Obrigado! O Termo de Uso de Imagem e LGPD foi assinado digitalmente. Uma cópia em PDF foi enviada para o seu e-mail e salva no seu Drive Pessoal.')
        return redirect('dashboard')

    return render(request, 'midia_lgpd/termo_aceite.html', {
        'termo': termo_ativo,
        'ja_assinou': ja_assinou
    })

import json

@login_required
@requer_permissao('midia', 'ver')
def portal_lgpd(request):
    # Encontrar a assinatura atual
    assinatura = RegistroAceiteLGPD.objects.filter(membro=request.user, status='aceito').order_by('-data_resposta').first()
    return render(request, 'midia_lgpd/portal_lgpd.html', {
        'assinatura': assinatura
    })

@login_required
@requer_permissao('midia', 'ver')
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
        'habilidades': list(user.habilidades.values_list('nome', flat=True)) if hasattr(user, 'habilidades') and hasattr(user.habilidades, 'all') else [],
        'data_cadastro': str(user.date_joined),
        'historico_escalas': list(user.escalas_individuais.values('id', 'data_escala', 'horario_inicio', 'funcao_alocada__nome')),
    }
    json_data = json.dumps(dados, indent=4, ensure_ascii=False)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('meus_dados.json', json_data.encode('utf-8'))

    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="MeusDados_PVEnseada.zip"'
    return response

@login_required
@requer_permissao('midia', 'ver')
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
@requer_permissao('midia', 'excluir')
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
@requer_permissao('midia', 'excluir')
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
@requer_permissao('midia', 'ver')
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
        if pasta_raiz:
            PastaVirtual.objects.get_or_create(
                tipo_pasta='compartilhados',
                departamento=dep_atual,
                defaults={'nome': 'Compartilhados Comigo', 'is_sistema': True, 'parent': pasta_raiz}
            )
    else:
        # Pessoal
        modo = 'pessoal'
        pasta_raiz = PastaVirtual.objects.filter(tipo_pasta='usuario', dono_membro=request.user).first()
        if not pasta_raiz:
            messages.error(request, 'Seu Drive Pessoal ainda não foi gerado pelo sistema.')
            return redirect('dashboard')

        PastaVirtual.objects.get_or_create(
            tipo_pasta='compartilhados',
            dono_membro=request.user,
            defaults={'nome': 'Compartilhados Comigo', 'is_sistema': True, 'parent': pasta_raiz}
        )

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
            from django.db.models import Q
            hoje = timezone.now()
            # Buscar arquivos onde eu tenho Permissao
            if modo == 'departamento':
                # Arquivos compartilhados com meu departamento
                permissoes = PermissaoPVDrive.objects.filter(
                    Q(validade__isnull=True) | Q(validade__gte=hoje),
                    alvo_departamento=dep_atual,
                    is_ativo=True
                )
            else:
                # Arquivos compartilhados comigo
                permissoes = PermissaoPVDrive.objects.filter(
                    Q(validade__isnull=True) | Q(validade__gte=hoje),
                    alvo_membro=request.user,
                    is_ativo=True
                )

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
@requer_permissao('midia', 'ver')
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
@requer_permissao('midia', 'ver')
def renomear_pasta(request, pasta_id):
    pasta = get_object_or_404(PastaVirtual, id=pasta_id)

    if pasta.is_sistema:
        messages.error(request, 'Pastas de sistema não podem ser renomeadas.')
        return redirect('pv_drive_home')

    if request.method == 'POST':
        novo_nome = request.POST.get('nome')
        if novo_nome:
            pasta.nome = novo_nome
            pasta.save()

            # GDrive rename (opcional)
            service = get_drive_service()
            if service and pasta.gdrive_folder_id:
                try:
                    service.files().update(fileId=pasta.gdrive_folder_id, body={'name': novo_nome}, supportsAllDrives=True).execute()
                except Exception as e:
                    print(f"GDrive rename erro: {e}")

            messages.success(request, 'Pasta renomeada com sucesso.')

    if pasta.departamento:
        return redirect('pv_drive_pasta', alvo_id=pasta.departamento.id, pasta_id=pasta.parent.id if pasta.parent else pasta.id)
    else:
        return redirect('pv_drive_pessoal_pasta', pasta_id=pasta.parent.id if pasta.parent else pasta.id)

@login_required
@requer_permissao('midia', 'ver')
def excluir_pasta(request, pasta_id):
    pasta = get_object_or_404(PastaVirtual, id=pasta_id)

    if pasta.is_sistema:
        messages.error(request, 'Pastas de sistema não podem ser excluídas.')
        return redirect('pv_drive_home')

    if request.method == 'POST':
        # GDrive delete (opcional)
        service = get_drive_service()
        if service and pasta.gdrive_folder_id:
            try:
                service.files().update(fileId=pasta.gdrive_folder_id, body={'trashed': True}, supportsAllDrives=True).execute()
            except Exception as e:
                print(f"GDrive delete erro: {e}")

        pasta.is_excluida = True
        pasta.data_exclusao = timezone.now()
        pasta.save()
        messages.success(request, 'Pasta movida para a lixeira.')

    if pasta.departamento:
        return redirect('pv_drive_pasta', alvo_id=pasta.departamento.id, pasta_id=pasta.parent.id if pasta.parent else pasta.id)
    else:
        return redirect('pv_drive_pessoal_pasta', pasta_id=pasta.parent.id if pasta.parent else pasta.id)

@login_required
@requer_permissao('midia', 'ver')
def renomear_arquivo(request, arquivo_id):
    arquivo = get_object_or_404(ArquivoMidia, id=arquivo_id, is_excluido=False)

    if request.method == 'POST':
        novo_nome = request.POST.get('titulo')
        if novo_nome:
            arquivo.titulo = novo_nome
            arquivo.save()

            # GDrive rename (opcional)
            service = get_drive_service()
            if service and arquivo.gdrive_file_id:
                try:
                    service.files().update(fileId=arquivo.gdrive_file_id, body={'name': novo_nome}, supportsAllDrives=True).execute()
                except Exception as e:
                    print(f"GDrive file rename erro: {e}")

            messages.success(request, 'Arquivo renomeado com sucesso.')

    if arquivo.pasta:
        if arquivo.pasta.departamento:
            return redirect('pv_drive_pasta', alvo_id=arquivo.pasta.departamento.id, pasta_id=arquivo.pasta.id)
        else:
            return redirect('pv_drive_pessoal_pasta', pasta_id=arquivo.pasta.id)
    return redirect('pv_drive_home')

@login_required
@requer_permissao('midia', 'ver')
def excluir_arquivo(request, arquivo_id):
    arquivo = get_object_or_404(ArquivoMidia, id=arquivo_id, is_excluido=False)

    if request.method == 'POST':
        # GDrive delete (opcional)
        service = get_drive_service()
        if service and arquivo.gdrive_file_id:
            try:
                service.files().update(fileId=arquivo.gdrive_file_id, body={'trashed': True}, supportsAllDrives=True).execute()
            except Exception as e:
                print(f"GDrive file delete erro: {e}")

        arquivo.is_excluido = True
        arquivo.save()
        messages.success(request, 'Arquivo movido para a lixeira.')

    if arquivo.pasta:
        if arquivo.pasta.departamento:
            return redirect('pv_drive_pasta', alvo_id=arquivo.pasta.departamento.id, pasta_id=arquivo.pasta.id)
        else:
            return redirect('pv_drive_pessoal_pasta', pasta_id=arquivo.pasta.id)
    return redirect('pv_drive_home')

@login_required
@requer_permissao('midia', 'ver')
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
def check_arquivo_acesso(request, arquivo):
    user = request.user
    if is_super_admin(user): return True
    if arquivo.dono_membro == user: return True

    deptos_usuario = (user.departamentos_liderados.all() | user.departamentos_subliderados.all()).distinct()
    if arquivo.departamento in deptos_usuario: return True

    hoje = timezone.now()
    from django.db.models import Q
    permissoes = PermissaoPVDrive.objects.filter(
        arquivo=arquivo, is_ativo=True
    ).filter(
        Q(validade__isnull=True) | Q(validade__gte=hoje)
    )
    for p in permissoes:
        if p.alvo_membro == user or p.alvo_departamento in deptos_usuario:
            if p.senha_acesso:
                if request.session.get(f'acesso_liberado_{p.id}'):
                    return p
                else:
                    return p.id # Precisa de senha
            return p

    p_pasta = arquivo.pasta
    while p_pasta:
        permissoes_pasta = PermissaoPVDrive.objects.filter(
            pasta=p_pasta, is_ativo=True
        ).filter(
            Q(validade__isnull=True) | Q(validade__gte=hoje)
        )
        for p in permissoes_pasta:
            if p.alvo_membro == user or p.alvo_departamento in deptos_usuario:
                return p
        p_pasta = p_pasta.parent

    return False

from django.views.decorators.clickjacking import xframe_options_sameorigin

@login_required
@requer_permissao('midia', 'ver')
@xframe_options_sameorigin
def visualizar_arquivo(request, arquivo_id):
    arquivo = get_object_or_404(ArquivoMidia, id=arquivo_id, is_excluido=False)

    acesso = check_arquivo_acesso(request, arquivo)
    if acesso is False:
        messages.error(request, "Você não tem permissão para acessar este arquivo.")
        return redirect('pv_drive_home')
    elif type(acesso) == int:
        return redirect('acesso_protegido_senha', permissao_id=acesso)

    if not arquivo.gdrive_file_id:
        if arquivo.arquivo:
            return redirect(arquivo.arquivo.url)
        messages.error(request, "Arquivo não encontrado no Google Drive.")
        return redirect('pv_drive_home')

    service = get_drive_service()
    try:
        req = service.files().get_media(fileId=arquivo.gdrive_file_id, supportsAllDrives=True)
        file_content = req.execute()

        # Secesso garantido. Autodestruir se aplicável
        if type(acesso) != bool and acesso.is_autodestruir:
            acesso.foi_acessado = True
            acesso.is_ativo = False
            acesso.save()

        mime_type, _ = mimetypes.guess_type(arquivo.titulo)
        response = HttpResponse(file_content, content_type=mime_type or 'application/octet-stream')
        response['Content-Disposition'] = f'inline; filename="{arquivo.titulo}"'
        return response
    except Exception as e:
        messages.error(request, f"Erro ao acessar arquivo: {e}")
        return redirect('pv_drive_home')

@login_required
@requer_permissao('midia', 'ver')
def baixar_arquivo(request, arquivo_id):
    arquivo = get_object_or_404(ArquivoMidia, id=arquivo_id, is_excluido=False)

    acesso = check_arquivo_acesso(request, arquivo)
    if acesso is False:
        messages.error(request, "Você não tem permissão para baixar este arquivo.")
        return redirect('pv_drive_home')
    elif type(acesso) == int:
        return redirect('acesso_protegido_senha', permissao_id=acesso)

    if not arquivo.gdrive_file_id:
        if arquivo.arquivo:
            response = HttpResponse(arquivo.arquivo.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{arquivo.titulo}"'

            # Secesso garantido. Autodestruir se aplicável
            if type(acesso) != bool and acesso.is_autodestruir:
                acesso.foi_acessado = True
                acesso.is_ativo = False
                acesso.save()

            return response
        messages.error(request, "Arquivo não encontrado.")
        return redirect('pv_drive_home')

    service = get_drive_service()
    try:
        req = service.files().get_media(fileId=arquivo.gdrive_file_id, supportsAllDrives=True)
        file_content = req.execute()

        # Secesso garantido. Autodestruir se aplicável
        if type(acesso) != bool and acesso.is_autodestruir:
            acesso.foi_acessado = True
            acesso.is_ativo = False
            acesso.save()

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
@requer_permissao('midia', 'ver')
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
@requer_permissao('midia', 'ver')
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
@requer_permissao('midia', 'ver')
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
@requer_permissao('midia', 'ver')
def processar_compartilhamento(request):
    if request.method == 'POST':
        item_tipo = request.POST.get('item_tipo') # 'pasta' ou 'arquivo'
        item_id = request.POST.get('item_id')
        tipo_alvo = request.POST.get('tipo_alvo')
        alvo_id = request.POST.get('alvo_id')
        nivel = request.POST.get('nivel', 'leitor')
        validade_str = request.POST.get('validade')
        senha = request.POST.get('senha')
        is_autodestruir = request.POST.get('is_autodestruir') == 'on'

        validade = parse_datetime(validade_str) if validade_str else None

        pasta = None
        arquivo = None
        nome_item = ""

        if item_tipo == 'pasta':
            pasta = get_object_or_404(PastaVirtual, id=item_id, is_excluida=False)
            if request.user.nivel_hierarquico not in ['super_admin', 'pastor_regente'] and pasta.dono_membro != request.user and pasta.criado_por != request.user:
                messages.error(request, "Você não tem permissão para compartilhar esta pasta.")
                return redirect('pv_drive_home')
            nome_item = pasta.nome
        else:
            arquivo = get_object_or_404(ArquivoMidia, id=item_id, is_excluido=False)
            if request.user.nivel_hierarquico not in ['super_admin', 'pastor_regente'] and arquivo.dono_membro != request.user and arquivo.enviado_por != request.user:
                messages.error(request, "Você não tem permissão para compartilhar este arquivo.")
                return redirect('pv_drive_home')
            nome_item = arquivo.titulo

        if tipo_alvo == 'departamento':
            alvo = get_object_or_404(Departamento, id=alvo_id)
            permissao = PermissaoPVDrive.objects.create(
                pasta=pasta, arquivo=arquivo, alvo_departamento=alvo, nivel=nivel,
                concedido_por=request.user, validade=validade,
                senha_acesso=senha, is_autodestruir=is_autodestruir
            )
            msg = f"Item compartilhado com o departamento {alvo.nome}."
            pasta_compartilhados = PastaVirtual.objects.filter(tipo_pasta='compartilhados', departamento=alvo).first()
        elif tipo_alvo == 'membro':
            from core.models import Membro
            alvo = get_object_or_404(Membro, id=alvo_id)
            permissao = PermissaoPVDrive.objects.create(
                pasta=pasta, arquivo=arquivo, alvo_membro=alvo, nivel=nivel,
                concedido_por=request.user, validade=validade,
                senha_acesso=senha, is_autodestruir=is_autodestruir
            )
            msg = f"Item compartilhado com {alvo.get_full_name()}."
            pasta_compartilhados = PastaVirtual.objects.filter(tipo_pasta='compartilhados', dono_membro=alvo).first()

            if senha:
                # Enviar senha por e-mail para o membro
                enviar_email_html(
                    destinatario=alvo.email,
                    assunto="Chave de Acesso - Arquivo Compartilhado",
                    template_name="generico.html",
                    context={
                        'content': f"<h2 style='color:#1d4ed8;'>Arquivo Protegido no PV Drive</h2><p>O usuário <b>{request.user.first_name}</b> compartilhou o item <b>{nome_item}</b> com você.</p><p>A senha para acessá-lo é: <strong style='font-size:20px; color:#b91c1c;'>{senha}</strong></p><p>Acesse a aba 'Compartilhados Comigo' no PV Drive para desbloquear.</p>"
                    }
                )
                from intranet.services.whatsapp_service import enviar_whatsapp_template
                if getattr(alvo, 'telefone', None):
                    enviar_whatsapp_template(alvo.telefone, 'pvdrive_senha_compartilhamento.txt', {'nome_item': nome_item, 'senha': senha, 'remetente': request.user.first_name})

        # Restaurando: Cria atalho no GDrive dentro de Compartilhados Comigo
        if pasta_compartilhados and pasta_compartilhados.gdrive_folder_id:
            service = get_drive_service()
            if service:
                gdrive_target = None
                if pasta and pasta.gdrive_folder_id:
                    gdrive_target = pasta.gdrive_folder_id
                elif arquivo and arquivo.gdrive_file_id:
                    gdrive_target = arquivo.gdrive_file_id

                if gdrive_target:
                    try:
                        shortcut_metadata = {
                            'name': nome_item,
                            'mimeType': 'application/vnd.google-apps.shortcut',
                            'shortcutDetails': {
                                'targetId': gdrive_target
                            },
                            'parents': [pasta_compartilhados.gdrive_folder_id]
                        }
                        service.files().create(body=shortcut_metadata, fields='id', supportsAllDrives=True).execute()
                    except Exception as e:
                        print(f"Erro ao criar atalho no gdrive: {e}")

        messages.success(request, msg)
        return redirect('pv_drive_home')
    return redirect('pv_drive_home')

@login_required
@requer_permissao('midia', 'ver')
def meus_compartilhamentos(request):
    permissoes = PermissaoPVDrive.objects.filter(concedido_por=request.user).order_by('-data_concessao')

    q = request.GET.get('q', '').strip()
    if q:
        from django.db.models import Q
        permissoes = permissoes.filter(
            Q(pasta__nome__icontains=q) |
            Q(arquivo__titulo__icontains=q) |
            Q(alvo_membro__first_name__icontains=q) |
            Q(alvo_departamento__nome__icontains=q)
        )

    return render(request, 'midia_lgpd/meus_compartilhamentos.html', {
        'permissoes': permissoes,
        'q': q
    })

@login_required
@requer_permissao('midia', 'ver')
def acesso_protegido_senha(request, permissao_id):
    permissao = get_object_or_404(PermissaoPVDrive, id=permissao_id, is_ativo=True)

    # Validar se o usuario tem direito a essa permissao (alvo)
    tem_acesso = False
    if permissao.alvo_membro == request.user:
        tem_acesso = True
    elif permissao.alvo_departamento:
        deptos_usuario = (request.user.departamentos_liderados.all() | request.user.departamentos_subliderados.all()).distinct()
        if permissao.alvo_departamento in deptos_usuario:
            tem_acesso = True

    if not tem_acesso and not is_super_admin(request.user):
        messages.error(request, 'Você não tem acesso a este compartilhamento.')
        return redirect('pv_drive_home')

    if request.method == 'POST':
        senha_digitada = request.POST.get('senha')
        if senha_digitada == permissao.senha_acesso:
            # Senha Correta! Libera a sessão para as próximas views baixarem o arquivo de fato
            request.session[f'acesso_liberado_{permissao.id}'] = True

            if permissao.arquivo:
                return redirect('baixar_arquivo', arquivo_id=permissao.arquivo.id)
            elif permissao.pasta:
                return redirect('pv_drive_home')
        else:
            messages.error(request, 'Senha incorreta!')

    return render(request, 'midia_lgpd/acesso_protegido.html', {
        'permissao': permissao
    })

from intranet.services.groq_ai import analisar_documento_para_roteamento
from thefuzz import process
from core.models import Membro, NotificacaoGlobal
import mimetypes

@login_required
@requer_permissao('midia', 'ver')
def upload_inteligente_ocr(request):
    if request.method == 'POST':
        arquivo = request.FILES.get('arquivo_ia')
        if not arquivo:
            messages.error(request, 'Nenhum arquivo enviado para a IA.')
            return redirect('pv_drive_home')

        # 1. Acionar Groq para extrair dados
        messages.info(request, 'A IA está lendo o documento, aguarde...')
        dados_ia = analisar_documento_para_roteamento(arquivo)

        if not dados_ia:
            messages.error(request, 'A Inteligência Artificial falhou em ler este documento. Faça o upload manual.')
            return redirect('pv_drive_home')

        dept_nome = dados_ia.get('departamento_sugerido', 'Geral')
        titulo = dados_ia.get('titulo_sugerido', arquivo.name)
        resumo = dados_ia.get('resumo', '')

        # 2. Fuzzy Matching para encontrar o Departamento
        departamentos_all = Departamento.objects.all()
        nomes_deptos = {d.id: d.nome for d in departamentos_all}
        best_match = process.extractOne(dept_nome, nomes_deptos)

        departamento = None
        if best_match and best_match[1] >= 50:
            departamento = Departamento.objects.get(id=best_match[2])

        if not departamento:
            messages.warning(request, f'IA sugeriu departamento "{dept_nome}" mas não encontramos. Salvo na sua raiz.')
            pasta_destino, _ = PastaVirtual.objects.get_or_create(
                nome='Meus Uploads Inteligentes',
                dono_membro=request.user,
                tipo_pasta='usuario',
                defaults={'is_sistema': True}
            )
        else:
            # Encontrar a pasta Raiz do Departamento
            pasta_destino = PastaVirtual.objects.filter(departamento=departamento, tipo_pasta='departamento', parent__isnull=True).first()
            if not pasta_destino:
                pasta_destino = PastaVirtual.objects.create(
                    nome=departamento.nome,
                    departamento=departamento,
                    tipo_pasta='departamento',
                    is_sistema=True
                )

        # 3. Upload para Google Drive (se configurado)
        service = get_drive_service()
        gdrive_file_id = None
        gdrive_url = None

        if service and pasta_destino.gdrive_folder_id:
            try:
                import hashlib
                from googleapiclient.http import MediaIoBaseUpload

                # Reset file pointer after pdfplumber read it
                arquivo.seek(0)

                file_metadata = {
                    'name': arquivo.name, # Mantem o nome original como pedido pelo usuario
                    'parents': [pasta_destino.gdrive_folder_id]
                }
                mime_type, _ = mimetypes.guess_type(arquivo.name)
                media = MediaIoBaseUpload(arquivo.file, mimetype=mime_type or 'application/octet-stream', resumable=True)
                file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink', supportsAllDrives=True).execute()

                gdrive_file_id = file.get('id')
                gdrive_url = file.get('webViewLink')
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Upload IA Falhou GDrive: {e}")

        # 4. Criar ArquivoMidia
        novo_arquivo = ArquivoMidia.objects.create(
            titulo=arquivo.name,
            departamento=departamento,
            dono_membro=request.user if not departamento else None,
            pasta=pasta_destino,
            enviado_por=request.user,
            tamanho_bytes=arquivo.size,
            extensao=arquivo.name.split('.')[-1] if '.' in arquivo.name else '',
            gdrive_file_id=gdrive_file_id,
            gdrive_url=gdrive_url
        )

        # 5. Notificar Líderes do Departamento
        if departamento:
            lideres = Membro.objects.filter(departamentos_liderados=departamento, is_active=True)
            from core.utils_notifications import enviar_notificacao_real_time
            for lider in lideres:
                enviar_notificacao_real_time(
                    usuario=lider,
                    titulo=f"Novo Upload Inteligente: {departamento.nome}",
                    mensagem=f"A IA roteou o arquivo '{titulo}' para seu departamento. Resumo: {resumo}",
                    link_acao=f"/drive/dep/{departamento.id}/"
                )

        messages.success(request, f'🤖 Mágica feita! Arquivo classificado pela IA como "{titulo}" e roteado para a pasta {pasta_destino.nome}.')
        return redirect('pv_drive_home')

    return redirect('pv_drive_home')

@login_required
@requer_permissao('midia', 'ver')
def cancelar_compartilhamento(request, permissao_id):
    try:
        permissao = PermissaoPVDrive.objects.get(id=permissao_id)
    except PermissaoPVDrive.DoesNotExist:
        messages.error(request, f'O compartilhamento com ID {permissao_id} não foi encontrado ou já foi cancelado.')
        return redirect('pv_drive_home')

    # Valida se o usuário pode cancelar (é o dono da pasta, o criador original ou admin)
    if not (request.user.nivel_hierarquico in ['super_admin', 'pastor_regente'] or
            permissao.pasta.dono_membro == request.user or
            permissao.concedido_por == request.user):
        messages.error(request, "Você não tem autorização para cancelar este compartilhamento.")
        return redirect('pv_drive_home')

    permissao.is_ativo = False
    permissao.save()

    # Remover shortcut no GDrive poderia ser feito aqui caso o sistema estivesse com permissões completas, mas por agora inativar já remove da listagem.

    messages.success(request, "Compartilhamento cancelado com sucesso.")

    # Retorna para a mesma view que o usuario estava
    modo = 'pessoal'
    if permissao.pasta.departamento:
        modo = 'departamento'
        return redirect('pv_drive_pasta', alvo_id=permissao.pasta.departamento.id, pasta_id=permissao.pasta.id)
    else:
        return redirect('pv_drive_pessoal_pasta', pasta_id=permissao.pasta.id)


# ==========================================
# NOVAS VIEWS LGPD V2 (COMPLIANCE E TERMOS)
# ==========================================
from .models import RegistroAceiteLGPD
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse
import urllib.parse
import io
from xhtml2pdf import pisa

@login_required
@requer_permissao('midia', 'ver')
def painel_lgpd_dashboard(request):
    from gestao_membros.models import Membro

    total_aceites = RegistroAceiteLGPD.objects.filter(status='aceito').count()

    # Gente faltando dar aceite = (Pendentes solicitados) + (Membros Ativos que não assinaram)
    membros_que_assinaram = RegistroAceiteLGPD.objects.filter(membro__isnull=False, status='aceito').values_list('membro_id', flat=True)
    membros_pendentes_count = Membro.objects.filter(is_active=True).exclude(id__in=membros_que_assinaram).count()
    solicitacoes_pendentes_count = RegistroAceiteLGPD.objects.filter(status='pendente').count()
    total_pendentes = membros_pendentes_count + solicitacoes_pendentes_count

    termo_membro = TermoLGPD.objects.filter(tipo='membro', is_ativo=True).first()
    termo_visitante = TermoLGPD.objects.filter(tipo='visitante', is_ativo=True).first()
    termo_crianca = TermoLGPD.objects.filter(tipo='crianca', is_ativo=True).first()

    pesquisa = request.GET.get('q', '')
    historico = RegistroAceiteLGPD.objects.all()
    if pesquisa:
        historico = historico.filter(Q(nome_completo__icontains=pesquisa) | Q(cpf__icontains=pesquisa))

    return render(request, 'midia_lgpd/painel_dashboard.html', {
        'total_aceites': total_aceites,
        'total_pendentes': total_pendentes,
        'termo_membro': termo_membro,
        'termo_visitante': termo_visitante,
        'termo_crianca': termo_crianca,
        'historico': historico,
        'pesquisa': pesquisa,
        'membros_pendentes_count': membros_pendentes_count
    })

@login_required
@requer_permissao('midia', 'editar')
def enviar_solicitacao_lgpd(request):
    if request.method == 'POST':
        nome = request.POST.get('nome_completo')
        email = request.POST.get('email', '')
        cpf = request.POST.get('cpf', '')
        tipo = request.POST.get('tipo_termo')
        nome_crianca = request.POST.get('nome_crianca', '')

        termo = TermoLGPD.objects.filter(tipo=tipo, is_ativo=True).first()
        if not termo:
            return JsonResponse({'sucesso': False, 'msg': 'Termo base não encontrado.'})

        registro = RegistroAceiteLGPD.objects.create(
            nome_completo=nome,
            email=email,
            cpf=cpf,
            nome_crianca=nome_crianca,
            termo=termo
        )

        link_publico = request.build_absolute_uri(reverse('termo_publico_view', args=[registro.token_acesso]))

        if email:
            try:
                from intranet.services.gmail_service import enviar_email_simples
                assunto = 'Igreja PV Enseada - Solicitação de Consentimento (LGPD)'
                msg = f"Olá {nome},\n\nPor favor, leia e aceite o termo de consentimento de imagem acessando o link:\n{link_publico}"
                enviar_email_simples(email, assunto, msg)
            except:
                pass

        texto_zap = f"Olá {nome}, somos da Mídia da Igreja PV Enseada. Por favor, leia e dê seu aceite no nosso termo de imagem de forma rápida através deste link: {link_publico}"
        zap_url = f"https://wa.me/?text={urllib.parse.quote(texto_zap)}"

        return JsonResponse({
            'sucesso': True,
            'zap_url': zap_url,
            'link_publico': link_publico
        })
    return HttpResponse(status=405)

def termo_publico_view(request, token):
    registro = get_object_or_404(RegistroAceiteLGPD, token_acesso=token)

    texto_termo = registro.termo.conteudo_juridico
    texto_termo = texto_termo.replace('{{ NOME }}', registro.nome_completo)
    texto_termo = texto_termo.replace('{{ CPF }}', registro.cpf or 'NÃO INFORMADO')
    texto_termo = texto_termo.replace('{{ NOME_CRIANCA }}', registro.nome_crianca or '')
    data_atual = timezone.now().strftime('%d/%m/%Y às %H:%M')
    texto_termo = texto_termo.replace('{{ DATA }}', data_atual)

    return render(request, 'midia_lgpd/termo_publico.html', {
        'registro': registro,
        'texto_termo': texto_termo
    })

def processar_aceite_lgpd(request, token):
    registro = get_object_or_404(RegistroAceiteLGPD, token_acesso=token)
    if request.method == 'POST':
        acao = request.POST.get('acao') # 'aceito' ou 'recusado'

        registro.status = acao
        registro.data_resposta = timezone.now()

        # Coleta de metadados
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        registro.ip_registro = ip
        registro.user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Histórico de Auditoria
        if not isinstance(registro.historico_alteracoes, list):
            registro.historico_alteracoes = []
        registro.historico_alteracoes.append({
            'data': registro.data_resposta.isoformat(),
            'acao': acao,
            'ip': ip,
            'user_agent': registro.user_agent
        })

        # Gerar PDF (Sempre gera, mesmo se recusado para termos o comprovante da recusa)
        from django.template.loader import render_to_string
        from xhtml2pdf import pisa
        import io
        template_path = 'midia_lgpd/pdfs/termo_assinado.html'

        texto_termo = registro.termo.conteudo_juridico
        texto_termo = texto_termo.replace('{{ NOME }}', registro.nome_completo)
        texto_termo = texto_termo.replace('{{ CPF }}', registro.cpf or 'NÃO INFORMADO')
        texto_termo = texto_termo.replace('{{ NOME_CRIANCA }}', registro.nome_crianca or '')
        texto_termo = texto_termo.replace('{{ DATA }}', registro.data_resposta.strftime('%d/%m/%Y às %H:%M'))

        if acao == 'recusado':
            texto_termo = "<h1 style='color:red; text-align:center;'>TERMO RECUSADO PELO TITULAR</h1><hr>" + texto_termo

        context = {'registro': registro, 'texto_termo': texto_termo}
        html = render_to_string(template_path, context)

        result = io.BytesIO()
        pdf = pisa.pisaDocument(io.BytesIO(html.encode("utf-8")), result)
        pdf_bytes = None
        if not pdf.err:
            from django.core.files.base import ContentFile
            pdf_bytes = result.getvalue()
            registro.arquivo_pdf.save(f'LGPD_{acao}_{registro.id}.pdf', ContentFile(pdf_bytes))

        registro.save()

        # Integração PV Drive
        from gestao_membros.models import Departamento
        from midia_lgpd.models import PastaVirtual, ArquivoMidia

        if registro.arquivo_pdf:
            if registro.membro:
                # É membro, salvar na raiz do usuário
                pasta_destino, _ = PastaVirtual.objects.get_or_create(
                    dono_membro=registro.membro,
                    tipo_pasta='usuario',
                    defaults={'nome': f'Pasta de {registro.membro.get_full_name()}', 'is_sistema': True}
                )
            else:
                # É visitante, salvar na pasta do Departamento Mídia & LGPD
                depto_midia = Departamento.objects.filter(nome='Mídia & LGPD').first()
                if not depto_midia:
                    depto_midia = Departamento.objects.create(nome='Mídia & LGPD', categoria='departamento')
                pasta_midia_raiz, _ = PastaVirtual.objects.get_or_create(
                    departamento=depto_midia,
                    tipo_pasta='departamento',
                    defaults={'nome': 'Raiz Mídia & LGPD', 'is_sistema': True}
                )
                pasta_destino, _ = PastaVirtual.objects.get_or_create(
                    parent=pasta_midia_raiz,
                    departamento=depto_midia,
                    nome=f'Visitante: {registro.nome_completo}',
                    defaults={'tipo_pasta': 'normal'}
                )

            # Criar ArquivoMidia associado
            ArquivoMidia.objects.create(
                titulo=f'Comprovante LGPD - {acao.capitalize()} - {registro.nome_completo}',
                arquivo=registro.arquivo_pdf,
                pasta=pasta_destino,
                dono_membro=registro.membro,
                tamanho_bytes=registro.arquivo_pdf.size if registro.arquivo_pdf else 0,
                extensao='pdf'
            )

        # Envio de E-mail de Segunda Via
        if registro.email and pdf_bytes:
            from intranet.services.gmail_service import enviar_email_html
            from intranet.services.whatsapp_service import enviar_whatsapp_template
            mensagem = f"Confirmamos a recepção da sua resposta: <strong>{acao.upper()}</strong> para o termo de consentimento.<br>Segue anexo seu comprovante com rastreabilidade digital para seus registros."
            enviar_email_html(
                destinatario=registro.email,
                assunto=f"Comprovante de Termo LGPD - {acao.capitalize()}",
                template_name="generico.html",
                context={'content': f"<h2 style='color:#14532d;'>Olá, {registro.nome_completo}!</h2><p>{mensagem}</p>"},
                anexos=[(f"Termo_LGPD_{registro.nome_completo}_{acao}.pdf", pdf_bytes, 'application/pdf')]
            )
            from intranet.services.whatsapp_service import enviar_whatsapp_template
            if registro.membro and getattr(registro.membro, 'telefone', None):
                enviar_whatsapp_template(registro.membro.telefone, 'lgpd_segunda_via.txt', {'nome': registro.nome_completo})

        messages.success(request, f"Sua resposta ({acao}) foi registrada com sucesso!")
        return redirect('termo_publico_view', token=registro.token_acesso)
    return HttpResponse(status=405)

def baixar_pdf_termo(request, token):
    registro = get_object_or_404(RegistroAceiteLGPD, token_acesso=token)
    if registro.arquivo_pdf:
        response = HttpResponse(registro.arquivo_pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Termo_LGPD_{registro.nome_completo}.pdf"'
        return response
    return HttpResponse("PDF não encontrado ou não gerado.", status=404)
