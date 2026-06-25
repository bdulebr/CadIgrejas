"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: pdv/views.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.template.loader import get_template
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from permissoes.decorators import requer_permissao
from django.core.exceptions import PermissionDenied
from datetime import datetime
from .models import Produto, CategoriaProduto, Venda, ItemVenda, Caixa, Cliente, ConfiguracaoPDV, MovimentoCaixa, OperadorCaixa
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from functools import wraps
from django.http import JsonResponse
from django.contrib import messages
import json
import xmltodict

def pdv_auth_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'pdv_operador_id' not in request.session:
            return redirect('pdv_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def pdv_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            pin = data.get('pin', '')
            operador = OperadorCaixa.objects.filter(pin=pin, ativo=True).first()
            if operador:
                request.session['pdv_operador_id'] = operador.id
                return JsonResponse({'success': True})
            return JsonResponse({'success': False, 'message': 'PIN inválido.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return render(request, 'pdv/login_pdv.html')

def pdv_logout(request):
    if 'pdv_operador_id' in request.session:
        del request.session['pdv_operador_id']
    return redirect('pdv_login')

def pdv_access_check(user):
    if user.nivel_hierarquico == 'super_admin':
        return True

    config = ConfiguracaoPDV.objects.first()
    if config:
        if config.lider == user or config.operadores.filter(id=user.id).exists():
            return True

    return False

def sysadmin_access_check(user):
    return user.nivel_hierarquico == 'super_admin'

@login_required
@requer_permissao('pdv', 'ver')
def pdv_dashboard(request):
    config, _ = ConfiguracaoPDV.objects.get_or_create(id=1)

    # Caixa atual
    caixa_atual = Caixa.objects.filter(status='aberto').last()

    vendas_hoje = Venda.objects.filter(data_venda__date=timezone.now().date(), status='concluida')
    total_vendas_hoje = sum(v.total for v in vendas_hoje)
    from django.db.models import F
    produtos_alerta = Produto.objects.filter(estoque_atual__lte=F('estoque_minimo'))
    return render(request, 'pdv/dashboard.html', {
        'caixa_atual': caixa_atual,
        'total_vendas_hoje': total_vendas_hoje,
        'qtd_vendas_hoje': vendas_hoje.count(),
        'produtos_alerta': produtos_alerta,
        'config': config
    })

@pdv_auth_required
def pdv_frente_caixa(request):
    caixa_atual = Caixa.objects.filter(status='aberto').last()
    operador = OperadorCaixa.objects.get(id=request.session['pdv_operador_id'])
    config, _ = ConfiguracaoPDV.objects.get_or_create(id=1)
    produtos_rapidos = Produto.objects.filter(estoque_atual__gt=0).order_by('nome')
    return render(request, 'pdv/frente_caixa.html', {
        'caixa_atual': caixa_atual,
        'operador_pdv': operador,
        'config': config,
        'produtos_rapidos': produtos_rapidos
    })

@pdv_auth_required
def api_buscar_produto(request, codigo):
    try:
        produto = Produto.objects.get(codigo_barras=codigo)
        return JsonResponse({
            'success': True,
            'id': produto.id,
            'nome': produto.nome,
            'preco_venda': float(produto.preco_venda),
            'estoque_atual': produto.estoque_atual
        })
    except Produto.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Produto não encontrado.'})

@csrf_exempt
@pdv_auth_required
def api_abrir_caixa(request):
    if request.method == 'POST':
        caixa_atual = Caixa.objects.filter(status='aberto').last()
        if caixa_atual:
            return JsonResponse({'success': False, 'message': 'Já existe um caixa aberto.'})
        try:
            data = json.loads(request.body)
            saldo_inicial = float(data.get('saldo_inicial', 0))
            op_id = request.session.get('pdv_operador_id')
            op = OperadorCaixa.objects.filter(id=op_id).first()
            Caixa.objects.create(operador=op, saldo_inicial=saldo_inicial)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False})

@csrf_exempt
@pdv_auth_required
def api_fechar_caixa(request):
    if request.method == 'POST':
        caixa_atual = Caixa.objects.filter(status='aberto').last()
        if not caixa_atual:
            return JsonResponse({'success': False, 'message': 'Nenhum caixa aberto.'})
        try:
            data = json.loads(request.body)
            saldo_final = float(data.get('saldo_final', 0))
            caixa_atual.status = 'fechado'
            caixa_atual.data_fechamento = timezone.now()
            caixa_atual.saldo_final_real = saldo_final
            caixa_atual.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False})

