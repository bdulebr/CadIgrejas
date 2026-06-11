from django.db import models
from django.utils import timezone

class Casal(models.Model):
    STATUS_CHOICES = (
        ('Namorados', 'Namorados'),
        ('Noivos', 'Noivos'),
        ('Casados', 'Casados'),
        ('Em Crise', 'Em Crise'),
        ('Separados', 'Separados'),
    )

    nome_conjuge_1 = models.CharField('Nome Cônjuge 1', max_length=150)
    nome_conjuge_2 = models.CharField('Nome Cônjuge 2', max_length=150)

    email_1 = models.EmailField('E-mail Cônjuge 1', blank=True, null=True)
    email_2 = models.EmailField('E-mail Cônjuge 2', blank=True, null=True)

    telefone_1 = models.CharField('Telefone Cônjuge 1', max_length=20, blank=True, null=True)
    telefone_2 = models.CharField('Telefone Cônjuge 2', max_length=20, blank=True, null=True)

    status_relacionamento = models.CharField('Status do Relacionamento', max_length=50, choices=STATUS_CHOICES, default='Casados')
    data_aniversario_casamento = models.DateField('Data do Casamento (Bodas)', blank=True, null=True)

    endereco = models.TextField('Endereço', blank=True, null=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    # Campo de Gamificação / Trilha de Noivos
    trilha_noivos_etapa = models.IntegerField('Etapa Trilha de Noivos', default=0, help_text="0: N/A, 1: Iniciado, 2: Curso Feito, 3: Aconselhamento, 4: Altar")

    def __str__(self):
        return f"{self.nome_conjuge_1} & {self.nome_conjuge_2}"

    @property
    def nomes_juntos(self):
        return f"{self.nome_conjuge_1} e {self.nome_conjuge_2}"

class HistoricoAconselhamentoCasal(models.Model):
    casal = models.ForeignKey(Casal, on_delete=models.CASCADE, related_name='historicos_aconselhamento')
    data_sessao = models.DateTimeField(default=timezone.now)
    pastor_conselheiro = models.CharField('Pastor / Conselheiro', max_length=100)
    observacoes = models.TextField('Observações da Sessão')
    nivel_crise = models.IntegerField('Nível de Crise (1 a 5)', default=1, help_text="1: Saudável, 5: Alerta Vermelho / Separação")

    def __str__(self):
        return f"Aconselhamento {self.casal.nomes_juntos} em {self.data_sessao.strftime('%d/%m/%Y')}"

class CursoCasal(models.Model):
    nome = models.CharField('Nome do Curso', max_length=150)
    descricao = models.TextField('Descrição')
    valor_curso = models.DecimalField('Valor do Curso', max_digits=10, decimal_places=2, default=0.00)
    carga_horaria = models.IntegerField('Carga Horária (Horas)', default=10)
    data_inicio = models.DateField('Data de Início', blank=True, null=True)
    data_fim = models.DateField('Data de Término', blank=True, null=True)

    def __str__(self):
        return self.nome

class MatriculaCursoCasal(models.Model):
    STATUS_PAGAMENTO = (
        ('Pendente', 'Pendente'),
        ('Pago', 'Pago'),
        ('Bolsa Parcial', 'Bolsa Parcial'),
        ('Bolsa Integral', 'Bolsa Integral'),
    )

    curso = models.ForeignKey(CursoCasal, on_delete=models.CASCADE, related_name='matriculas')
    casal = models.ForeignKey(Casal, on_delete=models.CASCADE, related_name='matriculas_cursos')
    data_matricula = models.DateTimeField(auto_now_add=True)

    status_pagamento = models.CharField('Status Financeiro', max_length=50, choices=STATUS_PAGAMENTO, default='Pendente')
    valor_pago = models.DecimalField('Valor Pago', max_digits=10, decimal_places=2, default=0.00)

    percentual_conclusao = models.IntegerField('Progresso (%)', default=0)
    aprovado = models.BooleanField('Aprovado / Certificado', default=False)

    def __str__(self):
        return f"{self.casal.nomes_juntos} - {self.curso.nome}"

class EventoCasal(models.Model):
    titulo = models.CharField('Título do Evento', max_length=150)
    data_evento = models.DateTimeField('Data e Hora')
    local = models.CharField('Local', max_length=200)
    descricao = models.TextField('Descrição', blank=True, null=True)

    def __str__(self):
        return f"{self.titulo} - {self.data_evento.strftime('%d/%m/%Y')}"

class PresencaEventoCasal(models.Model):
    evento = models.ForeignKey(EventoCasal, on_delete=models.CASCADE, related_name='presencas')
    casal = models.ForeignKey(Casal, on_delete=models.CASCADE, related_name='eventos_presentes')
    confirmou_presenca = models.BooleanField('Confirmou Presença?', default=False)
    compareceu = models.BooleanField('Compareceu?', default=False)

    def __str__(self):
        return f"Presença {self.casal.nomes_juntos} - {self.evento.titulo}"
