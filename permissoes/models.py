from django.db import models
from core.models import Membro
from gestao_membros.models import Departamento

class ModuloSistema(models.Model):
    """
    Define os módulos estruturais do sistema para o controle de acesso RBAC.
    Ex: 'tesouraria', 'escalas', 'almoxarifado'.
    """
    nome = models.CharField(max_length=100, help_text="Nome de exibição. Ex: Tesouraria")
    slug = models.SlugField(max_length=50, unique=True, help_text="Código identificador único. Ex: tesouraria")
    descricao = models.TextField(blank=True, null=True)
    icone_lucide = models.CharField(max_length=50, default="box", help_text="Ícone Lucide para a UI")

    class Meta:
        verbose_name = 'Módulo do Sistema'
        verbose_name_plural = 'Módulos do Sistema'

    def __str__(self):
        return self.nome

class PermissaoMembro(models.Model):
    """
    Concede acesso direto a um membro para um módulo específico.
    """
    membro = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='permissoes_modulos')
    modulo = models.ForeignKey(ModuloSistema, on_delete=models.CASCADE, related_name='membros_permitidos')

    pode_ver = models.BooleanField(default=False)
    pode_editar = models.BooleanField(default=False)
    pode_excluir = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Permissão de Membro'
        verbose_name_plural = 'Permissões de Membros'
        unique_together = ('membro', 'modulo')

    def __str__(self):
        return f"{self.membro.first_name} -> {self.modulo.nome}"

class PermissaoDepartamento(models.Model):
    """
    Concede acesso a todos os membros ativos/líderes de um departamento para um módulo específico.
    """
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='permissoes_modulos')
    modulo = models.ForeignKey(ModuloSistema, on_delete=models.CASCADE, related_name='departamentos_permitidos')

    pode_ver = models.BooleanField(default=False)
    pode_editar = models.BooleanField(default=False)
    pode_excluir = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Permissão de Departamento'
        verbose_name_plural = 'Permissões de Departamentos'
        unique_together = ('departamento', 'modulo')

    def __str__(self):
        return f"{self.departamento.nome} -> {self.modulo.nome}"
