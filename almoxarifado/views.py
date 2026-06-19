"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: almoxarifado/views.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from permissoes.decorators import requer_permissao
from django.contrib import messages
from django.utils import timezone
from .models import ItemAlmoxarifado, MovimentacaoAlmoxarifado, CategoriaItem
from core.models import Membro, NotificacaoGlobal
from midia_lgpd.models import PastaVirtual, ArquivoMidia
from gestao_membros.models import Departamento
from thefuzz import process
import threading

def get_lideres_almoxarifado():
    return Membro.objects.filter(departamentos_liderados__nome__icontains='almoxarifado')

def notificar_lideres_background(item, movimentacao):
    lideres = get_lideres_almoxarifado()
    acao = "RETIRADO" if movimentacao.tipo == 'retirada' else "DEVOLVIDO/ADICIONADO"
    titulo = f"Aviso Almoxarifado: Item {acao}"

    cond_texto = f" | Condição: {item.get_condicao_fisica_display()}" if item.condicao_fisica else ""
    val_texto = f" | Valor: R$ {item.valor_monetario}" if item.valor_monetario else ""

    mensagem = f"O item '{item.nome}' teve uma {movimentacao.get_tipo_display()} registrada por {movimentacao.nome_digitado}. Qtd: {movimentacao.quantidade}{cond_texto}{val_texto}."

    from core.utils_notifications import enviar_notificacao_real_time
    for lider in lideres:
        enviar_notificacao_real_time(
            usuario=lider,
            titulo=titulo,
            mensagem=mensagem,
            link_acao='/almoxarifado/livro/'
        )

def qr_movimentar_item(request, item_id, tipo):
    item = get_object_or_404(ItemAlmoxarifado, id_unico=item_id)

    if request.method == 'POST':
        nome_digitado = request.POST.get('nome', '').strip()
        qtd_str = request.POST.get('quantidade', '1')
        observacao = request.POST.get('observacao', '').strip()

        try:
            qtd = int(qtd_str)
        except ValueError:
            qtd = 1

        if qtd <= 0:
            messages.error(request, "A quantidade deve ser maior que zero.")
            return redirect('qr_retirar_item' if tipo == 'retirada' else 'qr_devolver_item', item_id=item_id)

        if tipo == 'retirada':
            if qtd > item.quantidade_estoque:
                messages.error(request, f"Estoque insuficiente. Temos apenas {item.quantidade_estoque} un.")
                return redirect('qr_retirar_item', item_id=item_id)

            item.quantidade_estoque -= qtd
            if item.tipo_item == 'permanente':
                item.status_item = 'emprestado'
            elif item.quantidade_estoque == 0:
                item.status_item = 'consumido'

        elif tipo == 'devolucao':
            item.quantidade_estoque += qtd
            if item.tipo_item == 'permanente':
                item.status_item = 'disponivel'

        membro_vinculado = None
        if nome_digitado:
            nomes_db = list(Membro.objects.values_list('first_name', flat=True))
            if nomes_db:
                best_match = process.extractOne(nome_digitado, nomes_db, score_cutoff=85)
                if best_match:
                    membro_vinculado = Membro.objects.filter(first_name=best_match[0]).first()

        item.save()

        mov = MovimentacaoAlmoxarifado.objects.create(
            item=item,
            tipo=tipo,
            quantidade=qtd,
            nome_digitado=nome_digitado,
            membro_vinculado=membro_vinculado,
            observacao=observacao
        )

        threading.Thread(target=notificar_lideres_background, args=(item, mov)).start()
        return render(request, 'almoxarifado/qr_sucesso.html', {'mov': mov})

    return render(request, 'almoxarifado/qr_movimentacao.html', {'item': item, 'tipo': tipo})

def can_edit_almoxarifado(user):
    if user.is_superuser or user.nivel_hierarquico == 'super_admin':
        return True
    if user.departamentos_liderados.filter(nome__icontains='almoxarifado').exists():
        return True
    return False

