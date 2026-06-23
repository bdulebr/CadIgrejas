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
        ('pendente', 'Pendente de Aprovação'),
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
    apelido = models.CharField(max_length=50, null=True, blank=True, help_text="Apelido ou nome comum pelo qual é conhecido (ajuda a Inteligência Artificial)")
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

    def __str__(self):
        nome_base = self.get_full_name() or self.username
        if self.apelido:
            return f"{nome_base} ({self.apelido})"
        return nome_base

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
                    import threading
                    def fetch_geoip_async(ip):
                        import requests
                        try:
                            resp = requests.get(f'http://ip-api.com/json/{ip}', timeout=2.0)
                            if resp.status_code == 200:
                                data = resp.json()
                                if data.get('status') == 'success':
                                    cidade = f"{data.get('city', '')} - {data.get('region', '')}"[:100]
                                    isp = data.get('isp', '')[:145]
                                    LogAuditoria.objects.filter(ip_origem=ip, cidade_origem__isnull=True).update(
                                        cidade_origem=cidade, isp_origem=isp
                                    )
                        except Exception:
                            pass

                    threading.Thread(target=fetch_geoip_async, args=(self.ip_origem,)).start()

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
    intervalo_reenvio_emails_horas = models.IntegerField(default=1, help_text="Intervalo automático (em horas) para tentar reenviar e-mails que falharam.")

    # API WhatsApp (Meta Cloud)
    whatsapp_ativo = models.BooleanField(default=False, help_text="Master switch. Se falso, nenhum WhatsApp será disparado.")
    intervalo_reenvio_whatsapp_horas = models.IntegerField(default=1, help_text="Intervalo automático (em horas) para tentar reenviar whatsapps que falharam.")
    whatsapp_phone_number_id = models.CharField(max_length=100, null=True, blank=True, help_text="ID do Número de Telefone (Meta Cloud API)")
    whatsapp_access_token = models.CharField(max_length=500, null=True, blank=True, help_text="Token de Acesso Permanente (Meta Cloud API)")
    whatsapp_verify_token = models.CharField(max_length=100, null=True, blank=True, help_text="Verify Token (Webhook Challenge)")
    whatsapp_app_secret = models.CharField(max_length=100, null=True, blank=True, help_text="App Secret (Webhook HMAC SHA256)")

    class Meta:
        verbose_name = 'Configuração do Sistema'
        verbose_name_plural = 'Configurações do Sistema'

    def __str__(self):
        return f"Configurações Gerais (Manutenção: {self.is_maintenance})"

class NoticiaTicker(models.Model):
    titulo = models.CharField(max_length=100, default='Destaque', help_text="Título da notícia")
    mensagem = models.TextField(help_text="Conteúdo da notícia", default='')
    ativo = models.BooleanField(default=True)
    ordem = models.IntegerField(default=0, help_text="Ordem de exibição")

    class Meta:
        verbose_name = 'Notícia Global (Dashboard)'
        verbose_name_plural = 'Notícias Globais (Dashboard)'
        ordering = ['ordem']

    def __str__(self):
        return self.titulo


class LinkRapido(models.Model):
    VISIBILIDADE_CHOICES = (
        ('geral', 'Todos os Usuários'),
        ('membros', 'Apenas Membros e Acima'),
        ('lideres', 'Líderes e Acima'),
        ('admin', 'Somente Administradores'),
    )

    titulo = models.CharField(max_length=50)
    url = models.CharField(max_length=255)
    icone_svg = models.TextField(blank=True, help_text="Código SVG do ícone")
    ordem = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    visibilidade = models.CharField(max_length=20, choices=VISIBILIDADE_CHOICES, default='geral')

    class Meta:
        ordering = ['ordem']
        verbose_name = 'Link Rápido'
        verbose_name_plural = 'Links Rápidos'

    def __str__(self):
        return self.titulo

class NotificacaoGlobal(models.Model):
    TIPO_CHOICES = (
        ('info', 'Informação'),
        ('success', 'Sucesso'),
        ('warning', 'Aviso'),
        ('error', 'Erro'),
        ('upload_ia', 'Upload IA'),
    )

    destinatario = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='notificacoes')
    remetente = models.ForeignKey(Membro, on_delete=models.SET_NULL, null=True, blank=True, related_name='notificacoes_enviadas')
    titulo = models.CharField(max_length=200)
    mensagem = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='info')
    link_acao = models.CharField(max_length=500, blank=True, null=True, help_text="URL para onde a notificação redireciona")
    lida = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_criacao']

    def __str__(self):
        return f"{self.titulo} para {self.destinatario.username}"


