"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: permissoes/models.py
"""
from django.db import models
from core.models import Membro
from gestao_membros.models import Departamento

ESCOPO_CHOICES = (
    ('global', 'Global (Toda a Igreja)'),
    ('departamento', 'Departamento (Apenas seu depto)'),
    ('proprio', 'Próprio (Apenas dados próprios)'),
)

class ModuloSistema(models.Model):
    """
    Define os módulos estruturais do sistema para o controle de acesso RBAC.
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

class PerfilAcesso(models.Model):
    """
    Agrupa permissões (Roles) para atribuir a membros facilmente.
    Ex: "Administrador Financeiro", "Líder de Célula".
    """
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    membros = models.ManyToManyField(Membro, blank=True, related_name='perfis_acesso')

    class Meta:
        verbose_name = 'Perfil de Acesso'
        verbose_name_plural = 'Perfis de Acesso'

    def __str__(self):
        return self.nome

class PermissaoBase(models.Model):
    """Classe abstrata com os campos comuns de permissões."""
    modulo = models.ForeignKey(ModuloSistema, on_delete=models.CASCADE)

    pode_ver = models.BooleanField(default=False)
    pode_editar = models.BooleanField(default=False)
    pode_excluir = models.BooleanField(default=False)

    # 2. Ações Granulares (Ex: {"aprovar_despesa": true})
    acoes_extras = models.JSONField(default=dict, blank=True, help_text='Dicionário JSON de ações customizadas')

    # 3. Permissões Temporárias / Expiráveis
    data_expiracao = models.DateTimeField(null=True, blank=True, help_text="Se preenchido, o acesso será revogado após esta data")

    # 4. Escopo de Dados (RLS)
    escopo_acesso = models.CharField(max_length=20, choices=ESCOPO_CHOICES, default='global')

    # 5. Log de Auditoria
    concedido_por = models.ForeignKey(Membro, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    concedido_em = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        abstract = True


class PermissaoPerfil(PermissaoBase):
    perfil = models.ForeignKey(PerfilAcesso, on_delete=models.CASCADE, related_name='permissoes_modulos')

    class Meta:
        verbose_name = 'Permissão de Perfil'
        verbose_name_plural = 'Permissões de Perfis'
        unique_together = ('perfil', 'modulo')

    def __str__(self):
        return f"Perfil {self.perfil.nome} -> {self.modulo.nome}"


class PermissaoMembro(PermissaoBase):
    membro = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='permissoes_modulos')
    modulo = models.ForeignKey(ModuloSistema, on_delete=models.CASCADE, related_name='membros_permitidos')

    class Meta:
        verbose_name = 'Permissão de Membro'
        verbose_name_plural = 'Permissões de Membros'
        unique_together = ('membro', 'modulo')

    def __str__(self):
        return f"{self.membro.first_name} -> {self.modulo.nome}"


class PermissaoDepartamento(PermissaoBase):
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='permissoes_modulos')
    modulo = models.ForeignKey(ModuloSistema, on_delete=models.CASCADE, related_name='departamentos_permitidos')

    class Meta:
        verbose_name = 'Permissão de Departamento'
        verbose_name_plural = 'Permissões de Departamentos'
        unique_together = ('departamento', 'modulo')

    def __str__(self):
        return f"{self.departamento.nome} -> {self.modulo.nome}"
