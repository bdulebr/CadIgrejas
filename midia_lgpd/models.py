"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: midia_lgpd/models.py
* DESCRIÇÃO: Entidades de arquivos de mídia e termos de LGPD
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 25/05/2026 14:10
* LOG DE ALTERAÇÕES:
* - 25/05/2026 14:10: Criação inicial
"""

from django.db import models
from core.models import Membro
from gestao_membros.models import Departamento
import uuid

class TermoLGPD(models.Model):
    titulo = models.CharField(max_length=200, help_text="Ex: Termo de Uso de Imagem v1")
    conteudo_juridico = models.TextField(help_text="Texto completo do termo para o membro ler")
    data_publicacao = models.DateTimeField(auto_now_add=True)
    is_ativo = models.BooleanField(default=True, help_text="Apenas um termo deve estar ativo por vez")

    def __str__(self):
        return f"{self.titulo} - {'(Ativo)' if self.is_ativo else '(Obsoleto)'}"

    def save(self, *args, **kwargs):
        if self.is_ativo:
            TermoLGPD.objects.filter(is_ativo=True).update(is_ativo=False)
        super().save(*args, **kwargs)

class AssinaturaLGPD(models.Model):
    membro = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='assinaturas_lgpd')
    termo = models.ForeignKey(TermoLGPD, on_delete=models.RESTRICT)
    data_aceite = models.DateTimeField(auto_now_add=True)
    ip_registro = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        unique_together = ('membro', 'termo')

    def __str__(self):
        return f"{self.membro.first_name} aceitou {self.termo.titulo}"

class PastaVirtual(models.Model):
    nome = models.CharField(max_length=100)
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='pastas')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subpastas')
    criado_por = models.ForeignKey(Membro, on_delete=models.SET_NULL, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    is_excluida = models.BooleanField(default=False)
    data_exclusao = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        if self.parent:
            return f"{self.parent.nome} / {self.nome} ({self.departamento.nome})"
        return f"{self.nome} ({self.departamento.nome})"

class CompartilhamentoPasta(models.Model):
    pasta = models.ForeignKey(PastaVirtual, on_delete=models.CASCADE, related_name='compartilhamentos')
    departamento_destino = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='pastas_compartilhadas')
    criado_por = models.ForeignKey(Membro, on_delete=models.SET_NULL, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    validade = models.DateTimeField(null=True, blank=True)
    is_ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.pasta.nome} -> {self.departamento_destino.nome}"

class ArquivoMidia(models.Model):
    titulo = models.CharField(max_length=200)
    arquivo = models.FileField(upload_to='arquivos/%Y/%m/')
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='arquivos_midia')
    pasta = models.ForeignKey(PastaVirtual, on_delete=models.CASCADE, related_name='arquivos', null=True, blank=True)
    enviado_por = models.ForeignKey(Membro, on_delete=models.SET_NULL, null=True)
    data_envio = models.DateTimeField(auto_now_add=True)
    tamanho_bytes = models.BigIntegerField(default=0)
    extensao = models.CharField(max_length=20, blank=True)
    hash_sha256 = models.CharField(max_length=64, blank=True)
    is_publico_para_membros = models.BooleanField(default=False, help_text="Se marcado, voluntários comuns do setor poderão baixar o arquivo")
    is_excluido = models.BooleanField(default=False)
    data_exclusao = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.titulo

class DocumentoTemplate(models.Model):
    titulo = models.CharField(max_length=200, help_text="Ex: Autorização de Acampamento")
    descricao = models.TextField(blank=True, null=True)
    conteudo_base = models.TextField(help_text="Corpo do contrato/documento. Use {{NOME}} para variáveis.")
    campos_json = models.JSONField(default=list, help_text="Lista de campos: [{'nome': 'NOME', 'tipo': 'text', 'label': 'Nome Completo'}]")
    html_canva = models.TextField(blank=True, help_text="Estrutura HTML do Editor Canva")
    css_canva = models.TextField(blank=True, help_text="Estilos CSS do Editor Canva")
    json_canva = models.JSONField(null=True, blank=True, help_text="Grafo de elementos GrapesJS/Fabric")
    criado_por = models.ForeignKey(Membro, on_delete=models.SET_NULL, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.titulo

class DocumentoGerado(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente de Assinatura'),
        ('assinado', 'Assinado/Concluído'),
        ('cancelado', 'Cancelado')
    ]
    
    template = models.ForeignKey(DocumentoTemplate, on_delete=models.RESTRICT, related_name='documentos_gerados')
    token_acesso = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email_destino = models.EmailField(help_text="E-mail que receberá o link para assinatura")
    nome_destino = models.CharField(max_length=200, blank=True, null=True)
    solicitado_por = models.ForeignKey(Membro, on_delete=models.SET_NULL, null=True, related_name='documentos_solicitados')
    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    dados_preenchidos = models.JSONField(default=dict, blank=True, null=True)
    
    arquivo_pdf_final = models.FileField(upload_to='documentos_assinados/%Y/%m/', null=True, blank=True)
    anexo_fisico_escaneado = models.FileField(upload_to='documentos_escaneados/%Y/%m/', null=True, blank=True)
    
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_assinatura = models.DateTimeField(null=True, blank=True)
    ip_assinatura = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.template.titulo} para {self.email_destino} - {self.get_status_display()}"

