from django.db import models
from core.models import Membro, LogImutavel
from gestao_membros.models import Departamento
from django.core.validators import FileExtensionValidator
import hashlib

class CategoriaTesouraria(models.Model):
    nome = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategorias')
    tipo = models.CharField(max_length=10, choices=(('entrada', 'Entrada'), ('saida', 'Saída')))
    cor_hex = models.CharField(max_length=7, default='#3b82f6')

    def __str__(self):
        if self.parent:
            return f"{self.parent.nome} > {self.nome}"
        return self.nome

class TagTesouraria(models.Model):
    nome = models.CharField(max_length=50, unique=True)
    cor_hex = models.CharField(max_length=7, default='#10b981')

    def __str__(self):
        return f"#{self.nome}"

class Lancamento(models.Model):
    STATUS_CHOICES = (
        ('pago', 'Pago/Recebido'),
        ('pendente', 'Pendente'),
        ('atrasado', 'Atrasado'),
        ('cancelado', 'Cancelado'),
    )

    TIPO_CHOICES = (
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
    )

    descricao = models.CharField(max_length=255)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    data_vencimento = models.DateField()
    data_lancamento = models.DateTimeField(null=True, blank=True, help_text="Data e hora em que a transação ocorreu de fato")
    data_pagamento = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pago')

    categoria = models.ForeignKey(CategoriaTesouraria, on_delete=models.RESTRICT, related_name='lancamentos')
    tags = models.ManyToManyField(TagTesouraria, blank=True)

    FORMA_PAGAMENTO_CHOICES = (
        ('pix', 'PIX'),
        ('boleto', 'Boleto'),
        ('credito', 'Cartão de Crédito'),
        ('debito', 'Cartão de Débito'),
        ('dinheiro', 'Dinheiro'),
        ('transferencia', 'Transferência'),
        ('outros', 'Outros')
    )
    forma_pagamento = models.CharField(max_length=20, choices=FORMA_PAGAMENTO_CHOICES, default='outros')
    impostos = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Total de impostos cobrados na nota")

    is_parcelado = models.BooleanField(default=False)
    numero_parcelas = models.PositiveIntegerField(default=1, null=True, blank=True)
    parcela_atual = models.PositiveIntegerField(default=1, null=True, blank=True)

    observacoes = models.TextField(blank=True)

    responsavel = models.ForeignKey(Membro, on_delete=models.RESTRICT, related_name='lancamentos_registrados')
    departamento_origem = models.ForeignKey(Departamento, on_delete=models.RESTRICT, related_name='lancamentos_departamento', null=True, blank=True)

    # Rastreio Zero-Trust
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    hash_assinatura = models.CharField(max_length=64, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-data_vencimento', '-id']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Assinatura de integridade no Log Imutavel da Intranet
        impostos_str = f"|IMP:{self.impostos}" if self.impostos else ""
        parcelas_str = f"|PARC:{self.parcela_atual}/{self.numero_parcelas}" if self.is_parcelado else ""
        data_lanc_str = f"|LANC:{self.data_lancamento}" if self.data_lancamento else ""
        data_str = f"LANC-{self.id}|{self.valor}|{self.tipo}|{self.status}|{self.data_vencimento}{data_lanc_str}|{self.forma_pagamento}{impostos_str}{parcelas_str}"
        hash_val = hashlib.sha256(data_str.encode('utf-8')).hexdigest()

        if self.hash_assinatura != hash_val:
            self.hash_assinatura = hash_val
            super().save(update_fields=['hash_assinatura'])

            LogImutavel.objects.create(
                membro=self.responsavel,
                acao=f"SALVOU_LANCAMENTO_{self.id}",
                dados_acao=f"Val:{self.valor} | Tipo:{self.tipo} | St:{self.status} | Cat:{self.categoria.nome}"
            )

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.descricao} (R$ {self.valor})"

class AnexoLancamento(models.Model):
    lancamento = models.ForeignKey(Lancamento, on_delete=models.CASCADE, related_name='anexos')
    arquivo = models.FileField(upload_to='tesouraria/anexos/%Y/%m/', validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'xls', 'xlsx', 'csv', 'doc', 'docx'])])
    nome_original = models.CharField(max_length=255)
    enviado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Anexo de {self.lancamento.id} - {self.nome_original}"


class ConfiguracaoTesouraria(models.Model):
    email_sede = models.EmailField(blank=True, null=True, help_text="E-mail da Sede para recebimento do relatório mensal")
    nome_recebedor_sede = models.CharField(max_length=150, blank=True, null=True, help_text="Nome da pessoa ou departamento responsável na Sede")
    planilha_padrao_sede = models.FileField(
        upload_to='tesouraria/templates_sede/',
        null=True, blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['xls', 'xlsx'])],
        help_text="Upload da planilha padrão (template) exigida pela Sede. A IA preencherá este arquivo."
    )
    ultima_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuração da Tesouraria'
        verbose_name_plural = 'Configurações da Tesouraria'

    def __str__(self):
        return "Configurações Globais da Tesouraria"
