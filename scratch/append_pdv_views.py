import os

new_views = """
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
def configuracoes_pdv(request):
    config = ConfiguracaoPDV.objects.first()
    if not config:
        config = ConfiguracaoPDV.objects.create()
        
    if request.method == 'POST':
        config.ativo = request.POST.get('ativo') == 'on'
        config.imprimir_recibo_automatico = request.POST.get('imprimir_recibo_automatico') == 'on'
        config.nfce_ativado = request.POST.get('nfce_ativado') == 'on'
        config.save()
        messages.success(request, 'Configurações atualizadas!')
        return redirect('pdv_dashboard')
        
    return render(request, 'pdv/configuracoes.html', {'config': config})

@login_required
def livro_caixa(request):
    caixas = Caixa.objects.all().order_by('-data_abertura')
    movimentos = MovimentoCaixa.objects.all().order_by('-data_movimento')[:50]
    return render(request, 'pdv/livro_caixa.html', {'caixas': caixas, 'movimentos': movimentos})
"""

with open(r'c:\Users\MarcosLira\Desktop\Marcos\Projeto\pdv\views.py', 'a', encoding='utf-8') as f:
    f.write(new_views)