@login_required
@requer_permissao('almoxarifado', 'ver')
def painel_inventario(request):
    if not can_edit_almoxarifado(request.user):
        messages.error(request, "Acesso Negado.")
        return redirect('dashboard')

    q = request.GET.get('q', '')
    cat_filter = request.GET.get('categoria', '')
    sub_filter = request.GET.get('subcategoria', '')
    origem_filter = request.GET.get('origem', '')
    tipo_filter = request.GET.get('tipo_item', '')

    import winsound
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Sum

    itens = ItemAlmoxarifado.objects.all().order_by('-id')

    # Métricas Gerais Reais
    total_emprestados = ItemAlmoxarifado.objects.filter(status_item='emprestado').count()
    itens_em_manutencao = ItemAlmoxarifado.objects.filter(status_item='manutencao').count()
    valor_total_estoque = ItemAlmoxarifado.objects.filter(valor_monetario__isnull=False).aggregate(total=Sum('valor_monetario'))['total'] or 0.00

    # Motor de Vencimentos (Alerta Zero-Trust)
    hoje = timezone.now().date()
    limite = hoje + timedelta(days=15)
    itens_vencendo = itens.filter(tipo_item='consumo', data_vencimento__lte=limite, quantidade_estoque__gt=0).order_by('data_vencimento')
    alerta_vencimento = False

    if itens_vencendo.exists():
        alerta_vencimento = True
        try:
            winsound.Beep(1000, 500)
            winsound.Beep(1500, 500)
        except:
            pass

    if q:
        itens = itens.filter(nome__icontains=q) | itens.filter(id_unico__icontains=q)
    if cat_filter:
        itens = itens.filter(categoria_id=cat_filter)
    if sub_filter:
        itens = itens.filter(subcategoria_id=sub_filter)
    if origem_filter:
        itens = itens.filter(origem=origem_filter)
    if tipo_filter:
        itens = itens.filter(tipo_item=tipo_filter)

    if request.headers.get('HX-Request'):
        return render(request, 'almoxarifado/partials/tabela_inventario.html', {'itens': itens})

    # Dash info
    ultimas_retiradas = MovimentacaoAlmoxarifado.objects.filter(tipo='retirada').order_by('-data_hora')[:5]
    ultimas_devolucoes = MovimentacaoAlmoxarifado.objects.filter(tipo='devolucao').order_by('-data_hora')[:5]

    categorias = CategoriaItem.objects.prefetch_related('subcategorias').all().order_by('nome')

    # Para montar os options na view
    origens_choices = ItemAlmoxarifado.ORIGEM_CHOICES
    tipos_choices = ItemAlmoxarifado.TIPO_CHOICES
    status_choices = ItemAlmoxarifado.STATUS_CHOICES

    return render(request, 'almoxarifado/painel_inventario.html', {
        'itens': itens,
        'q': q,
        'cat_filter': cat_filter,
        'sub_filter': sub_filter,
        'origem_filter': origem_filter,
        'tipo_filter': tipo_filter,
        'categorias': categorias,
        'origens_choices': origens_choices,
        'tipos_choices': tipos_choices,
        'status_choices': status_choices,
        'ultimas_retiradas': ultimas_retiradas,
        'ultimas_devolucoes': ultimas_devolucoes,
        'alerta_vencimento': alerta_vencimento,
        'itens_vencendo': itens_vencendo,
        'total_emprestados': total_emprestados,
        'itens_em_manutencao': itens_em_manutencao,
        'valor_total_estoque': valor_total_estoque
    })

@login_required
@requer_permissao('almoxarifado', 'ver')
def livro_almoxarifado(request):
    if not can_edit_almoxarifado(request.user):
        messages.error(request, "Acesso Negado.")
        return redirect('dashboard')

    movimentacoes = MovimentacaoAlmoxarifado.objects.all().order_by('-data_hora')
    return render(request, 'almoxarifado/livro_almoxarifado.html', {'movimentacoes': movimentacoes})

