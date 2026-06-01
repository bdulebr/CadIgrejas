from django.contrib import admin
from .models import Escala, CompetenciaEscala

@admin.register(CompetenciaEscala)
class CompetenciaEscalaAdmin(admin.ModelAdmin):
    list_display = ('departamento', 'mes_ano', 'status')
    list_filter = ('departamento', 'status', 'mes_ano')
    search_fields = ('mes_ano',)

@admin.register(Escala)
class EscalaAdmin(admin.ModelAdmin):
    list_display = ('membro_escalado', 'departamento_alocado', 'funcao_alocada', 'data_escala', 'horario_inicio', 'status')
    list_filter = ('status', 'departamento_alocado', 'data_escala', 'tipo_evento')
    search_fields = ('membro_escalado__first_name', 'departamento_alocado__nome')

from .models import CultoEvento

@admin.register(CultoEvento)
class CultoEventoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'data_hora', 'recorrente', 'ativo')
    list_filter = ('recorrente', 'ativo', 'data_hora')
    search_fields = ('nome',)
