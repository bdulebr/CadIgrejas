"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: escalas/admin.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from .models import CultoEvento
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


@admin.register(CultoEvento)
class CultoEventoAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)
