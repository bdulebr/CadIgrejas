"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: visitantes/admin.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.contrib import admin
from .models import Visitante, VisitaCulto, RegistroAcompanhamento

class VisitaCultoInline(admin.TabularInline):
    model = VisitaCulto
    extra = 1

class RegistroAcompanhamentoInline(admin.StackedInline):
    model = RegistroAcompanhamento
    extra = 1

@admin.register(Visitante)
class VisitanteAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'tipo', 'em_acompanhamento', 'telefone', 'familiar_vinculado', 'data_cadastro')
    list_filter = ('tipo', 'em_acompanhamento', 'data_cadastro')
    search_fields = ('nome_completo', 'email', 'telefone')
    inlines = [VisitaCultoInline, RegistroAcompanhamentoInline]
    autocomplete_fields = ['cadastrado_por', 'familiar_vinculado']

@admin.register(VisitaCulto)
class VisitaCultoAdmin(admin.ModelAdmin):
    list_display = ('visitante', 'data_culto', 'observacoes')
    list_filter = ('data_culto',)
    search_fields = ('visitante__nome_completo', 'observacoes')
    autocomplete_fields = ['visitante']

@admin.register(RegistroAcompanhamento)
class RegistroAcompanhamentoAdmin(admin.ModelAdmin):
    list_display = ('visitante', 'data_contato', 'meio_contato', 'responsavel')
    list_filter = ('meio_contato', 'data_contato', 'responsavel')
    search_fields = ('visitante__nome_completo', 'resumo_conversa', 'responsavel__nome_completo')
    autocomplete_fields = ['visitante', 'responsavel']