@csrf_exempt
@pdv_auth_required
def api_finalizar_venda(request):
    if request.method == 'POST':
        caixa_atual = Caixa.objects.filter(status='aberto').last()
        if not caixa_atual:
            return JsonResponse({'success': False, 'message': 'Caixa fechado.'})

        try:
            data = json.loads(request.body)
            itens = data.get('itens', [])
            forma_pagamento = data.get('forma_pagamento', 'Dinheiro')
            desconto = float(data.get('desconto', 0))

            cpf_cliente = data.get('cpf', '')
            nome_cliente = data.get('nome_cliente', '')

            cliente = None
            if cpf_cliente or nome_cliente:
                cliente, _ = Cliente.objects.get_or_create(
                    cpf=cpf_cliente,
                    defaults={'nome': nome_cliente if nome_cliente else 'Cliente não identificado'}
                )

            if not itens:
                return JsonResponse({'success': False, 'message': 'Carrinho vazio.'})

            subtotal = sum(float(i['preco']) * int(i['qtd']) for i in itens)
            total = subtotal - desconto

            tipo_venda = data.get('tipo_venda', 'imediata')
            status_pagamento = data.get('status_pagamento', 'pago')
            status_entrega = data.get('status_entrega', 'entregue')
            nome_cliente_reserva = data.get('nome_cliente_reserva', '')

            venda = Venda.objects.create(
                caixa=caixa_atual,
                cliente=cliente,
                subtotal=subtotal,
                desconto=desconto,
                total=total,
                forma_pagamento=forma_pagamento,
                tipo_venda=tipo_venda,
                status_pagamento=status_pagamento,
                status_entrega=status_entrega,
                nome_cliente_reserva=nome_cliente_reserva
            )

            for i in itens:
                prod = Produto.objects.get(id=i['id'])
                qtd = int(i['qtd'])
                ItemVenda.objects.create(
                    venda=venda,
                    produto=prod,
                    quantidade=qtd,
                    valor_unitario=prod.preco_venda,
                    valor_total=float(prod.preco_venda) * qtd
                )
                prod.estoque_atual -= qtd
                prod.save()

            if status_pagamento == 'pago':
                MovimentoCaixa.objects.create(
                    caixa=caixa_atual,
                    tipo='entrada',
                    valor=total,
                    descricao=f'Venda #{venda.id}' if tipo_venda == 'imediata' else f'Reserva Paga #{venda.id}'
                )
                caixa_atual.saldo_final_esperado += total
                caixa_atual.save()

            return JsonResponse({'success': True, 'venda_id': venda.id, 'total': float(total)})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@pdv_auth_required
def imprimir_cupom(request, venda_id):
    venda = get_object_or_404(Venda, id=venda_id)
    config = ConfiguracaoPDV.objects.first()
    return render(request, 'pdv/cupom_impressao.html', {'venda': venda, 'config': config})

