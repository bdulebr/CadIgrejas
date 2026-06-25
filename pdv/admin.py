"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: pdv/admin.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.contrib import admin
from .models import CategoriaProduto, Fornecedor, Cliente, Produto, Caixa, Venda, ItemVenda, MovimentoCaixa, ConfiguracaoPDV, OperadorCaixa

admin.site.register(CategoriaProduto)
admin.site.register(OperadorCaixa)
admin.site.register(Fornecedor)
admin.site.register(Cliente)

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('codigo_barras', 'nome', 'estoque_atual', 'preco_venda')
    search_fields = ('nome', 'codigo_barras')
    list_filter = ('categoria',)

@admin.register(Caixa)
class CaixaAdmin(admin.ModelAdmin):
    list_display = ('id', 'operador', 'data_abertura', 'status', 'saldo_final_real')
    list_filter = ('status', 'data_abertura')

class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 0

@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ('id', 'caixa', 'total', 'forma_pagamento', 'data_venda', 'status')
    list_filter = ('status', 'forma_pagamento', 'data_venda')
    inlines = [ItemVendaInline]


admin.site.register(MovimentoCaixa)
admin.site.register(ConfiguracaoPDV)


@admin.register(ItemVenda)
class ItemVendaAdmin(admin.ModelAdmin):
    pass
