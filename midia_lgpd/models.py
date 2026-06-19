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
    TIPO_CHOICES = [
        ('membro', 'Membro / Voluntário'),
        ('visitante', 'Visitante Geral'),
        ('crianca', 'Criança / Menor de Idade'),
    ]
    titulo = models.CharField(max_length=200, help_text="Ex: Termo de Uso de Imagem v1")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='membro')
    conteudo_juridico = models.TextField(help_text="Texto completo do termo para o membro ler")
    data_publicacao = models.DateTimeField(auto_now_add=True)
    is_ativo = models.BooleanField(default=True, help_text="Apenas um termo ativo por tipo")

    def __str__(self):
        return f"{self.titulo} - {self.get_tipo_display()} {'(Ativo)' if self.is_ativo else '(Obsoleto)'}"

    def save(self, *args, **kwargs):
        if self.is_ativo:
            TermoLGPD.objects.filter(tipo=self.tipo, is_ativo=True).update(is_ativo=False)
        super().save(*args, **kwargs)

class AssinaturaLGPD(models.Model):
    # LEGADO: Mantido apenas por histórico antigo
    membro = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='assinaturas_lgpd')
    termo = models.ForeignKey(TermoLGPD, on_delete=models.RESTRICT)
    data_aceite = models.DateTimeField(auto_now_add=True)
    ip_registro = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.membro.first_name} aceitou {self.termo.titulo}"

class RegistroAceiteLGPD(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aceito', 'Aceito'),
        ('recusado', 'Recusado')
    ]

    # Vínculo com a intranet (se houver)
    membro = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='aceites_lgpd_v2', null=True, blank=True)

    # Dados da pessoa (Preenchidos pela mídia ou pelo sistema)
    nome_completo = models.CharField('Nome Completo', max_length=255)
    cpf = models.CharField('CPF', max_length=20, blank=True, null=True)
    email = models.EmailField('E-mail', blank=True, null=True)

    # Caso seja criança
    nome_crianca = models.CharField('Nome da Criança (Opcional)', max_length=255, blank=True, null=True)

    termo = models.ForeignKey(TermoLGPD, on_delete=models.RESTRICT)
    token_acesso = models.UUIDField(default=uuid.uuid4, unique=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pendente')

    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_resposta = models.DateTimeField(null=True, blank=True)
    ip_registro = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)

    arquivo_pdf = models.FileField('PDF Gerado', upload_to='lgpd/documentos_assinados/', null=True, blank=True)

    class Meta:
        ordering = ['-data_solicitacao']

    def __str__(self):
        return f"{self.nome_completo} - {self.get_status_display()}"

class PastaVirtual(models.Model):
    TIPO_CHOICES = [
        ('raiz', 'Raiz do Sistema'),
        ('raiz_deptos', 'Raiz de Departamentos'),
        ('raiz_usuarios', 'Raiz de Usuários'),
        ('departamento', 'Pasta de Departamento'),
        ('usuario', 'Pasta Pessoal de Usuário'),
        ('compartilhados', 'Compartilhados Comigo'),
        ('normal', 'Pasta Normal')
    ]

    nome = models.CharField(max_length=100)
    tipo_pasta = models.CharField(max_length=30, choices=TIPO_CHOICES, default='normal')
    is_sistema = models.BooleanField(default=False, help_text="Se marcado, a pasta não pode ser excluída ou renomeada")

    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='pastas', null=True, blank=True)
    dono_membro = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='pastas_pessoais', null=True, blank=True)

    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subpastas')
    criado_por = models.ForeignKey(Membro, on_delete=models.SET_NULL, null=True, related_name='pastas_criadas')
    data_criacao = models.DateTimeField(auto_now_add=True)
    is_excluida = models.BooleanField(default=False)
    data_exclusao = models.DateTimeField(null=True, blank=True)

    # Integração Google Drive
    gdrive_folder_id = models.CharField(max_length=255, blank=True, null=True)
    gdrive_url = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        dono = self.departamento.nome if self.departamento else (self.dono_membro.get_full_name() if self.dono_membro else 'Sistema')
        if self.parent:
            return f"{self.parent.nome} / {self.nome} ({dono})"
        return f"{self.nome} ({dono})"

class PermissaoPVDrive(models.Model):
    NIVEL_CHOICES = [
        ('leitor', 'Pode Visualizar e Baixar'),
        ('editor', 'Pode Fazer Upload e Editar'),
        ('admin', 'Administrador (Pode Excluir)')
    ]

    pasta = models.ForeignKey(PastaVirtual, on_delete=models.CASCADE, related_name='permissoes', null=True, blank=True)
    arquivo = models.ForeignKey('ArquivoMidia', on_delete=models.CASCADE, related_name='permissoes', null=True, blank=True)

    alvo_departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, null=True, blank=True, related_name='permissoes_recebidas')
    alvo_membro = models.ForeignKey(Membro, on_delete=models.CASCADE, null=True, blank=True, related_name='permissoes_recebidas')

    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES, default='leitor')
    concedido_por = models.ForeignKey(Membro, on_delete=models.SET_NULL, null=True, related_name='permissoes_concedidas')
    data_concessao = models.DateTimeField(auto_now_add=True)
    validade = models.DateTimeField(null=True, blank=True, help_text="Se preenchido, o acesso expira nesta data.")

    # Recursos Avançados de Compartilhamento (Missão Impossível)
    senha_acesso = models.CharField(max_length=128, blank=True, null=True, help_text="Hash de senha para acesso seguro")
    is_autodestruir = models.BooleanField(default=False, help_text="Se marcado, o arquivo some do compartilhamento após o primeiro acesso")
    foi_acessado = models.BooleanField(default=False)

    is_ativo = models.BooleanField(default=True)

    def __str__(self):
        alvo = self.alvo_departamento.nome if self.alvo_departamento else self.alvo_membro.get_full_name()
        return f"{self.get_nivel_display()} para {alvo} na pasta {self.pasta.nome if self.pasta else 'Desconhecida'}"

class CompartilhamentoPasta(models.Model):
    # OBSOLETO: Mantido apenas por compatibilidade até migrar para PermissaoPVDrive
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
    arquivo = models.FileField(upload_to='arquivos/%Y/%m/', null=True, blank=True, help_text="Arquivo local (Legado ou Temporário)")
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='arquivos_midia', null=True, blank=True)
    dono_membro = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='arquivos_pessoais', null=True, blank=True)

    pasta = models.ForeignKey(PastaVirtual, on_delete=models.CASCADE, related_name='arquivos', null=True, blank=True)
    enviado_por = models.ForeignKey(Membro, on_delete=models.SET_NULL, null=True)
    data_envio = models.DateTimeField(auto_now_add=True)
    tamanho_bytes = models.BigIntegerField(default=0)
    extensao = models.CharField(max_length=20, blank=True)
    hash_sha256 = models.CharField(max_length=64, blank=True)
    is_publico_para_membros = models.BooleanField(default=False, help_text="Se marcado, voluntários comuns do setor poderão baixar o arquivo")
    is_excluido = models.BooleanField(default=False)
    data_exclusao = models.DateTimeField(null=True, blank=True)

    # Integração Google Drive
    gdrive_file_id = models.CharField(max_length=255, blank=True, null=True)
    gdrive_url = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.titulo
