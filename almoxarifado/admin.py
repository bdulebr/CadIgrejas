"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: almoxarifado/admin.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.contrib import admin
from .models import CategoriaItem, SubcategoriaItem, ItemAlmoxarifado, MovimentacaoAlmoxarifado

@admin.register(CategoriaItem)
class CategoriaItemAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)

@admin.register(SubcategoriaItem)
class SubcategoriaItemAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria')
    list_filter = ('categoria',)
    search_fields = ('nome', 'categoria__nome')

@admin.register(ItemAlmoxarifado)
class ItemAlmoxarifadoAdmin(admin.ModelAdmin):
    list_display = ('id_unico', 'nome', 'categoria', 'tipo_item', 'quantidade_estoque', 'status_item', 'valor_monetario', 'status_pagamento', 'condicao_fisica', 'exige_aprovacao')
    list_filter = ('status_item', 'tipo_item', 'origem', 'categoria', 'status_pagamento', 'condicao_fisica', 'exige_aprovacao')
    search_fields = ('id_unico', 'nome', 'fornecedor_doador')
    readonly_fields = ('id_unico',)

@admin.register(MovimentacaoAlmoxarifado)
class MovimentacaoAlmoxarifadoAdmin(admin.ModelAdmin):
    list_display = ('item', 'tipo', 'quantidade', 'nome_digitado', 'status_aprovacao', 'data_hora', 'assinatura_digital_hash')
    list_filter = ('tipo', 'status_aprovacao', 'data_hora')
    search_fields = ('item__nome', 'nome_digitado', 'email_digitado', 'assinatura_digital_hash')
    readonly_fields = ('assinatura_digital_hash',)
