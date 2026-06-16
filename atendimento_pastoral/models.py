from django.db import models
from django.conf import settings
from django.utils import timezone

class PessoaAtendimento(models.Model):
    ESTADO_CIVIL_CHOICES = (
        ('Solteiro(a)', 'Solteiro(a)'),
        ('Casado(a)', 'Casado(a)'),
        ('Divorciado(a)', 'Divorciado(a)'),
        ('Viúvo(a)', 'Viúvo(a)'),
        ('Outro', 'Outro'),
    )

    nome_completo = models.CharField('Nome Completo', max_length=150)
    telefone = models.CharField('Telefone / WhatsApp', max_length=20)
    email = models.EmailField('E-mail', blank=True, null=True)
    endereco = models.CharField('Endereço Completo', max_length=255, blank=True, null=True)
    estado_civil = models.CharField('Estado Civil', max_length=50, choices=ESTADO_CIVIL_CHOICES, default='Solteiro(a)')
    data_nascimento = models.DateField('Data de Nascimento', blank=True, null=True)

    anotacoes_gerais = models.TextField('Anotações Gerais', blank=True, null=True, help_text='Informações gerais, não usar para histórico pastoral.')

    nivel_crise = models.IntegerField('Nível de Crise', default=1, help_text="1: Saudável, 5: Alerta Máximo")

    # Marcadores de risco rápido (JSON)
    tags_risco = models.JSONField('Tags de Risco', default=list, blank=True, help_text='Ex: ["Risco de Suicídio", "Divórcio", "Violência"]')

    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pessoa (Atendimento)'
        verbose_name_plural = 'Pessoas (Atendimento)'

    def __str__(self):
        return self.nome_completo

class AgendamentoPastoral(models.Model):
    LOCAL_CHOICES = (
        ('Gabinete Igreja', 'Gabinete Igreja'),
        ('Casa da Pessoa', 'Casa da Pessoa'),
        ('Online (Meet/Zoom)', 'Online (Meet/Zoom)'),
        ('Outro', 'Outro'),
    )

    STATUS_CHOICES = (
        ('Agendado', 'Agendado'),
        ('Realizado', 'Realizado'),
        ('Cancelado', 'Cancelado'),
        ('Faltou', 'Faltou'),
    )

    pessoa = models.ForeignKey(PessoaAtendimento, on_delete=models.CASCADE, related_name='agendamentos')
    pastor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='agendamentos_pastorais')

    data_agendamento = models.DateField('Data do Atendimento')
    hora_inicio = models.TimeField('Hora de Início')
    hora_fim = models.TimeField('Hora de Fim')

    local = models.CharField('Local', max_length=50, choices=LOCAL_CHOICES, default='Gabinete Igreja')
    status = models.CharField('Status', max_length=30, choices=STATUS_CHOICES, default='Agendado')

    notificacao_enviada = models.BooleanField('Notificação Enviada?', default=False)

    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Agendamento Pastoral'
        verbose_name_plural = 'Agendamentos Pastorais'
        ordering = ['data_agendamento', 'hora_inicio']

    def __str__(self):
        return f"{self.pessoa.nome_completo} com {self.pastor.get_full_name()} em {self.data_agendamento.strftime('%d/%m/%Y')} {self.hora_inicio.strftime('%H:%M')}"

class SessaoAtendimento(models.Model):
    agendamento = models.OneToOneField(AgendamentoPastoral, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessao_realizada', help_text="Opcional. Permite registrar atendimento surpresa/sem agenda.")
    pessoa = models.ForeignKey(PessoaAtendimento, on_delete=models.CASCADE, related_name='historico_sessoes')
    pastor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sessoes_ministradas')

    data_sessao = models.DateTimeField('Data e Hora da Sessão', default=timezone.now)
    resumo_sessao = models.TextField('Resumo / Prontuário')

    nivel_crise = models.IntegerField('Nível de Crise', default=1, help_text="1: Saudável, 5: Alerta Máximo")
    exige_retorno_em_dias = models.IntegerField('Sugerir Retorno em (Dias)', blank=True, null=True, help_text="Ex: 15. Deixe em branco se não precisar.")

    analise_comportamental = models.TextField('Análise Comportamental Inteligente (ACI)', blank=True, null=True, help_text='Gerada automaticamente pela IA (Gemini) atuando como Psicólogo Sênior.')

    # Campo de controle de RLS rigoroso
    is_restrito = models.BooleanField('Acesso Estrito ao Pastor', default=True, help_text="Se marcado, nem o super admin deve ver o conteúdo (se a regra exigir).")

    class Meta:
        verbose_name = 'Sessão de Atendimento'
        verbose_name_plural = 'Sessões de Atendimento'
        ordering = ['-data_sessao']

    def __str__(self):
        return f"Sessão {self.pessoa.nome_completo} em {self.data_sessao.strftime('%d/%m/%Y')} por {self.pastor.first_name}"
