from .models import SessaoAtendimento, AgendamentoPastoral, PessoaAtendimento
from django.contrib import admin

# Register your models here.


@admin.register(PessoaAtendimento)
class PessoaAtendimentoAdmin(admin.ModelAdmin):
    pass

@admin.register(AgendamentoPastoral)
class AgendamentoPastoralAdmin(admin.ModelAdmin):
    pass

@admin.register(SessaoAtendimento)
class SessaoAtendimentoAdmin(admin.ModelAdmin):
    pass