@login_required
@requer_permissao('almoxarifado', 'ver')
def exportar_livro_pdf(request):
    from xhtml2pdf import pisa
    from io import BytesIO
    from django.http import HttpResponse, HttpResponseForbidden
    from django.template.loader import render_to_string

    if not can_edit_almoxarifado(request.user):
        return HttpResponse("Acesso Negado", status=403)

    # Tenta pegar um template customizado do banco de dados (modulo de midia/LGPD)
    template_db = None

    movimentacoes = MovimentacaoAlmoxarifado.objects.all().order_by('-data_hora')

    import os
    from django.conf import settings
    from core.models import ConfiguracaoSistema

    sys_config = ConfiguracaoSistema.objects.first()
    if sys_config and sys_config.igreja_logo:
        logo_path = sys_config.igreja_logo.url
    else:
        logo_path = settings.STATIC_URL + 'img/logo.jpg'

    if template_db:
        from django.template import Template, Context
        t = Template(template_db.conteudo_base)
        html_str = t.render(Context({'movimentacoes': movimentacoes, 'data_geracao': timezone.now(), 'logo_path': logo_path}))
    else:
        # Fallback local
        html_str = render_to_string('almoxarifado/pdf_livro_fallback.html', {'movimentacoes': movimentacoes, 'logo_path': logo_path})

    def fetch_resources(uri, rel):
        if uri.startswith(settings.MEDIA_URL):
            return os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
        elif uri.startswith(settings.STATIC_URL):
            return os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))
        return uri

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_str.encode("UTF-8")), result, link_callback=fetch_resources)

    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="livro_almoxarifado.pdf"'
        return response
    return HttpResponse("Erro ao gerar PDF", status=500)

