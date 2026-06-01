"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: core/models.py
* DESCRIÇÃO: Modelos base do sistema, usuários e auditoria (Zero-Trust).
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 25/05/2026 13:42
* LOG DE ALTERAÇÕES:
* - 25/05/2026 13:42: Criação inicial
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
import hashlib
import json

from django.core.validators import FileExtensionValidator

class Membro(AbstractUser):
    NIVEL_CHOICES = (
        ('super_admin', 'Super-admin'),
        ('pastor_regente', 'Pastor Regente'),
        ('pastor', 'Pastor'),
        ('missionario', 'Missionário'),
        ('lider', 'Líder'),
        ('sub_lider', 'Sub-líder'),
        ('membro_voluntario', 'Membro Voluntário'),
    )

    STATUS_CHOICES = (
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
        ('bloqueado', 'Bloqueado'),
        ('transferido', 'Transferido'),
        ('falecido', 'Falecido'),
    )

    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True)
    rg = models.CharField(max_length=20, null=True, blank=True)
    telefone = models.CharField(max_length=20, null=True, blank=True)
    foto_perfil = models.ImageField(upload_to='perfil/', null=True, blank=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])])

    # Dados Pessoais Adicionais
    sexo = models.CharField(max_length=20, choices=(('Masculino', 'Masculino'), ('Feminino', 'Feminino'), ('Outro', 'Outro')), null=True, blank=True)
    estado_civil = models.CharField(max_length=50, null=True, blank=True)
    profissao = models.CharField(max_length=100, null=True, blank=True)
    escolaridade = models.CharField(max_length=100, null=True, blank=True)

    data_nascimento = models.DateField(null=True, blank=True)
    data_casamento = models.DateField(null=True, blank=True)
    conjuge = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    filhos = models.TextField(blank=True, help_text="Nomes dos filhos separados por vírgula")
    habilidades = models.ManyToManyField('gestao_membros.Habilidade', blank=True, related_name='membros')

    # Endereço
    cep = models.CharField(max_length=10, null=True, blank=True)
    endereco = models.CharField(max_length=200, null=True, blank=True)
    numero = models.CharField(max_length=20, null=True, blank=True)
    complemento = models.CharField(max_length=100, null=True, blank=True)
    bairro = models.CharField(max_length=100, null=True, blank=True)
    cidade = models.CharField(max_length=100, null=True, blank=True)
    estado = models.CharField(max_length=2, null=True, blank=True)

    # Histórico Eclesiástico
    data_batismo = models.DateField(null=True, blank=True)
    membro_desde = models.DateField(null=True, blank=True)
    igreja_anterior = models.CharField(max_length=200, null=True, blank=True)

    # Extras
    redes_sociais = models.CharField(max_length=200, null=True, blank=True, help_text="Ex: @instagram")
    tamanho_camisa = models.CharField(max_length=10, choices=(('PP', 'PP'), ('P', 'P'), ('M', 'M'), ('G', 'G'), ('GG', 'GG'), ('XG', 'XG'), ('XXG', 'XXG')), null=True, blank=True)
    alergias = models.TextField(blank=True, help_text="Alergias ou restrições alimentares/médicas")
    contato_emergencia = models.CharField(max_length=100, null=True, blank=True, help_text="Nome e telefone para emergências")

    nivel_hierarquico = models.CharField(max_length=30, choices=NIVEL_CHOICES, default='membro_voluntario')
    pin_pdv = models.CharField(max_length=4, blank=True, null=True, help_text='PIN de 4 dígitos para acesso rápido ao Caixa PDV')
    status_conta = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')

    # LGPD
    termos_aceitos = models.BooleanField(default=False)
    hash_aceite_lgpd = models.CharField(max_length=256, null=True, blank=True, editable=False)
    data_aceite = models.DateTimeField(null=True, blank=True)

    # Trabalho e Estudo (Disponibilidade)
    horario_trabalho_inicio = models.TimeField(null=True, blank=True, help_text="Início do expediente de trabalho ou estudo")
    horario_trabalho_fim = models.TimeField(null=True, blank=True, help_text="Fim do expediente de trabalho ou estudo")
    dias_trabalho = models.CharField(max_length=50, blank=True, help_text="Dias trabalhados separados por vírgula (0=Seg, 6=Dom)")
    dias_folga = models.CharField(max_length=50, blank=True, help_text="Dias de folga separados por vírgula (0=Seg, 6=Dom)")
    anotacoes_lideranca = models.TextField(blank=True, help_text="Anotações privadas da liderança sobre o membro")

    def __str__(self):
        return self.get_full_name() or self.username

    def save(self, *args, **kwargs):
        if self.status_conta == 'ativo':
            self.is_active = True
        else:
            self.is_active = False
        super().save(*args, **kwargs)


class DiaIndisponivel(models.DateField):
    membro = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='dias_indisponiveis')
    data = models.DateField()

    class Meta:
        unique_together = ('membro', 'data')

    def __str__(self):
        return f"{self.membro} indisponível em {self.data}"


