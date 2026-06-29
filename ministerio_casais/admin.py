from .models import EventoCasal, PagamentoCursoCasal, EntregaAtividadeAluno, PostagemCurso, PresencaAula, MatriculaCursoCasal, AulaTurma, ProfessorTurma, TurmaCurso, CursoCasal, HistoricoAconselhamentoCasal, Casal, LoteEvento, InscricaoEvento, PagamentoInscricaoEvento, DespesaMinisterio
"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: ministerio_casais/admin.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.contrib import admin

# Register your models here.


@admin.register(Casal)
class CasalAdmin(admin.ModelAdmin):
    pass

@admin.register(HistoricoAconselhamentoCasal)
class HistoricoAconselhamentoCasalAdmin(admin.ModelAdmin):
    pass

@admin.register(CursoCasal)
class CursoCasalAdmin(admin.ModelAdmin):
    pass

@admin.register(TurmaCurso)
class TurmaCursoAdmin(admin.ModelAdmin):
    pass

@admin.register(ProfessorTurma)
class ProfessorTurmaAdmin(admin.ModelAdmin):
    pass

@admin.register(AulaTurma)
class AulaTurmaAdmin(admin.ModelAdmin):
    pass

@admin.register(MatriculaCursoCasal)
class MatriculaCursoCasalAdmin(admin.ModelAdmin):
    pass

@admin.register(PresencaAula)
class PresencaAulaAdmin(admin.ModelAdmin):
    pass

@admin.register(PostagemCurso)
class PostagemCursoAdmin(admin.ModelAdmin):
    pass

@admin.register(EntregaAtividadeAluno)
class EntregaAtividadeAlunoAdmin(admin.ModelAdmin):
    pass

@admin.register(PagamentoCursoCasal)
class PagamentoCursoCasalAdmin(admin.ModelAdmin):
    pass

@admin.register(EventoCasal)
class EventoCasalAdmin(admin.ModelAdmin):
    pass

@admin.register(LoteEvento)
class LoteEventoAdmin(admin.ModelAdmin):
    pass

@admin.register(InscricaoEvento)
class InscricaoEventoAdmin(admin.ModelAdmin):
    pass

@admin.register(PagamentoInscricaoEvento)
class PagamentoInscricaoEventoAdmin(admin.ModelAdmin):
    pass

@admin.register(DespesaMinisterio)
class DespesaMinisterioAdmin(admin.ModelAdmin):
    pass