@login_required
@requer_permissao('almoxarifado', 'ver')
def cadastrar_item_almoxarifado(request):
    if not can_edit_almoxarifado(request.user):
        messages.error(request, "Acesso Negado.")
        return redirect('dashboard')

    categorias = CategoriaItem.objects.all()

    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        categoria_id = request.POST.get('categoria')
        categoria = CategoriaItem.objects.filter(id=categoria_id).first() if categoria_id else None
        subcategoria_id = request.POST.get('subcategoria')
        subcategoria = SubcategoriaItem.objects.filter(id=subcategoria_id).first() if subcategoria_id else None
        tipo_item = request.POST.get('tipo_item', 'permanente')
        quantidade = int(request.POST.get('quantidade', 1))
        data_vencimento = request.POST.get('data_vencimento')
        origem = request.POST.get('origem', 'desconhecido')
        fornecedor = request.POST.get('fornecedor_doador', '').strip()
        localizacao = request.POST.get('localizacao', '').strip()
        destino = request.POST.get('destino_uso', '').strip()
        observacao = request.POST.get('observacao', '').strip()

        valor_str = request.POST.get('valor_monetario', '')
        valor_monetario = float(valor_str) if valor_str else None
        status_pagamento = request.POST.get('status_pagamento', 'nao_se_aplica')
        condicao_fisica = request.POST.get('condicao_fisica', 'nova')

        foto = request.FILES.get('foto_item')
        anexos = request.FILES.getlist('anexos_multiplos')

        id_unico_manual = request.POST.get('id_unico', '').strip()
        exige_aprovacao = request.POST.get('exige_aprovacao') == 'True'

        item = ItemAlmoxarifado(
            nome=nome,
            categoria=categoria,
            subcategoria=subcategoria,
            tipo_item=tipo_item,
            quantidade_estoque=quantidade,
            origem=origem,
            fornecedor_doador=fornecedor,
            localizacao=localizacao,
            destino_uso=destino,
            observacao=observacao,
            valor_monetario=valor_monetario,
            status_pagamento=status_pagamento,
            condicao_fisica=condicao_fisica,
            exige_aprovacao=exige_aprovacao
        )
        if id_unico_manual:
            item.id_unico = id_unico_manual

        if data_vencimento:
            item.data_vencimento = data_vencimento

        if foto:
            item.foto_item = foto

        item.save() # Gera ID Unico

        # Integracao PV Drive
        depto_almo, _ = Departamento.objects.get_or_create(nome='Almoxarifado')
        pasta_raiz_almo, _ = PastaVirtual.objects.get_or_create(nome='Almoxarifado', departamento=depto_almo, defaults={'tipo_pasta': 'departamento', 'is_sistema': True})
        pasta_item = PastaVirtual.objects.create(
            nome=f"{item.id_unico} - {item.nome}",
            departamento=depto_almo,
            parent=pasta_raiz_almo,
            tipo_pasta='normal'
        )
        item.pasta_pv_drive = pasta_item
        item.save()

        # Salva os N Anexos no PV Drive
        for arquivo in anexos:
            ArquivoMidia.objects.create(
                titulo=arquivo.name,
                arquivo=arquivo,
                pasta=pasta_item,
                departamento=depto_almo,
                enviado_por=request.user,
                tamanho_bytes=arquivo.size,
                extensao=os.path.splitext(arquivo.name)[1].lower()
            )

        # Log de Entrada Inicial
        MovimentacaoAlmoxarifado.objects.create(
            item=item,
            tipo='entrada_estoque',
            quantidade=quantidade,
            nome_digitado=request.user.first_name,
            membro_vinculado=request.user,
            observacao="Cadastro Inicial do Item"
        )

        messages.success(request, f"Item {item.nome} cadastrado com sucesso.")
        return redirect('painel_inventario')

    origens_choices = ItemAlmoxarifado.ORIGEM_CHOICES
    tipos_choices = ItemAlmoxarifado.TIPO_CHOICES
    pagamento_choices = ItemAlmoxarifado.PAGAMENTO_CHOICES
    condicao_choices = ItemAlmoxarifado.CONDICAO_CHOICES

    return render(request, 'almoxarifado/cadastrar_item.html', {
        'categorias': categorias,
        'origens_choices': origens_choices,
        'tipos_choices': tipos_choices,
        'pagamento_choices': pagamento_choices,
        'condicao_choices': condicao_choices
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from permissoes.decorators import requer_permissao
from .models import CategoriaItem, SubcategoriaItem

@login_required
@requer_permissao('almoxarifado', 'ver')
def gerenciar_categorias(request):
    if not request.user.nivel_hierarquico in ['super_admin', 'pastor', 'lider']:
        return HttpResponseForbidden("Acesso Negado")

    categorias = CategoriaItem.objects.all().order_by('nome')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            nome = request.POST.get('nome')
            if nome:
                CategoriaItem.objects.create(nome=nome)
                messages.success(request, f"Categoria '{nome}' criada.")

        elif action == 'edit':
            cat_id = request.POST.get('cat_id')
            nome = request.POST.get('nome')
            cat = get_object_or_404(CategoriaItem, id=cat_id)
            cat.nome = nome
            cat.save()
            messages.success(request, "Categoria atualizada.")

        elif action == 'delete':
            cat_id = request.POST.get('cat_id')
            cat = get_object_or_404(CategoriaItem, id=cat_id)
            cat.delete()
            messages.success(request, "Categoria apagada.")

        elif action == 'add_sub':
            cat_id = request.POST.get('cat_id')
            nome = request.POST.get('nome')
            cat = get_object_or_404(CategoriaItem, id=cat_id)
            if nome:
                SubcategoriaItem.objects.create(nome=nome, categoria=cat)
                messages.success(request, f"Subcategoria '{nome}' adicionada a {cat.nome}.")

        elif action == 'delete_sub':
            sub_id = request.POST.get('sub_id')
            sub = get_object_or_404(SubcategoriaItem, id=sub_id)
            sub.delete()
            messages.success(request, "Subcategoria apagada.")

        return redirect('gerenciar_categorias_almoxarifado')

    return render(request, 'almoxarifado/gerenciar_categorias.html', {'categorias': categorias})

@login_required
@requer_permissao('almoxarifado', 'editar')
def editar_item_almoxarifado(request, item_id):
    item = get_object_or_404(ItemAlmoxarifado, id=item_id)
    categorias = CategoriaItem.objects.all()

    if request.method == 'POST':
        item.nome = request.POST.get('nome', '').strip()
        categoria_id = request.POST.get('categoria')
        item.categoria_id = categoria_id if categoria_id else None

        subcategoria_id = request.POST.get('subcategoria')
        item.subcategoria_id = subcategoria_id if subcategoria_id else None
        item.tipo_item = request.POST.get('tipo_item', 'permanente')
        item.quantidade_estoque = int(request.POST.get('quantidade', item.quantidade_estoque))

        data_vencimento = request.POST.get('data_vencimento')
        if data_vencimento:
            item.data_vencimento = data_vencimento

        item.origem = request.POST.get('origem', 'desconhecido')
        item.fornecedor_doador = request.POST.get('fornecedor_doador', '').strip()
        item.localizacao = request.POST.get('localizacao', '').strip()
        item.destino_uso = request.POST.get('destino_uso', '').strip()
        item.observacao = request.POST.get('observacao', '').strip()

        valor_str = request.POST.get('valor_monetario', '')
        item.valor_monetario = float(valor_str) if valor_str else None
        item.status_pagamento = request.POST.get('status_pagamento', 'nao_se_aplica')
        item.condicao_fisica = request.POST.get('condicao_fisica', 'nova')
        item.status_item = request.POST.get('status_item', 'disponivel')

        # Auditoria Zero-Trust Log (se o status foi para descartado)
        if item.status_item == 'descartado':
            item.quantidade_estoque = 0
        item.exige_aprovacao = request.POST.get('exige_aprovacao') == 'True'
        foto = request.FILES.get('foto_item')
        if foto:
            item.foto_item = foto

        item.save()
        messages.success(request, f"Item {item.id_unico} atualizado com sucesso.")
        return redirect('painel_inventario')

    origens_choices = ItemAlmoxarifado.ORIGEM_CHOICES
    tipos_choices = ItemAlmoxarifado.TIPO_CHOICES
    status_choices = ItemAlmoxarifado.STATUS_CHOICES
    pagamento_choices = ItemAlmoxarifado.PAGAMENTO_CHOICES
    condicao_choices = ItemAlmoxarifado.CONDICAO_CHOICES

    return render(request, 'almoxarifado/editar_item.html', {
        'item': item,
        'categorias': categorias,
        'origens_choices': origens_choices,
        'tipos_choices': tipos_choices,
        'status_choices': status_choices,
        'pagamento_choices': pagamento_choices,
        'condicao_choices': condicao_choices
    })

import qrcode
import base64
from io import BytesIO

@login_required
@requer_permissao('almoxarifado', 'ver')
def imprimir_etiqueta_qr(request, item_id):
    if not can_edit_almoxarifado(request.user):
        return HttpResponseForbidden("Acesso Negado")

    item = get_object_or_404(ItemAlmoxarifado, id=item_id)

    from django.conf import settings
    # URL completa (Ex: https://pve.com.br/almoxarifado/qr/retirar/123/)
    base_url = settings.BASE_URL

    url_retirar = f"{base_url}/almoxarifado/qr/retirar/{item.id_unico}/"
    qr_ret = qrcode.QRCode(version=1, box_size=10, border=4)
    qr_ret.add_data(url_retirar)
    qr_ret.make(fit=True)
    img_ret = qr_ret.make_image(fill_color="black", back_color="white")
    buf_ret = BytesIO()
    img_ret.save(buf_ret, format="PNG")
    qr_retirar_b64 = base64.b64encode(buf_ret.getvalue()).decode()

    url_devolver = f"{base_url}/almoxarifado/qr/devolver/{item.id_unico}/"
    qr_dev = qrcode.QRCode(version=1, box_size=10, border=4)
    qr_dev.add_data(url_devolver)
    qr_dev.make(fit=True)
    img_dev = qr_dev.make_image(fill_color="black", back_color="white")
    buf_dev = BytesIO()
    img_dev.save(buf_dev, format="PNG")
    qr_devolver_b64 = base64.b64encode(buf_dev.getvalue()).decode()

    import os
    from django.conf import settings
    logo_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'img', 'logo.jpg')

    return render(request, 'almoxarifado/etiqueta_qr_pdf.html', {
        'item': item,
        'qr_retirar_b64': qr_retirar_b64,
        'qr_devolver_b64': qr_devolver_b64,
        'logo_path': logo_path
    })

@login_required
@requer_permissao('almoxarifado', 'ver')
def imprimir_todos_qrs(request):
    if not can_edit_almoxarifado(request.user):
        return HttpResponseForbidden("Acesso Negado")

    itens = ItemAlmoxarifado.objects.all()
    itens_qr = []
    from django.conf import settings
    base_url = settings.BASE_URL

    for item in itens:
        url_retirar = f"{base_url}/almoxarifado/qr/retirar/{item.id_unico}/"
        qr_ret = qrcode.QRCode(version=1, box_size=10, border=4)
        qr_ret.add_data(url_retirar)
        qr_ret.make(fit=True)
        img_ret = qr_ret.make_image(fill_color="black", back_color="white")
        buf_ret = BytesIO()
        img_ret.save(buf_ret, format="PNG")
        qr_retirar_b64 = base64.b64encode(buf_ret.getvalue()).decode()

        url_devolver = f"{base_url}/almoxarifado/qr/devolver/{item.id_unico}/"
        qr_dev = qrcode.QRCode(version=1, box_size=10, border=4)
        qr_dev.add_data(url_devolver)
        qr_dev.make(fit=True)
        img_dev = qr_dev.make_image(fill_color="black", back_color="white")
        buf_dev = BytesIO()
        img_dev.save(buf_dev, format="PNG")
        qr_devolver_b64 = base64.b64encode(buf_dev.getvalue()).decode()

        itens_qr.append({
            'item': item,
            'qr_retirar_b64': qr_retirar_b64,
            'qr_devolver_b64': qr_devolver_b64
        })

    return render(request, 'almoxarifado/todas_etiquetas_qr.html', {'itens_qr': itens_qr})

# ==========================================
# QR CODES GENÉRICOS (MÓDULO DE AUTO-SERVIÇO)
# ==========================================

def scanner_generico(request, tipo):
    # Renderiza o scanner genérico. Quando um QR Code é lido,
    # ele redirecionará para a rota específica do item lido via JS.
    return render(request, 'almoxarifado/scanner_qr_generico.html', {'tipo': tipo})

def baixar_qr_generico(request, tipo):
    import qrcode
    from django.http import HttpResponse, HttpResponseForbidden
    from django.urls import reverse

    # Gera a URL absoluta para a rota do Scanner Genérico
    url_relativa = reverse('scanner_retirada_generico' if tipo == 'retirada' else 'scanner_devolucao_generico')
    from django.conf import settings
    url_absoluta = f"{settings.BASE_URL}{url_relativa}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url_absoluta)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")
    response['Content-Disposition'] = f'attachment; filename="QR_Geral_{tipo.capitalize()}.png"'
    return response