@login_required
@requer_permissao('pdv', 'ver')
def importar_xml_fornecedor(request):
    if request.method == 'POST' and request.FILES.get('xml_file'):
        xml_file = request.FILES['xml_file']
        try:
            content = xml_file.read()
            # Tratamento robusto para parsing do XML de nota fiscal
            doc = xmltodict.parse(content)

            # Navegar na estrutura da NFe padrao
            nfe = doc.get('nfeProc', doc).get('NFe', {})
            infNFe = nfe.get('infNFe', {})

            dets = infNFe.get('det', [])
            if not isinstance(dets, list):
                dets = [dets]

            produtos_importados = 0
            cat_default, _ = CategoriaProduto.objects.get_or_create(nome="Importados via XML")

            for det in dets:
                prod_xml = det.get('prod', {})
                codigo_barras = prod_xml.get('cEAN', '')
                nome = prod_xml.get('xProd', '')
                quantidade = float(prod_xml.get('qCom', 0))
                valor_unitario = float(prod_xml.get('vUnCom', 0))
                ncm = prod_xml.get('NCM', '')
                cfop = prod_xml.get('CFOP', '')

                if codigo_barras and codigo_barras != 'SEM GTIN':
                    produto, created = Produto.objects.get_or_create(
                        codigo_barras=codigo_barras,
                        defaults={
                            'nome': nome,
                            'preco_custo': valor_unitario,
                            'preco_venda': valor_unitario * 1.5,  # Sugestao automatica 50% margem
                            'estoque_atual': 0,
                            'categoria': cat_default,
                            'ncm': ncm,
                            'cfop': cfop
                        }
                    )
                    produto.estoque_atual += int(quantidade)
                    produto.preco_custo = valor_unitario  # Atualiza preco de custo
                    produto.save()
                    produtos_importados += 1

            messages.success(request, f'XML processado com sucesso! {produtos_importados} itens adicionados ao estoque.')
        except Exception as e:
            messages.error(request, f'Erro ao processar XML: {str(e)}')

    return redirect('pdv_configuracoes')

@login_required
def lista_produtos(request):
    produtos = Produto.objects.all().order_by('nome')
    return render(request, 'pdv/produtos.html', {'produtos': produtos})

