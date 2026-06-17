from .models import ConfiguracaoTesouraria, AnexoLancamento, Lancamento, TagTesouraria, CategoriaTesouraria
"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: tesouraria/admin.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.contrib import admin

# Register your models here.


@admin.register(CategoriaTesouraria)
class CategoriaTesourariaAdmin(admin.ModelAdmin):
    pass

@admin.register(TagTesouraria)
class TagTesourariaAdmin(admin.ModelAdmin):
    pass

@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    pass

@admin.register(AnexoLancamento)
class AnexoLancamentoAdmin(admin.ModelAdmin):
    pass

@admin.register(ConfiguracaoTesouraria)
class ConfiguracaoTesourariaAdmin(admin.ModelAdmin):
    pass
