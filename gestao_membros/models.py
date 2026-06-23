"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: gestao_membros/models.py
* DESCRIÇÃO: Modelos relacionados aos Departamentos, Ministérios e Setores.
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 25/05/2026 13:42
* LOG DE ALTERAÇÕES:
* - 25/05/2026 13:42: Criação inicial
"""

from django.db import models
from core.models import Membro

class Habilidade(models.Model):
    departamento = models.ForeignKey('Departamento', on_delete=models.CASCADE, related_name='habilidades', null=True)
    nome = models.CharField(max_length=100) # Removido unique=True, pois cada dep pode ter "Músico"
    descricao = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.nome


from django.core.validators import FileExtensionValidator

class Departamento(models.Model):
    CATEGORIA_CHOICES = (
        ('grupo', 'Grupo'),
        ('setor', 'Setor'),
        ('ministerio', 'Ministério'),
        ('departamento', 'Departamento'),
    )

    id_unico_fixo = models.CharField(max_length=20, unique=True, blank=True)
    nome = models.CharField(max_length=100)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    is_system = models.BooleanField(default=False, help_text="Departamentos do sistema não podem ser excluídos e garantem o funcionamento de módulos cruciais.")
    logo = models.ImageField(upload_to='departamentos/logos/', null=True, blank=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'svg', 'webp'])])

    instrucoes_padrao_escala = models.TextField(blank=True, help_text="Instruções padrão que aparecerão no rodapé do PDF das escalas.")

    lideres = models.ManyToManyField(Membro, related_name='departamentos_liderados', blank=True)
    sub_lideres = models.ManyToManyField(Membro, related_name='departamentos_subliderados', blank=True)
    membros_ativos = models.ManyToManyField(Membro, related_name='departamentos_ativos', blank=True)

    def __str__(self):
        return f"{self.nome} ({self.id_unico_fixo})"

    def save(self, *args, **kwargs):
        import random
        if not self.id_unico_fixo:
            # Generate 6 digit code
            while True:
                code = str(random.randint(100000, 999999))
                if not Departamento.objects.filter(id_unico_fixo=code).exists():
                    self.id_unico_fixo = code
                    break
        super().save(*args, **kwargs)

class ConfiguracaoSlotEscala(models.Model):
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='configuracao_slots')
    tipo_evento = models.CharField(max_length=50)
    funcao = models.ForeignKey('Funcao', on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('departamento', 'tipo_evento', 'funcao')

    def get_tipo_evento_display(self):
        from escalas.models import CultoEvento
        if not self.tipo_evento:
            return "Sem Evento"
        if self.tipo_evento.isdigit():
            evento = CultoEvento.objects.filter(id=int(self.tipo_evento)).first()
        else:
            evento = CultoEvento.objects.filter(chave_slug=self.tipo_evento).first()
        return evento.nome if evento else f"Culto Removido (ID: {self.tipo_evento})"

    def __str__(self):
        return f"{self.quantidade}x {self.funcao.nome} em {self.get_tipo_evento_display()}"

class Funcao(models.Model):
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='funcoes')
    nome = models.CharField(max_length=100)
    descricao = models.CharField(max_length=200, blank=True)
    requisitos = models.ManyToManyField(Habilidade, blank=True)

    def __str__(self):
        return f"{self.nome} - {self.departamento.nome}"


class Indisponibilidade(models.Model):
    membro = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='indisponibilidades')
    data_inicio = models.DateField()
    data_fim = models.DateField()
    motivo = models.CharField(max_length=200, help_text="Ex: Viagem, Doença, Trabalho")

    def __str__(self):
        return f"{self.membro.first_name} ausente de {self.data_inicio} até {self.data_fim}"

class AvisoMural(models.Model):
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='avisos')
    autor = models.ForeignKey(Membro, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    mensagem = models.TextField()
    data_postagem = models.DateTimeField(auto_now_add=True)
    fixado = models.BooleanField(default=False)
    data_expiracao = models.DateTimeField(null=True, blank=True)
    link_externo = models.URLField(max_length=500, blank=True, null=True)
    @property
    def status(self):
        if not self.data_expiracao:
            return 'ativo'
        from django.utils import timezone
        if timezone.now() > self.data_expiracao:
            return 'expirado'
        return 'ativo'

    def __str__(self):
        return f"Aviso: {self.titulo} - {self.departamento.nome}"

class AvisoAnexo(models.Model):
    aviso = models.ForeignKey(AvisoMural, on_delete=models.CASCADE, related_name='anexos')
    arquivo = models.FileField(upload_to='avisos_anexos/')
    nome_original = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        if self.arquivo and not self.nome_original:
            self.nome_original = self.arquivo.name.split('/')[-1]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Anexo de: {self.aviso.titulo}"

class AvaliacaoMembro(models.Model):
    membro = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='avaliacoes_recebidas')
    avaliador = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='avaliacoes_feitas')
    nota = models.IntegerField(choices=[(1,'1'), (2,'2'), (3,'3'), (4,'4'), (5,'5')])
    comentarios = models.TextField()
    data = models.DateTimeField(auto_now_add=True)
    enviado_ao_membro = models.BooleanField(default=False)

    def __str__(self):
        return f"Avaliação de {self.membro.first_name} por {self.avaliador.first_name}"

class Ocorrencia(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    data_ocorrencia = models.DateField()
    data_registro = models.DateTimeField(auto_now_add=True)
    autor = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='ocorrencias_registradas')
    envolvidos = models.ManyToManyField(Membro, related_name='ocorrencias_envolvido')
    anexo = models.FileField(upload_to='ocorrencias/', null=True, blank=True, validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])])

    def __str__(self):
        return f"Ocorrência: {self.titulo} - {self.data_ocorrencia}"

class AcaoDisciplinar(models.Model):
    TIPO_CHOICES = (
        ('advertencia', 'Advertência Formal'),
        ('suspensao', 'Suspensão'),
        ('expulsao', 'Desligamento / Expulsão'),
    )
    membro = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='acoes_disciplinares')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    motivo = models.TextField()
    data_aplicacao = models.DateTimeField(auto_now_add=True)
    data_fim_suspensao = models.DateField(null=True, blank=True)
    autor = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='acoes_disciplinares_aplicadas')
    enviado_email = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.membro.first_name}"


# --- NOVAS FUNCIONALIDADES: RECRUTAMENTO E AGENDA ---

class VagaSetor(models.Model):
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='vagas_abertas')
    titulo = models.CharField(max_length=100)
    descricao = models.TextField(help_text="Explique o que o voluntário vai fazer e os requisitos")
    quantidade = models.PositiveIntegerField(default=1)
    ativa = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Vaga: {self.titulo} - {self.departamento.nome}"

class CandidaturaVaga(models.Model):
    STATUS_CHOICES = (
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
    )
    vaga = models.ForeignKey(VagaSetor, on_delete=models.CASCADE, related_name='candidaturas')
    membro = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='minhas_candidaturas')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    mensagem = models.TextField(blank=True, help_text="Por que você quer participar deste ministério?")
    data_candidatura = models.DateTimeField(auto_now_add=True)
    data_resposta = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Candidatura de {self.membro.first_name} para {self.vaga.titulo}"

class EventoInternoSetor(models.Model):
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='eventos_internos')
    titulo = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    local = models.CharField(max_length=150, blank=True)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} - {self.departamento.nome}"

class AnotacaoRH(models.Model):
    membro = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='anotacoes_rh')
    autor = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='anotacoes_rh_criadas')
    anotacao = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_criacao']

    def __str__(self):
        return f"Anotação sobre {self.membro.first_name} por {self.autor.first_name}"
