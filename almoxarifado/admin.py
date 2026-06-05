from django.contrib import admin
from .models import CategoriaItem, ItemAlmoxarifado, MovimentacaoAlmoxarifado

@admin.register(CategoriaItem)
class CategoriaItemAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)

@admin.register(ItemAlmoxarifado)
class ItemAlmoxarifadoAdmin(admin.ModelAdmin):
    list_display = ('id_unico', 'nome', 'categoria', 'tipo_item', 'quantidade_estoque', 'status_item')
    list_filter = ('status_item', 'tipo_item', 'origem', 'categoria')
    search_fields = ('id_unico', 'nome', 'fornecedor_doador')
    readonly_fields = ('id_unico',)

@admin.register(MovimentacaoAlmoxarifado)
class MovimentacaoAlmoxarifadoAdmin(admin.ModelAdmin):
    list_display = ('item', 'tipo', 'quantidade', 'nome_digitado', 'data_hora', 'assinatura_digital_hash')
    list_filter = ('tipo', 'data_hora')
    search_fields = ('item__nome', 'nome_digitado', 'assinatura_digital_hash')
    readonly_fields = ('assinatura_digital_hash',)