class EmailLog(models.Model):
    STATUS_CHOICES = [
        ('enviado', 'Enviado'),
        ('pendente', 'Pendente'),
        ('falha', 'Falha ao Enviar'),
    ]

    destinatario = models.EmailField()
    assunto = models.CharField(max_length=255)
    corpo_html = models.TextField(blank=True, null=True, help_text="Cópia do HTML para permitir reenvio")
    anexos_json = models.TextField(blank=True, null=True, help_text="Lista serializada de caminhos de anexos")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    qtd_reenvios = models.IntegerField(default=0, help_text="Quantas vezes o sistema tentou reenviar")
    data_envio = models.DateTimeField(auto_now_add=True)
    erro_mensagem = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Log de E-mail'
        verbose_name_plural = 'Logs de E-mails'
        ordering = ['-data_envio']

    def __str__(self):
        return f"[{self.get_status_display()}] {self.assunto} -> {self.destinatario}"


class LogWhatsApp(models.Model):
    STATUS_CHOICES = [
        ('enviado', 'Enviado'),
        ('pendente', 'Pendente'),
        ('falha', 'Falha ao Enviar'),
    ]

    destinatario_numero = models.CharField(max_length=30)
    template_usado = models.CharField(max_length=150, help_text="Nome do template na Meta ou tipo de envio")
    corpo_json = models.TextField(blank=True, null=True, help_text="Payload original em JSON para reenvio exato")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    qtd_reenvios = models.IntegerField(default=0, help_text="Quantas vezes o sistema tentou reenviar")
    data_envio = models.DateTimeField(auto_now_add=True)
    erro_mensagem = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Log de WhatsApp'
        verbose_name_plural = 'Logs de WhatsApp'
        ordering = ['-data_envio']

    def __str__(self):
        return f"[{self.get_status_display()}] {self.template_usado} -> {self.destinatario_numero}"


class DatabaseBackup(models.Model):
    arquivo = models.CharField(max_length=500, help_text="Caminho físico do arquivo de backup.")
    tamanho_mb = models.DecimalField(max_digits=10, decimal_places=2, help_text="Tamanho do arquivo em MB.")
    data_criacao = models.DateTimeField(auto_now_add=True)
    enviado_nuvem = models.BooleanField(default=False, help_text="Indica se o backup já foi enviado para a nuvem.")
    gdrive_file_id = models.CharField(max_length=255, blank=True, null=True, help_text="ID do arquivo no Google Drive.")

    class Meta:
        verbose_name = 'Backup de Banco de Dados'
        verbose_name_plural = 'Backups de Banco de Dados'
        ordering = ['-data_criacao']

    def __str__(self):
        return f"Backup {self.data_criacao.strftime('%d/%m/%Y %H:%M:%S')} - {self.tamanho_mb}MB"


class SpiderTestLog(models.Model):
    data_execucao = models.DateTimeField(auto_now_add=True)
    iniciado_por = models.ForeignKey('Membro', on_delete=models.SET_NULL, null=True, blank=True)
    total_urls = models.IntegerField(default=0)
    erros_encontrados = models.IntegerField(default=0)
    log_texto = models.TextField()

    def __str__(self):
        return f"Spider Test #{self.id} - {self.data_execucao.strftime('%d/%m/%Y %H:%M')}"

class AIEngineerLog(models.Model):
    data_execucao = models.DateTimeField(auto_now_add=True)
    erro_analisado = models.TextField()
    arquivo_modificado = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=50) # 'SUCESSO', 'ROLLBACK', 'ERRO'
    detalhes = models.TextField()

    def __str__(self):
        return f"AI Engineer #{self.id} - {self.status} em {self.data_execucao.strftime('%d/%m/%Y %H:%M')}"


import hashlib

class LogImutavel(models.Model):
    membro = models.ForeignKey(Membro, on_delete=models.SET_NULL, null=True)
    acao = models.CharField(max_length=255)
    dados_acao = models.TextField()
    hash_anterior = models.CharField(max_length=64, blank=True, null=True)
    hash_atual = models.CharField(max_length=64, unique=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log Imutável (Zero-Trust)'
        verbose_name_plural = 'Logs Imutáveis (Zero-Trust)'
        ordering = ['-id']

    def save(self, *args, **kwargs):
        if not self.hash_atual:
            last_log = LogImutavel.objects.order_by('-id').first()
            self.hash_anterior = last_log.hash_atual if last_log else "GENESIS"

            data_to_hash = f"{self.membro.id if self.membro else 'SYS'}|{self.acao}|{self.dados_acao}|{self.hash_anterior}"
            self.hash_atual = hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest()
        super().save(*args, **kwargs)