# ==========================================
# API DE AUTO-SERVIÇO (CARRINHO E APROVAÇÕES)
# ==========================================
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
import json

def api_buscar_item(request, item_id):
    try:
        item = ItemAlmoxarifado.objects.get(id_unico=item_id)
        return JsonResponse({
            'sucesso': True,
            'id_unico': item.id_unico,
            'nome': item.nome,
            'quantidade_estoque': item.quantidade_estoque,
            'exige_aprovacao': item.exige_aprovacao,
            'tipo_item': item.get_tipo_item_display()
        })
    except ItemAlmoxarifado.DoesNotExist:
        return JsonResponse({'sucesso': False, 'mensagem': 'Item não encontrado'}, status=404)

@csrf_exempt
def finalizar_carrinho(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            tipo_acao = data.get('tipo_acao') # 'retirada' ou 'devolucao'
            nome_usuario = data.get('nome')
            email_usuario = data.get('email')
            itens = data.get('itens', []) # [{'id_unico': '...', 'quantidade': 1}, ...]

            if not itens:
                return JsonResponse({'sucesso': False, 'mensagem': 'Carrinho vazio'}, status=400)

            movimentacoes_criadas = []
            itens_pendentes = 0

            for item_data in itens:
                try:
                    item = ItemAlmoxarifado.objects.get(id_unico=item_data['id_unico'])
                    qtd = int(item_data['quantidade'])

                    status_aprov = 'aprovado'
                    if item.exige_aprovacao and tipo_acao == 'retirada':
                        status_aprov = 'pendente'
                        itens_pendentes += 1

                    mov = MovimentacaoAlmoxarifado.objects.create(
                        item=item,
                        tipo=tipo_acao,
                        quantidade=qtd,
                        nome_digitado=nome_usuario,
                        email_digitado=email_usuario,
                        status_aprovacao=status_aprov,
                        observacao="Registrado via Auto-Atendimento (Carrinho)"
                    )

                    if status_aprov == 'aprovado':
                        # Baixa imediata no estoque
                        if tipo_acao == 'retirada':
                            item.quantidade_estoque -= qtd
                        else:
                            item.quantidade_estoque += qtd
                        item.save()

                    movimentacoes_criadas.append(mov.id)
                except ItemAlmoxarifado.DoesNotExist:
                    continue

            # Aciona Notificacao e possivel envio de PDF
            from .tasks import processar_pos_carrinho_background
            import threading
            threading.Thread(target=processar_pos_carrinho_background, args=(movimentacoes_criadas,)).start()

            msg = "Operação registrada com sucesso!"
            if itens_pendentes > 0:
                msg += f" {itens_pendentes} item(ns) estão aguardando liberação do gestor."

            return JsonResponse({'sucesso': True, 'mensagem': msg})
        except Exception as e:
            return JsonResponse({'sucesso': False, 'mensagem': str(e)}, status=500)
    return JsonResponse({'sucesso': False}, status=405)

# ==========================================
# PAINEL DE APROVAÇÕES (GESTOR)
# ==========================================

@login_required
@requer_permissao('almoxarifado', 'ver')
def painel_aprovacoes_almoxarifado(request):
    if not can_edit_almoxarifado(request.user):
        return HttpResponseForbidden("Acesso Negado")

    movs_pendentes = MovimentacaoAlmoxarifado.objects.filter(status_aprovacao='pendente').order_by('data_hora')
    return render(request, 'almoxarifado/fila_aprovacoes.html', {'movimentacoes': movs_pendentes})

@login_required
@requer_permissao('almoxarifado', 'ver')
def processar_aprovacao(request, mov_id, acao):
    if not can_edit_almoxarifado(request.user):
        return HttpResponseForbidden("Acesso Negado")

    mov = get_object_or_404(MovimentacaoAlmoxarifado, id=mov_id)
    if mov.status_aprovacao != 'pendente':
        messages.warning(request, "Esta movimentação já foi processada.")
        return redirect('painel_aprovacoes_almoxarifado')

    if acao == 'aprovar':
        mov.status_aprovacao = 'aprovado'
        mov.observacao += f" [Aprovado por {request.user.first_name}]"
        mov.save()

        # Efetiva baixa/entrada no estoque real
        item = mov.item
        if mov.tipo == 'retirada':
            item.quantidade_estoque -= mov.quantidade
        else:
            item.quantidade_estoque += mov.quantidade
        item.save()

        # Gera e envia PDF Termo Cautela se necessário
        if mov.email_digitado:
            from .tasks import gerar_e_enviar_pdf_termo
            import threading
            threading.Thread(target=gerar_e_enviar_pdf_termo, args=([mov], mov.email_digitado, mov.nome_digitado)).start()

        messages.success(request, f"Movimentação de {item.nome} APROVADA.")

    elif acao == 'rejeitar':
        mov.status_aprovacao = 'rejeitado'
        mov.observacao += f" [Rejeitado por {request.user.first_name}]"
        mov.save()
        messages.error(request, f"Movimentação de {mov.item.nome} REJEITADA.")

    return redirect('painel_aprovacoes_almoxarifado')
