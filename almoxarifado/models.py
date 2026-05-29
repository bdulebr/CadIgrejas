"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: almoxarifado/models.py
* DESCRIÇÃO: Entidades do sistema de rastreio de patrimônio e equipamentos
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 25/05/2026 14:03
* LOG DE ALTERAÇÕES:
* - 25/05/2026 14:03: Criação inicial das tabelas
"""

from django.db import models
from core.models import Membro
from gestao_membros.models import Departamento
from django.core.validators import FileExtensionValidator

img_validators = [FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
doc_validators = [FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx'])]

class CategoriaAtivo(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return self.nome

class SubCategoriaAtivo(models.Model):
    categoria = models.ForeignKey(CategoriaAtivo, on_delete=models.CASCADE, related_name='subcategorias')
    nome = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.nome} ({self.categoria.nome})"

class Ativo(models.Model):
    STATUS_CHOICES = (
        ('disponivel', 'Disponível'),
        ('em_uso_fixo', 'Em Uso Fixo / Local'),
        ('emprestado', 'Emprestado'),
        ('manutencao', 'Em Manutenção'),
        ('quebrado', 'Danificado / Quebrado'),
    )
    ORIGEM_CHOICES = (
        ('comprado', 'Comprado'),
        ('doado', 'Doado'),
        ('transferido', 'Transferido (Filial)'),
        ('desconhecido', 'Desconhecido / Legado'),
    )

    nome = models.CharField(max_length=200)
    codigo_patrimonio = models.CharField(max_length=50, unique=True, help_text="Código único de barra ou serial")
    
    # Manter o texto por retrocompatibilidade e adicionar os relacional
    categoria = models.CharField(max_length=100, default="Geral")
    categoria_obj = models.ForeignKey(CategoriaAtivo, on_delete=models.SET_NULL, null=True, blank=True, related_name='ativos')
    subcategoria_obj = models.ForeignKey(SubCategoriaAtivo, on_delete=models.SET_NULL, null=True, blank=True, related_name='ativos')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='disponivel')
    
    origem = models.CharField(max_length=20, choices=ORIGEM_CHOICES, default='desconhecido')
    fornecedor_doador = models.CharField(max_length=200, blank=True, help_text="Loja de compra ou nome do doador")
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Valor monetário (R$)")
    
    anexo_comprovante = models.FileField(upload_to='comprovantes/ativos/', blank=True, null=True, help_text="Nota fiscal ou recibo", validators=doc_validators)
    foto_item = models.ImageField(upload_to='fotos/ativos/', blank=True, null=True, help_text="Foto real do equipamento", validators=img_validators)
    
    departamento_dono = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='ativos')
    localizacao = models.CharField(max_length=150, blank=True, help_text="Se estiver em Uso Fixo, qual é a sala/local?")
    
    data_aquisicao = models.DateField(auto_now_add=True)
    data_ultima_manutencao = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.nome} ({self.codigo_patrimonio})"

class Emprestimo(models.Model):
    ativo = models.ForeignKey(Ativo, on_delete=models.CASCADE, related_name='historico_emprestimos')
    membro_solicitante = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='itens_emprestados')
    
    data_retirada = models.DateTimeField(auto_now_add=True)
    data_devolucao_prevista = models.DateField()
    data_devolucao_real = models.DateTimeField(null=True, blank=True)
    
    observacao = models.TextField(blank=True, null=True, help_text="Anotações de defeitos ou estado do item na retirada")
    
    def __str__(self):
        return f"{self.ativo.nome} - {self.membro_solicitante.first_name}"

class AlimentoLote(models.Model):
    ORIGEM_CHOICES = (
        ('comprado', 'Comprado (Nota Fiscal)'),
        ('doado', 'Doado (Membro/Instituição)'),
        ('banco_alimentos', 'Banco de Alimentos Municipal'),
    )

    nome = models.CharField(max_length=150, help_text="Ex: Arroz 5kg, Feijão Preto")
    quantidade_inicial = models.PositiveIntegerField(help_text="Quantidade original", default=1)
    quantidade_atual = models.PositiveIntegerField(help_text="Quantidade restante", default=1)
    
    origem = models.CharField(max_length=20, choices=ORIGEM_CHOICES, default='doado')
    fornecedor_doador = models.CharField(max_length=200, blank=True, help_text="Nome do supermercado ou pessoa/instituição doadora")
    localizacao = models.CharField(max_length=150, blank=True, help_text="Ex: Prateleira B, Geladeira 1")
    foto_lote = models.ImageField(upload_to='fotos/alimentos/', blank=True, null=True, validators=img_validators)
    
    data_vencimento = models.DateField(null=True, blank=True)
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='lotes_alimentos', null=True)
    
    anexo_nota_fiscal = models.FileField(upload_to='comprovantes/alimentos_lotes/', null=True, blank=True, help_text="Nota Fiscal de compra ou termo de doação do lote todo.", validators=doc_validators)
    
    data_cadastro = models.DateTimeField(auto_now_add=True)
    observacoes = models.TextField(blank=True)

    def is_vencido(self):
        from datetime import date
        return date.today() > self.data_vencimento

    def __str__(self):
        return f"{self.nome} ({self.quantidade_atual} un) - Vence: {self.data_vencimento}"

class TransacaoAlimento(models.Model):
    TIPO_CHOICES = (
        ('entrada', 'Entrada (+)'),
        ('saida', 'Saída / Consumo (-)'),
    )
    
    lote = models.ForeignKey(AlimentoLote, on_delete=models.CASCADE, related_name='transacoes')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    quantidade = models.PositiveIntegerField()
    destino_origem = models.CharField(max_length=200, help_text="Para quem foi entregue? (Saída) ou Quem repôs? (Entrada)")
    observacao = models.TextField(blank=True)
    
    anexo_comprovante = models.FileField(upload_to='comprovantes/alimentos/', blank=True, null=True, help_text="Foto do recibo ou assinatura da família", validators=doc_validators)
    membro_responsavel = models.ForeignKey(Membro, on_delete=models.CASCADE)
    data_transacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.tipo.upper()}] {self.quantidade} un de {self.lote.nome}"

class Manutencao(models.Model):
    ativo = models.ForeignKey(Ativo, on_delete=models.CASCADE, related_name='historico_manutencoes')
    data_envio = models.DateField(auto_now_add=True)
    data_retorno_prevista = models.DateField(null=True, blank=True)
    data_retorno_real = models.DateField(null=True, blank=True)
    
    custo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    oficina_tecnico = models.CharField(max_length=200, help_text="Nome da oficina ou pessoa responsável pelo conserto")
    
    descricao_problema = models.TextField()
    solucao_aplicada = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Manutenção: {self.ativo.nome} em {self.data_envio}"
