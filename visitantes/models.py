from django.db import models
from django.utils import timezone
from core.models import Membro
from gestao_membros.models import Departamento

class Visitante(models.Model):
    TIPO_CHOICES = [
        ('Visitante', 'Visitante'),
        ('Novo Convertido', 'Novo Convertido'),
    ]

    nome_completo = models.CharField(max_length=255, verbose_name="Nome Completo")
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone (WhatsApp)")
    email = models.EmailField(blank=True, null=True, verbose_name="E-mail")
    endereco = models.TextField(blank=True, null=True, verbose_name="Endereço")

    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='Visitante', verbose_name="Tipo")
    em_acompanhamento = models.BooleanField(default=True, verbose_name="Em Acompanhamento", help_text="Marque se a pessoa ainda está sendo acompanhada ativamente")
    tornou_se_membro = models.BooleanField(default=False, verbose_name="Tornou-se Membro", help_text="Marque se este visitante se tornou membro integrado da igreja")
    desistiu = models.BooleanField(default=False, verbose_name="Desistiu", help_text="Marque se o visitante desistiu e não frequenta mais")

    data_cadastro = models.DateTimeField(default=timezone.now, verbose_name="Data de Cadastro")
    cadastrado_por = models.ForeignKey(Membro, on_delete=models.SET_NULL, null=True, blank=True, related_name='visitantes_cadastrados', verbose_name="Cadastrado Por")

    familiar_vinculado = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='membros_familia', verbose_name="Familiar / Relacionamento", help_text="Selecione caso esta pessoa pertença à mesma família de outro visitante cadastrado")

    class Meta:
        verbose_name = "Visitante / Novo Convertido"
        verbose_name_plural = "Visitantes e Novos Convertidos"
        ordering = ['-data_cadastro']

    def __str__(self):
        return f"{self.nome_completo} ({self.tipo})"


class VisitaCulto(models.Model):
    MODALIDADE_CHOICES = [
        ('Presencial', 'Presencial'),
        ('Live', 'Online / Live'),
    ]

    visitante = models.ForeignKey(Visitante, on_delete=models.CASCADE, related_name='visitas', verbose_name="Visitante")
    data_culto = models.DateField(default=timezone.now, verbose_name="Data do Culto/Evento")
    nome_culto = models.CharField(max_length=255, verbose_name="Qual Culto/Evento", default="Culto da Família")
    modalidade = models.CharField(max_length=50, choices=MODALIDADE_CHOICES, default='Presencial', verbose_name="Modalidade")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações", help_text="Ex: Fez apelo, Veio com a família, etc.")

    class Meta:
        verbose_name = "Visita / Presença"
        verbose_name_plural = "Histórico de Visitas"
        ordering = ['-data_culto']

    def __str__(self):
        return f"Visita de {self.visitante.nome_completo} em {self.data_culto.strftime('%d/%m/%Y')}"


class RegistroAcompanhamento(models.Model):
    MEIO_CHOICES = [
        ('WhatsApp', 'WhatsApp'),
        ('Ligação', 'Ligação'),
        ('Presencial', 'Presencial (No Culto)'),
        ('Visita', 'Visita no Lar'),
        ('Outro', 'Outro'),
    ]

    visitante = models.ForeignKey(Visitante, on_delete=models.CASCADE, related_name='registros_acompanhamento', verbose_name="Visitante")
    data_contato = models.DateTimeField(default=timezone.now, verbose_name="Data e Hora do Contato")
    meio_contato = models.CharField(max_length=50, choices=MEIO_CHOICES, default='WhatsApp', verbose_name="Meio de Contato")
    responsavel = models.ForeignKey(Membro, on_delete=models.SET_NULL, null=True, related_name='contatos_realizados', verbose_name="Líder/Voluntário Responsável")

    resumo_conversa = models.TextField(verbose_name="Resumo da Conversa", help_text="O que foi conversado? Como a pessoa está?")
    proximo_passo = models.CharField(max_length=255, blank=True, null=True, verbose_name="Próximo Passo", help_text="Ex: Ligar na próxima semana, convidou para GC, etc.")

    class Meta:
        verbose_name = "Registro de Acompanhamento"
        verbose_name_plural = "Diário de Acompanhamentos"
        ordering = ['-data_contato']

    def __str__(self):
        return f"Contato com {self.visitante.nome_completo} em {self.data_contato.strftime('%d/%m/%Y')}"
