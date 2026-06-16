"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: almoxarifado/models.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.db import models
from core.models import Membro
from gestao_membros.models import Departamento
from midia_lgpd.models import PastaVirtual
from django.core.validators import FileExtensionValidator
import uuid

img_validators = [FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]

class CategoriaItem(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.nome

class SubcategoriaItem(models.Model):
    nome = models.CharField(max_length=100)
    categoria = models.ForeignKey(CategoriaItem, on_delete=models.CASCADE, related_name='subcategorias')

    class Meta:
        unique_together = ('nome', 'categoria')

    def __str__(self):
        return f"{self.categoria.nome} - {self.nome}"

class ItemAlmoxarifado(models.Model):
    STATUS_CHOICES = (
        ('disponivel', 'Disponível'),
        ('emprestado', 'Emprestado / Em Uso Externo'),
        ('manutencao', 'Em Manutenção'),
        ('consumido', 'Consumido / Esgotado'),
        ('alocado', 'Alocado (Uso Fixo)'),
        ('descartado', 'Descartado / Baixa'),
    )
    ORIGEM_CHOICES = (
        ('comprado', 'Comprado (Igreja)'),
        ('doado', 'Doado (Membros/Terceiros)'),
        ('banco_alimentos', 'Banco de Alimentos Municipal'),
        ('transferido', 'Transferido de Filial'),
        ('desconhecido', 'Legado / Desconhecido'),
    )
    TIPO_CHOICES = (
        ('permanente', 'Ativo Permanente (Devolução Obrigatória)'),
        ('consumo', 'Item de Consumo (Alimentos/Descartáveis)'),
        ('fixo', 'Ativo Fixo (Alocado Permanentemente, não devolvido)'),
    )

    PAGAMENTO_CHOICES = (
        ('quitado', 'Quitado'),
        ('parcelado', 'Parcelado'),
        ('doacao', 'Doação/Grátis'),
        ('nao_se_aplica', 'Não se Aplica')
    )

    CONDICAO_CHOICES = (
        ('nova', 'Nova / Excelente'),
        ('boa', 'Boa'),
        ('regular', 'Regular / Intermediária'),
        ('ruim', 'Ruim')
    )

    # Identificação
    id_unico = models.CharField(max_length=50, unique=True, help_text="ID automático ou Código de Barras manual", blank=True)
    nome = models.CharField(max_length=200, help_text="Ex: Arroz 5kg, Câmera Sony, Microfone Shure")
    categoria = models.ForeignKey(CategoriaItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='itens')
    subcategoria = models.ForeignKey(SubcategoriaItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='itens')
    tipo_item = models.CharField(max_length=20, choices=TIPO_CHOICES, default='permanente')

    # Quantidades e Validade
    quantidade_estoque = models.PositiveIntegerField(default=1)
    data_entrada = models.DateField(auto_now_add=True)
    data_vencimento = models.DateField(null=True, blank=True, help_text="Para alimentos perecíveis")

    # Financeiro e Condição
    valor_monetario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status_pagamento = models.CharField(max_length=20, choices=PAGAMENTO_CHOICES, default='nao_se_aplica')
    condicao_fisica = models.CharField(max_length=20, choices=CONDICAO_CHOICES, default='nova')

    # Fluxo
    origem = models.CharField(max_length=20, choices=ORIGEM_CHOICES, default='desconhecido')
    fornecedor_doador = models.CharField(max_length=200, blank=True, help_text="Loja ou Pessoa que doou")
    localizacao = models.CharField(max_length=150, blank=True, help_text="Ex: Prateleira A, Armário de Som")
    destino_uso = models.CharField(max_length=200, blank=True, help_text="Para onde vai esse item? (Ex: Cestas Básicas, Culto Jovem)")

    # Status e PV Drive
    status_item = models.CharField(max_length=20, choices=STATUS_CHOICES, default='disponivel')
    observacao = models.TextField(blank=True)
    foto_item = models.ImageField(upload_to='fotos/almoxarifado/', blank=True, null=True, validators=img_validators)
    pasta_pv_drive = models.ForeignKey(PastaVirtual, on_delete=models.SET_NULL, null=True, blank=True, help_text="Pasta com todas as NF e comprovantes do item")

    # Controle de Alto Volume
    exige_aprovacao = models.BooleanField(default=False, help_text="Se marcado, a retirada deste item ficará pendente até aprovação de um Gestor.")

    def save(self, *args, **kwargs):
        if not self.id_unico:
            # Auto-generate ID if empty (ALM- + first 8 chars of uuid)
            self.id_unico = f"ALM-{str(uuid.uuid4())[:8].upper()}"

        # If quantity falls to 0, mark as consumed
        if self.quantidade_estoque == 0 and self.status_item != 'consumido':
            self.status_item = 'consumido'

        super().save(*args, **kwargs)

    def is_vencido(self):
        from datetime import date
        if self.data_vencimento:
            return date.today() > self.data_vencimento
        return False

    def __str__(self):
        return f"{self.id_unico} - {self.nome} ({self.quantidade_estoque} un)"


class MovimentacaoAlmoxarifado(models.Model):
    TIPO_MOVIMENTO = (
        ('retirada', 'Retirada (-)'),
        ('devolucao', 'Devolução (+)'),
        ('entrada_estoque', 'Entrada de Estoque (+)'),
        ('baixa', 'Baixa Definitiva (-)'),
    )

    STATUS_APROVACAO = (
        ('aprovado', 'Aprovado / Automático'),
        ('pendente', 'Pendente de Aprovação'),
        ('rejeitado', 'Rejeitado'),
    )

    item = models.ForeignKey(ItemAlmoxarifado, on_delete=models.CASCADE, related_name='movimentacoes')
    tipo = models.CharField(max_length=20, choices=TIPO_MOVIMENTO)
    quantidade = models.PositiveIntegerField(default=1)

    # Rastreio de quem retirou (Zero-Trust + Fuzzy)
    nome_digitado = models.CharField(max_length=200, help_text="Nome digitado no QR Code Público")
    email_digitado = models.EmailField(blank=True, null=True, help_text="Email para envio do Termo de Cautela Automático")
    membro_vinculado = models.ForeignKey(Membro, on_delete=models.SET_NULL, null=True, blank=True, help_text="Membro vinculado via IA/Fuzzy Match")

    status_aprovacao = models.CharField(max_length=20, choices=STATUS_APROVACAO, default='aprovado')
    data_hora = models.DateTimeField(auto_now_add=True)
    assinatura_digital_hash = models.CharField(max_length=256, editable=False, help_text="Hash SHA-256 de segurança")
    observacao = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new:
            import hashlib
            raw_data = f"{self.item.id_unico}|{self.tipo}|{self.quantidade}|{self.nome_digitado}|{self.data_hora}"
            self.assinatura_digital_hash = hashlib.sha256(raw_data.encode('utf-8')).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.quantidade}x {self.item.nome} por {self.nome_digitado}"
