from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.contrib import messages
from .models import Produto, Venda, ItemVenda, Caixa, CategoriaProduto, ConfiguracaoPDV, MovimentoCaixa
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import xmltodict

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
@user_passes_test(pdv_access_check)
def pdv_dashboard(request):
    config, _ = ConfiguracaoPDV.objects.get_or_create(id=1)

    # Caixa atual
    caixa_atual = Caixa.objects.filter(status='aberto').last()

    if request.method == 'POST':
        acao = request.POST.get('acao')
        if acao == 'abrir_caixa' and not caixa_atual:
            Caixa.objects.create(
                operador=request.user,
                saldo_inicial=float(request.POST.get('saldo_inicial', 0))
            )
            messages.success(request, 'Caixa aberto com sucesso.')
        elif acao == 'fechar_caixa' and caixa_atual:
            caixa_atual.status = 'fechado'
            caixa_atual.data_fechamento = timezone.now()
            caixa_atual.saldo_final_real = float(request.POST.get('saldo_final_real', 0))
            caixa_atual.save()
            messages.success(request, 'Caixa fechado com sucesso.')
        return redirect('pdv_dashboard')

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

@login_required
@user_passes_test(pdv_access_check)
def pdv_frente_caixa(request):
    caixa_atual = Caixa.objects.filter(status='aberto').last()
    if not caixa_atual:
        messages.warning(request, 'Você precisa abrir o caixa primeiro.')
        return redirect('pdv_dashboard')

    config, _ = ConfiguracaoPDV.objects.get_or_create(id=1)
    produtos_rapidos = Produto.objects.filter(estoque_atual__gt=0).order_by('nome')
    return render(request, 'pdv/frente_caixa.html', {
        'caixa_atual': caixa_atual,
        'config': config,
        'produtos_rapidos': produtos_rapidos
    })

@login_required
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
@login_required
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

            if not itens:
                return JsonResponse({'success': False, 'message': 'Carrinho vazio.'})

            subtotal = sum(float(i['preco']) * int(i['qtd']) for i in itens)
            total = subtotal - desconto

            venda = Venda.objects.create(
                caixa=caixa_atual,
                subtotal=subtotal,
                desconto=desconto,
                total=total,
                forma_pagamento=forma_pagamento
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

            MovimentoCaixa.objects.create(
                caixa=caixa_atual,
                tipo='entrada',
                valor=total,
                descricao=f'Venda #{venda.id}'
            )

            caixa_atual.saldo_final_esperado += total
            caixa_atual.save()

            return JsonResponse({'success': True, 'venda_id': venda.id, 'total': float(total)})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
@user_passes_test(pdv_access_check)
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
                            'preco_venda': valor_unitario * 1.5, # Sugestao automatica 50% margem
                            'estoque_atual': 0,
                            'categoria': cat_default,
                            'ncm': ncm,
                            'cfop': cfop
                        }
                    )
                    produto.estoque_atual += int(quantidade)
                    produto.preco_custo = valor_unitario # Atualiza preco de custo
                    produto.save()
                    produtos_importados += 1

            messages.success(request, f'XML processado com sucesso! {produtos_importados} itens adicionados ao estoque.')
        except Exception as e:
            messages.error(request, f'Erro ao processar XML: {str(e)}')

    return redirect('pdv_dashboard')

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

        Produto.objects.create(
            nome=nome,
            codigo_barras=codigo_barras,
            preco_custo=preco_custo,
            preco_venda=preco_venda,
            estoque_atual=estoque_atual
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

        Produto.objects.create(
            nome=nome,
            codigo_barras=codigo_barras,
            preco_custo=preco_custo,
            preco_venda=preco_venda,
            estoque_atual=estoque_atual
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
        produto.save()
        messages.success(request, 'Produto atualizado com sucesso!')
        return redirect('pdv_lista_produtos')

    categorias = CategoriaProduto.objects.all()
    return render(request, 'pdv/form_produto.html', {'produto': produto, 'categorias': categorias})

@login_required
@user_passes_test(sysadmin_access_check)
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
def livro_caixa(request):
    caixas = Caixa.objects.all().order_by('-data_abertura')
    movimentos = MovimentoCaixa.objects.all().order_by('-data_movimento')[:50]
    return render(request, 'pdv/livro_caixa.html', {'caixas': caixas, 'movimentos': movimentos})
