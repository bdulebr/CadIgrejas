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

from .models import AvaliacaoMembro, Ocorrencia, AcaoDisciplinar

@admin.register(AvaliacaoMembro)
class AvaliacaoMembroAdmin(admin.ModelAdmin):
    list_display = ('membro', 'avaliador', 'nota', 'data', 'enviado_ao_membro')
    list_filter = ('nota', 'enviado_ao_membro', 'data')
    search_fields = ('membro__first_name', 'avaliador__first_name', 'comentarios')

@admin.register(Ocorrencia)
class OcorrenciaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'data_ocorrencia', 'autor', 'data_registro')
    list_filter = ('data_ocorrencia', 'data_registro')
    search_fields = ('titulo', 'descricao', 'autor__first_name')

@admin.register(AcaoDisciplinar)
class AcaoDisciplinarAdmin(admin.ModelAdmin):
    list_display = ('membro', 'tipo', 'data_aplicacao', 'autor', 'enviado_email')
    list_filter = ('tipo', 'data_aplicacao', 'enviado_email')
    search_fields = ('membro__first_name', 'motivo', 'autor__first_name')