@login_required
def novo_produto(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        codigo_barras = request.POST.get('codigo_barras')
        preco_custo = request.POST.get('preco_custo', 0)
        preco_venda = request.POST.get('preco_venda', 0)
        estoque_atual = request.POST.get('estoque_atual', 0)
        ncm = request.POST.get('ncm', '00000000')
        cfop = request.POST.get('cfop', '')
        cbs = request.POST.get('cbs', '')
        ibs = request.POST.get('ibs', '')
        is_val = request.POST.get('imposto_seletivo', '')

        Produto.objects.create(
            nome=nome,
            codigo_barras=codigo_barras,
            preco_custo=preco_custo,
            preco_venda=preco_venda,
            estoque_atual=estoque_atual,
            ncm=ncm,
            cfop=cfop,
            cbs=cbs if cbs else None,
            ibs=ibs if ibs else None,
            imposto_seletivo=is_val if is_val else None
        )
        messages.success(request, 'Produto cadastrado com sucesso!')
        return redirect('pdv_lista_produtos')

    categorias = CategoriaProduto.objects.all()
    return render(request, 'pdv/form_produto.html', {'categorias': categorias})

@login_required
def editar_produto(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    if request.method == 'POST':
        produto.nome = request.POST.get('nome')
        produto.codigo_barras = request.POST.get('codigo_barras')
        produto.preco_custo = request.POST.get('preco_custo', 0)
        produto.preco_venda = request.POST.get('preco_venda', 0)
        produto.estoque_atual = request.POST.get('estoque_atual', 0)
        produto.ncm = request.POST.get('ncm', '00000000')
        produto.cfop = request.POST.get('cfop', '')

        cbs = request.POST.get('cbs', '')
        ibs = request.POST.get('ibs', '')
        is_val = request.POST.get('imposto_seletivo', '')
        produto.cbs = cbs if cbs else None
        produto.ibs = ibs if ibs else None
        produto.imposto_seletivo = is_val if is_val else None

        produto.save()
        messages.success(request, 'Produto atualizado com sucesso!')

@login_required
def lista_produtos(request):
    produtos = Produto.objects.all().order_by('nome')
    return render(request, 'pdv/produtos.html', {'produtos': produtos})

@login_required
def novo_produto(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        codigo_barras = request.POST.get('codigo_barras')
        preco_custo = request.POST.get('preco_custo', 0)
        preco_venda = request.POST.get('preco_venda', 0)
        estoque_atual = request.POST.get('estoque_atual', 0)
        ncm = request.POST.get('ncm', '00000000')
        cfop = request.POST.get('cfop', '')
        cbs = request.POST.get('cbs', '')
        ibs = request.POST.get('ibs', '')
        is_val = request.POST.get('imposto_seletivo', '')

        Produto.objects.create(
            nome=nome,
            codigo_barras=codigo_barras,
            preco_custo=preco_custo,
            preco_venda=preco_venda,
            estoque_atual=estoque_atual,
            ncm=ncm,
            cfop=cfop,
            cbs=cbs if cbs else None,
            ibs=ibs if ibs else None,
            imposto_seletivo=is_val if is_val else None
        )
        messages.success(request, 'Produto cadastrado com sucesso!')
        return redirect('pdv_lista_produtos')

    categorias = CategoriaProduto.objects.all()
    return render(request, 'pdv/form_produto.html', {'categorias': categorias})

@login_required
def editar_produto(request, produto_id):
    from django.contrib import messages  # Importar messages
    from django.shortcuts import redirect  # Importar redirect
    try:
        produto = Produto.objects.get(id=produto_id)
    except Produto.DoesNotExist:
        messages.error(request, f'O produto com ID {produto_id} não foi encontrado ou já foi removido.')
        return redirect('pdv_lista_produtos')

    if request.method == 'POST':
        produto.nome = request.POST.get('nome')
        produto.codigo_barras = request.POST.get('codigo_barras')
        produto.preco_custo = request.POST.get('preco_custo', 0)
        produto.preco_venda = request.POST.get('preco_venda', 0)
        produto.estoque_atual = request.POST.get('estoque_atual', 0)
        produto.ncm = request.POST.get('ncm', '00000000')
        produto.cfop = request.POST.get('cfop', '')

        cbs = request.POST.get('cbs', '')
        ibs = request.POST.get('ibs', '')
        is_val = request.POST.get('imposto_seletivo', '')
        produto.cbs = cbs if cbs else None
        produto.ibs = ibs if ibs else None
        produto.imposto_seletivo = is_val if is_val else None

        produto.save()
        messages.success(request, 'Produto atualizado com sucesso!')
        return redirect('pdv_lista_produtos')

    categorias = CategoriaProduto.objects.all()
    return render(request, 'pdv/form_produto.html', {'produto': produto, 'categorias': categorias})

@login_required
@requer_permissao('pdv', 'excluir')
def configuracoes_pdv(request):
    config = ConfiguracaoPDV.objects.first()
    if not config:
        config = ConfiguracaoPDV.objects.create()

    if request.method == 'POST':
        config.ativo = request.POST.get('ativo') == 'on'
        config.imprimir_recibo_automatico = request.POST.get('imprimir_recibo_automatico') == 'on'
        config.nfce_ativado = request.POST.get('nfce_ativado') == 'on'

        # Access control
        lider_id = request.POST.get('lider')
        if lider_id:
            from core.models import Membro
            config.lider = Membro.objects.filter(id=lider_id).first()
        else:
            config.lider = None

        operadores_ids = request.POST.getlist('operadores')
        config.save()

        if operadores_ids:
            from core.models import Membro
            ops = Membro.objects.filter(id__in=operadores_ids)
            config.operadores.set(ops)
        else:
            config.operadores.clear()

        messages.success(request, 'Configurações atualizadas!')
        return redirect('pdv_dashboard')

    from core.models import Membro
    membros = Membro.objects.filter(is_active=True).order_by('first_name', 'username')
    return render(request, 'pdv/configuracoes.html', {'config': config, 'membros': membros})

@login_required
@requer_permissao('pdv', 'editar')
def gerenciar_operadores(request):
    if request.method == 'POST':
        acao = request.POST.get('acao')
        if acao == 'novo':
            nome = request.POST.get('nome')
            pin = request.POST.get('pin')
            if len(pin) == 4 and pin.isdigit():
                OperadorCaixa.objects.create(nome=nome, pin=pin, ativo=True)
                messages.success(request, 'Operador criado com sucesso.')
            else:
                messages.error(request, 'O PIN deve ter exatamente 4 dígitos numéricos.')
        elif acao == 'excluir':
            op_id = request.POST.get('op_id')
            OperadorCaixa.objects.filter(id=op_id).delete()
            messages.success(request, 'Operador excluído.')
        elif acao == 'desativar':
            op_id = request.POST.get('op_id')
            op = OperadorCaixa.objects.filter(id=op_id).first()
            if op:
                op.ativo = not op.ativo
                op.save()
                messages.success(request, 'Status alterado.')
        return redirect('pdv_gerenciar_operadores')

    operadores = OperadorCaixa.objects.all().order_by('nome')
    return render(request, 'pdv/operadores.html', {'operadores': operadores})

@login_required
def livro_caixa(request):
    caixas = Caixa.objects.all().order_by('-data_abertura')
    movimentos = MovimentoCaixa.objects.all().order_by('-data_movimento')[:50]
    return render(request, 'pdv/livro_caixa.html', {'caixas': caixas, 'movimentos': movimentos})

@pdv_auth_required
def api_listar_reservas(request):
    from django.db.models import Q
    reservas = Venda.objects.filter(
        Q(tipo_venda='reserva') & (Q(status_pagamento='pendente') | Q(status_entrega='retirar'))
    ).order_by('-data_venda')
    data = []
    for r in reservas:
        data.append({
            'id': r.id,
            'cliente': r.nome_cliente_reserva or (r.cliente.nome if r.cliente else 'Desconhecido'),
            'total': float(r.total),
            'status_pagamento': r.status_pagamento,
            'status_entrega': r.status_entrega,
            'data': r.data_venda.strftime('%d/%m/%Y %H:%M')
        })
    return JsonResponse({'reservas': data})

@csrf_exempt
@pdv_auth_required
def api_atualizar_reserva(request, reserva_id):
    if request.method == 'POST':
        caixa_atual = Caixa.objects.filter(status='aberto').last()
        if not caixa_atual:
            return JsonResponse({'success': False, 'message': 'Nenhum caixa aberto para receber pagamento.'})
        try:
            reserva = Venda.objects.get(id=reserva_id, tipo_venda='reserva')
            data = json.loads(request.body)
            acao = data.get('acao')  # 'pagar' ou 'entregar' ou 'pagar_entregar'

            if 'pagar' in acao and reserva.status_pagamento == 'pendente':
                reserva.status_pagamento = 'pago'
                MovimentoCaixa.objects.create(
                    caixa=caixa_atual,
                    tipo='entrada',
                    valor=reserva.total,
                    descricao=f'Pagamento Reserva #{reserva.id}'
                )
                caixa_atual.saldo_final_esperado += reserva.total
                caixa_atual.save()

            if 'entregar' in acao:
                reserva.status_entrega = 'entregue'

            reserva.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False})

@pdv_auth_required
def relatorio_fiados(request):
    # Fiados = Entregue mas pendente de pagamento
    fiados = Venda.objects.filter(tipo_venda='reserva', status_pagamento='pendente', status_entrega='entregue').order_by('-data_venda')
    total_fiado = sum(v.total for v in fiados)
    return render(request, 'pdv/relatorio_fiados.html', {'fiados': fiados, 'total_fiado': total_fiado})


try:
    from xhtml2pdf import pisa
except ImportError:
    pisa = None

@pdv_auth_required
def relatorios_painel(request):
    periodo = request.GET.get('periodo', 'hoje')
    data_inicio_str = request.GET.get('data_inicio', '')
    data_fim_str = request.GET.get('data_fim', '')

    hoje = timezone.now().date()
    vendas = Venda.objects.prefetch_related('itens__produto').all()
    fiados = Venda.objects.prefetch_related('itens__produto').filter(tipo_venda='reserva', status_pagamento='pendente', status_entrega='entregue')

    data_inicio = None
    data_fim = None

    if periodo == 'hoje':
        vendas = vendas.filter(data_venda__date=hoje)
        fiados = fiados.filter(data_venda__date=hoje)
    elif periodo == 'mes':
        vendas = vendas.filter(data_venda__year=hoje.year, data_venda__month=hoje.month)
        fiados = fiados.filter(data_venda__year=hoje.year, data_venda__month=hoje.month)
    elif periodo == 'ano':
        vendas = vendas.filter(data_venda__year=hoje.year)
        fiados = fiados.filter(data_venda__year=hoje.year)
    elif periodo == 'personalizado' and data_inicio_str and data_fim_str:
        try:
            data_inicio = datetime.fromisoformat(data_inicio_str)
            data_fim = datetime.fromisoformat(data_fim_str)
            if timezone.is_naive(data_inicio):
                data_inicio = timezone.make_aware(data_inicio)
            if timezone.is_naive(data_fim):
                data_fim = timezone.make_aware(data_fim)
            vendas = vendas.filter(data_venda__range=(data_inicio, data_fim))
            fiados = fiados.filter(data_venda__range=(data_inicio, data_fim))
        except ValueError:
            pass  # Invalid format fallback

    vendas = vendas.order_by('-data_venda')
    fiados = fiados.order_by('-data_venda')

    total_vendas = sum(v.total for v in vendas if v.status_pagamento == 'pago')
    total_fiados = sum(v.total for v in fiados)

    context = {
        'periodo': periodo,
        'data_inicio_str': data_inicio_str,
        'data_fim_str': data_fim_str,
        'vendas': vendas,
        'fiados': fiados,
        'total_vendas': total_vendas,
        'total_fiados': total_fiados,
        'data_atual': hoje
    }
    return render(request, 'pdv/relatorios_painel.html', context)

@pdv_auth_required
def exportar_financeiro_pdf(request):
    periodo = request.GET.get('periodo', 'hoje')
    data_inicio_str = request.GET.get('data_inicio', '')
    data_fim_str = request.GET.get('data_fim', '')

    hoje = timezone.now().date()
    vendas = Venda.objects.prefetch_related('itens__produto').all()
    fiados = Venda.objects.prefetch_related('itens__produto').filter(tipo_venda='reserva', status_pagamento='pendente', status_entrega='entregue')

    periodo_texto = "Data: " + hoje.strftime("%d/%m/%Y")

    if periodo == 'hoje':
        vendas = vendas.filter(data_venda__date=hoje)
        fiados = fiados.filter(data_venda__date=hoje)
        periodo_texto = "Vendas de Hoje (" + hoje.strftime("%d/%m/%Y") + ")"
    elif periodo == 'mes':
        vendas = vendas.filter(data_venda__year=hoje.year, data_venda__month=hoje.month)
        fiados = fiados.filter(data_venda__year=hoje.year, data_venda__month=hoje.month)
        periodo_texto = "Vendas do Mês (" + hoje.strftime("%m/%Y") + ")"
    elif periodo == 'ano':
        vendas = vendas.filter(data_venda__year=hoje.year)
        fiados = fiados.filter(data_venda__year=hoje.year)
        periodo_texto = "Vendas do Ano (" + hoje.strftime("%Y") + ")"
    elif periodo == 'personalizado' and data_inicio_str and data_fim_str:
        try:
            data_inicio = datetime.fromisoformat(data_inicio_str)
            data_fim = datetime.fromisoformat(data_fim_str)
            if timezone.is_naive(data_inicio):
                data_inicio = timezone.make_aware(data_inicio)
            if timezone.is_naive(data_fim):
                data_fim = timezone.make_aware(data_fim)
            vendas = vendas.filter(data_venda__range=(data_inicio, data_fim))
            fiados = fiados.filter(data_venda__range=(data_inicio, data_fim))
            periodo_texto = "De {} até {}".format(data_inicio.strftime("%d/%m/%Y %H:%M"), data_fim.strftime("%d/%m/%Y %H:%M"))
        except ValueError:
            pass

    vendas = vendas.order_by('data_venda')
    fiados = fiados.order_by('data_venda')

    total_vendas = sum(v.total for v in vendas if v.status_pagamento == 'pago')
    total_fiados = sum(v.total for v in fiados)

    # Try to load System Settings for Logo
    from core.models import ConfiguracaoSistema
    sys_config = ConfiguracaoSistema.objects.first()

    context = {
        'periodo_texto': periodo_texto,
        'vendas': vendas,
        'fiados': fiados,
        'total_vendas': total_vendas,
        'total_fiados': total_fiados,
        'data_geracao': timezone.now(),
        'sys_config': sys_config
    }

    template = get_template('pdv/relatorio_financeiro_pdf.html')
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Relatorio_Financeiro_{periodo}.pdf"'

    if pisa:
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('Erro ao gerar PDF', status=500)
        return response
    else:
        return HttpResponse('xhtml2pdf não está instalado no servidor.', status=500)
