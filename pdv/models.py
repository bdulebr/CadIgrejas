from django.db import models
from core.models import Membro
import hashlib
import json

class CategoriaProduto(models.Model):
    nome = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = 'Categorias de Produtos'

    def __str__(self):
        return self.nome

class Fornecedor(models.Model):
    razao_social = models.CharField(max_length=200)
    cnpj = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Fornecedores'

    def __str__(self):
        return self.razao_social

class Cliente(models.Model):
    nome = models.CharField(max_length=200)
    cpf = models.CharField(max_length=20, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    anotacoes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return self.nome

class Produto(models.Model):
    nome = models.CharField(max_length=200)
    codigo_barras = models.CharField(max_length=100, unique=True, blank=True, null=True)
    categoria = models.ForeignKey(CategoriaProduto, on_delete=models.SET_NULL, null=True, blank=True)
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    estoque_atual = models.IntegerField(default=0)
    estoque_minimo = models.IntegerField(default=5)

    # Fiscal data for NFC-e readiness
    ncm = models.CharField(max_length=20, blank=True, null=True)
    cest = models.CharField(max_length=20, blank=True, null=True)
    cfop = models.CharField(max_length=10, blank=True, null=True)
    icms_cst = models.CharField(max_length=5, blank=True, null=True)

    def __str__(self):
        return f"{self.codigo_barras} - {self.nome}"

class Caixa(models.Model):
    STATUS_CHOICES = (
        ('aberto', 'Aberto'),
        ('fechado', 'Fechado')
    )
    operador = models.ForeignKey(Membro, on_delete=models.CASCADE)
    data_abertura = models.DateTimeField(auto_now_add=True)
    data_fechamento = models.DateTimeField(blank=True, null=True)
    saldo_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    saldo_final_esperado = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    saldo_final_real = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aberto')

    def __str__(self):
        return f"Caixa {self.id} - {self.operador.username} ({self.status})"

class Venda(models.Model):
    STATUS_CHOICES = (
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
        ('aguardando', 'Aguardando')
    )
    caixa = models.ForeignKey(Caixa, on_delete=models.CASCADE, related_name='vendas')
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    data_venda = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    forma_pagamento = models.CharField(max_length=50, default='Dinheiro')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='concluida')

    # Fiscal NFC-e
    chave_acesso_nfce = models.CharField(max_length=100, blank=True, null=True)
    protocolo_autorizacao = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Venda {self.id} - R$ {self.total}"

class ItemVenda(models.Model):
    venda = models.ForeignKey(Venda, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.IntegerField(default=1)
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name_plural = 'Itens de Venda'

class MovimentoCaixa(models.Model):
    TIPO_CHOICES = (
        ('entrada', 'Entrada (Suprimento/Venda)'),
        ('saida', 'Saída (Sangria/Despesa)')
    )
    caixa = models.ForeignKey(Caixa, on_delete=models.CASCADE, related_name='movimentos')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.CharField(max_length=200)
    data_movimento = models.DateTimeField(auto_now_add=True)

class ConfiguracaoPDV(models.Model):
    ativo = models.BooleanField(default=True)
    imprimir_recibo_automatico = models.BooleanField(default=False)

    # Controle de Acesso
    lider = models.ForeignKey('core.Membro', on_delete=models.SET_NULL, null=True, blank=True, related_name='pdv_lider_config')
    operadores = models.ManyToManyField('core.Membro', blank=True, related_name='pdv_operadores_config')

    # Módulo Fiscal NFC-e
    nfce_ativado = models.BooleanField(default=False, help_text="Se ativado, requer certificado e comunica com SEFAZ")
    certificado_a1 = models.FileField(upload_to='certificados/', blank=True, null=True)
    senha_certificado = models.CharField(max_length=100, blank=True, null=True)
    csc_id = models.CharField(max_length=10, blank=True, null=True, help_text="ID do CSC para QR Code NFC-e")
    csc_codigo = models.CharField(max_length=100, blank=True, null=True, help_text="Código CSC")

    def __str__(self):
        return "Configurações Globais PDV"
