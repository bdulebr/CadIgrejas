import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
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
    mensagem = f"O item '{item.nome}' teve uma {movimentacao.get_tipo_display()} registrada por {movimentacao.nome_digitado}. Qtd: {movimentacao.quantidade}."

    for lider in lideres:
        NotificacaoGlobal.objects.create(
            destinatario=lider,
            titulo=titulo,
            mensagem=mensagem,
            tipo='info',
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
def painel_inventario(request):
    if not can_edit_almoxarifado(request.user):
        messages.error(request, "Acesso Negado.")
        return redirect('dashboard')

    itens = ItemAlmoxarifado.objects.all().order_by('-id')

    # Dash info
    ultimas_retiradas = MovimentacaoAlmoxarifado.objects.filter(tipo='retirada').order_by('-data_hora')[:5]
    ultimas_devolucoes = MovimentacaoAlmoxarifado.objects.filter(tipo='devolucao').order_by('-data_hora')[:5]

    return render(request, 'almoxarifado/painel_inventario.html', {
        'itens': itens,
        'ultimas_retiradas': ultimas_retiradas,
        'ultimas_devolucoes': ultimas_devolucoes
    })

@login_required
def livro_almoxarifado(request):
    if not can_edit_almoxarifado(request.user):
        messages.error(request, "Acesso Negado.")
        return redirect('dashboard')

    movimentacoes = MovimentacaoAlmoxarifado.objects.all().order_by('-data_hora')
    return render(request, 'almoxarifado/livro_almoxarifado.html', {'movimentacoes': movimentacoes})

@login_required
def exportar_livro_pdf(request):
    import pdfkit
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from midia_lgpd.models import DocumentoTemplate

    if not can_edit_almoxarifado(request.user):
        return HttpResponse("Acesso Negado", status=403)

    # Tenta pegar um template customizado do banco de dados (modulo de midia/LGPD)
    template_db = DocumentoTemplate.objects.filter(tipo='relatorio_almoxarifado').first()

    movimentacoes = MovimentacaoAlmoxarifado.objects.all().order_by('-data_hora')

    if template_db:
        from django.template import Template, Context
        t = Template(template_db.conteudo_html)
        html_str = t.render(Context({'movimentacoes': movimentacoes, 'data_geracao': timezone.now()}))
    else:
        # Fallback local
        html_str = render_to_string('almoxarifado/pdf_livro_fallback.html', {'movimentacoes': movimentacoes})

    options = {
        'page-size': 'A4',
        'encoding': "UTF-8",
        'enable-local-file-access': None
    }

    pdf = pdfkit.from_string(html_str, False, options=options)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="livro_almoxarifado.pdf"'
    return response

@login_required
def cadastrar_item_almoxarifado(request):
    if not can_edit_almoxarifado(request.user):
        messages.error(request, "Acesso Negado.")
        return redirect('dashboard')

    categorias = CategoriaItem.objects.all()

    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        categoria_id = request.POST.get('categoria')
        subcategoria = request.POST.get('subcategoria', '').strip()
        tipo_item = request.POST.get('tipo_item', 'permanente')
        quantidade = int(request.POST.get('quantidade', 1))
        data_vencimento = request.POST.get('data_vencimento')
        origem = request.POST.get('origem', 'desconhecido')
        fornecedor = request.POST.get('fornecedor_doador', '').strip()
        localizacao = request.POST.get('localizacao', '').strip()
        destino = request.POST.get('destino_uso', '').strip()
        observacao = request.POST.get('observacao', '').strip()

        foto = request.FILES.get('foto_item')
        anexos = request.FILES.getlist('anexos_multiplos')

        categoria = CategoriaItem.objects.filter(id=categoria_id).first() if categoria_id else None

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
            observacao=observacao
        )
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

        messages.success(request, f"Item {item.id_unico} cadastrado com sucesso! Pasta no PV Drive gerada.")
        return redirect('painel_inventario')

    return render(request, 'almoxarifado/cadastrar_item.html', {'categorias': categorias})
