from django.contrib import admin
from .models import Habilidade, Departamento, Funcao, Indisponibilidade, AvisoMural, AvisoAnexo, ConfiguracaoSlotEscala

@admin.register(ConfiguracaoSlotEscala)
class ConfiguracaoSlotEscalaAdmin(admin.ModelAdmin):
    list_display = ('departamento', 'funcao', 'quantidade', 'tipo_evento')
    list_filter = ('departamento', 'tipo_evento')
    search_fields = ('departamento__nome', 'funcao__nome')

@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'id_unico_fixo')
    list_filter = ('categoria',)
    search_fields = ('nome', 'id_unico_fixo')

@admin.register(Habilidade)
class HabilidadeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao', 'departamento')
    list_filter = ('departamento',)
    search_fields = ('nome',)

@admin.register(Funcao)
class FuncaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'departamento')
    list_filter = ('departamento',)
    search_fields = ('nome', 'departamento__nome')

@admin.register(Indisponibilidade)
class IndisponibilidadeAdmin(admin.ModelAdmin):
    list_display = ('membro', 'data_inicio', 'data_fim', 'motivo')
    list_filter = ('data_inicio', 'data_fim')
    search_fields = ('membro__first_name', 'motivo')

@admin.register(AvisoMural)
class AvisoMuralAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'departamento', 'autor', 'data_postagem', 'data_expiracao', 'fixado')
    list_filter = ('fixado', 'departamento', 'data_postagem', 'data_expiracao')
    search_fields = ('titulo', 'mensagem', 'autor__first_name')

@admin.register(AvisoAnexo)
class AvisoAnexoAdmin(admin.ModelAdmin):
    list_display = ('aviso', 'nome_original', 'arquivo')
    search_fields = ('aviso__titulo', 'nome_original')
