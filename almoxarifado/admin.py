from django.contrib import admin
from .models import Ativo, Emprestimo, Manutencao, AlimentoLote, TransacaoAlimento, CategoriaAtivo, SubCategoriaAtivo

@admin.register(CategoriaAtivo)
class CategoriaAtivoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)

@admin.register(SubCategoriaAtivo)
class SubCategoriaAtivoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria')
    list_filter = ('categoria',)
    search_fields = ('nome', 'categoria__nome')

@admin.register(Ativo)
class AtivoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'codigo_patrimonio', 'status', 'departamento_dono', 'valor', 'categoria_obj')
    list_filter = ('status', 'origem', 'departamento_dono', 'categoria_obj')
    search_fields = ('nome', 'codigo_patrimonio')

@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = ('ativo', 'membro_solicitante', 'data_retirada', 'data_devolucao_real')
    list_filter = ('data_retirada', 'data_devolucao_real')
    search_fields = ('ativo__nome', 'membro_solicitante__first_name')

@admin.register(Manutencao)
class ManutencaoAdmin(admin.ModelAdmin):
    list_display = ('ativo', 'oficina_tecnico', 'data_envio', 'data_retorno_real', 'custo')
    list_filter = ('data_envio', 'data_retorno_real')
    search_fields = ('ativo__nome', 'oficina_tecnico')

@admin.register(AlimentoLote)
class AlimentoLoteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'quantidade_atual', 'data_vencimento', 'departamento')
    list_filter = ('data_vencimento', 'departamento')
    search_fields = ('nome',)

@admin.register(TransacaoAlimento)
class TransacaoAlimentoAdmin(admin.ModelAdmin):
    list_display = ('lote', 'tipo', 'quantidade', 'data_transacao', 'membro_responsavel')
    list_filter = ('tipo', 'data_transacao')
    search_fields = ('lote__nome', 'membro_responsavel__first_name')