class LogAuditoria(models.Model):
    usuario_acao = models.ForeignKey(Membro, on_delete=models.SET_NULL, null=True)
    acao_realizada = models.CharField(max_length=50) # Criar, Editar, Deletar, UX_Intent
    tabela_afetada = models.CharField(max_length=100)

    # Rastreio Avançado
    ip_origem = models.GenericIPAddressField(null=True, blank=True)
    cidade_origem = models.CharField(max_length=100, null=True, blank=True)
    isp_origem = models.CharField(max_length=150, null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)

    data_hora = models.DateTimeField(auto_now_add=True)
    diferenca_json = models.JSONField()

    # Zero-Trust Hash Chain (Blockchain-like)
    hash_anterior = models.CharField(max_length=256, null=True, blank=True, editable=False)
    hash_atual = models.CharField(max_length=256, editable=False)

    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'

    def save(self, *args, **kwargs):
        if not self.pk:
            from core.middleware import get_current_request
            import requests

            req = get_current_request()
            if req and not self.ip_origem:
                x_forwarded_for = req.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    self.ip_origem = x_forwarded_for.split(',')[0].strip()
                else:
                    self.ip_origem = req.META.get('REMOTE_ADDR')

                self.user_agent = req.META.get('HTTP_USER_AGENT', '')[:250]

                # Fetch GeoIP inline
                if self.ip_origem and self.ip_origem not in ['127.0.0.1', 'localhost']:
                    try:
                        resp = requests.get(f'http://ip-api.com/json/{self.ip_origem}', timeout=1.0)
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get('status') == 'success':
                                self.cidade_origem = f"{data.get('city', '')} - {data.get('region', '')}"[:100]
                                self.isp_origem = data.get('isp', '')[:145]
                    except Exception:
                        pass

            ultimo_log = LogAuditoria.objects.order_by('-id').first()
            if ultimo_log:
                self.hash_anterior = ultimo_log.hash_atual
            else:
                self.hash_anterior = "GENESIS_BLOCK"

            dados_str = f"{self.usuario_acao_id}{self.acao_realizada}{self.tabela_afetada}{self.data_hora}{self.diferenca_json}{self.hash_anterior}"
            self.hash_atual = hashlib.sha256(dados_str.encode()).hexdigest()
        super().save(*args, **kwargs)

class ConfiguracaoSistema(models.Model):
    is_maintenance = models.BooleanField(default=False)
    ultima_atualizacao = models.DateTimeField(auto_now=True)

    # Informações da Igreja (Globais)
    igreja_nome = models.CharField(max_length=150, default="PV Enseada", help_text="Nome Real ou Razão Social (Usado no topo e painéis)")
    nome_fantasia = models.CharField(max_length=150, null=True, blank=True, help_text="Nome Fantasia (Usado nos Títulos/Abas do navegador)")
    cnpj = models.CharField(max_length=20, null=True, blank=True, help_text="CNPJ da Instituição")
    endereco = models.TextField(null=True, blank=True, help_text="Endereço Completo para Rodapés e Recibos")

    # Mídias e Branding
    igreja_logo = models.ImageField(upload_to='logos/', null=True, blank=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'svg', 'webp'])])
    favicon = models.ImageField(upload_to='logos/', null=True, blank=True, validators=[FileExtensionValidator(allowed_extensions=['ico', 'png', 'jpg', 'jpeg', 'svg'])], help_text="Ícone pequeno exibido na aba do navegador")

    lider_global_escalas = models.ForeignKey('Membro', on_delete=models.SET_NULL, null=True, blank=True, related_name='lider_global_de_escalas', help_text="Pessoa responsável pela gestão global de todas as escalas.")

    # Motor Global de Emails
    envios_email_ativos = models.BooleanField(default=True, help_text="Master switch. Se falso, nenhum email será disparado (modo silencioso/manutenção).")

    class Meta:
        verbose_name = 'Configuração do Sistema'
        verbose_name_plural = 'Configurações do Sistema'

    def __str__(self):
        return f"Configurações Gerais (Manutenção: {self.is_maintenance})"

class NoticiaTicker(models.Model):
    texto = models.CharField(max_length=255, help_text="Ex: CULTOS AOS DOMINGOS 09:30 E 19:30")
    ativo = models.BooleanField(default=True)
    ordem = models.IntegerField(default=0, help_text="Ordem de exibição")

    class Meta:
        verbose_name = 'Notícia Plantão (Letreiro)'
        verbose_name_plural = 'Notícias Plantão (Letreiro)'
        ordering = ['ordem']

    def __str__(self):
        return self.texto


class TemplateDocumento(models.Model):
    TIPO_CHOICES = (
        ('email', 'E-mail'),
        ('pdf', 'PDF / Relatório'),
    )

    nome_acao = models.CharField(max_length=100, unique=True, help_text="Ex: escala_publicada, bem_vindo, termo_emprestimo")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='email')
    assunto_padrao = models.CharField(max_length=255, null=True, blank=True, help_text="Usado apenas se for E-mail")

    # Armazena o código gerado pelo GrapesJS
    html_content = models.TextField(blank=True)
    css_content = models.TextField(blank=True)
    components_json = models.JSONField(null=True, blank=True, help_text="Estrutura de blocos do GrapesJS")

    # Dicas pro admin
    variaveis_disponiveis = models.TextField(blank=True, help_text="Ex: {{ nome }}, {{ departamento.logo.url }}")

    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Template Dinâmico'
        verbose_name_plural = 'Templates Dinâmicos'

    def __str__(self):
        return f"{self.nome_acao} ({self.get_tipo_display()})"

class LinkRapido(models.Model):
    titulo = models.CharField(max_length=50)
    url = models.CharField(max_length=255)
    icone_svg = models.TextField(blank=True, help_text="Código SVG do ícone")
    ordem = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['ordem']
        verbose_name = 'Link Rápido'
        verbose_name_plural = 'Links Rápidos'

    def __str__(self):
        return self.titulo
