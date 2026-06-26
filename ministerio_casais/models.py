"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: ministerio_casais/models.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.conf import settings
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
    arquivado = models.BooleanField('Arquivado/Saiu', default=False)

    # Autenticação para o Portal do Aluno
    senha = models.CharField('Senha de Acesso', max_length=128, blank=True, null=True)
    precisa_trocar_senha = models.BooleanField('Trocar Senha no Próximo Login', default=True)

    foto_casal = models.ImageField('Foto do Casal', upload_to='casais/fotos/', blank=True, null=True)
    foto_conjuge_1 = models.ImageField('Foto Cônjuge 1', upload_to='casais/fotos/', blank=True, null=True)
    foto_conjuge_2 = models.ImageField('Foto Cônjuge 2', upload_to='casais/fotos/', blank=True, null=True)

    # Campo de Gamificação / Trilha de Noivos
    trilha_noivos_etapa = models.IntegerField('Etapa Trilha de Noivos', default=0, help_text="0: N/A, 1: Iniciado, 2: Curso Feito, 3: Aconselhamento, 4: Altar")

    # Acompanhamento Pastoral
    nivel_crise_atual = models.IntegerField('Nível de Crise Atual', default=1, help_text="1: Saudável, 2: Atritos Leves, 3: Conflitos Moderados, 4: Alerta Laranja, 5: Alerta Vermelho")

    def __str__(self):
        return f"{self.nome_conjuge_1} & {self.nome_conjuge_2}"

    @property
    def nomes_juntos(self):
        return f"{self.nome_conjuge_1} e {self.nome_conjuge_2}"

    @property
    def primeiro_nome_1(self):
        return self.nome_conjuge_1.split()[0] if self.nome_conjuge_1 else ""

    @property
    def primeiro_nome_2(self):
        return self.nome_conjuge_2.split()[0] if self.nome_conjuge_2 else ""

class HistoricoAconselhamentoCasal(models.Model):
    casal = models.ForeignKey(Casal, on_delete=models.CASCADE, related_name='historicos_aconselhamento')
    data_sessao = models.DateTimeField(default=timezone.now)

    ATENDIMENTO_CHOICES = (
        ('Casal', 'Casal'),
        ('Apenas Cônjuge 1', 'Apenas Cônjuge 1'),
        ('Apenas Cônjuge 2', 'Apenas Cônjuge 2'),
    )
    atendimento_para = models.CharField('Atendimento para', max_length=50, choices=ATENDIMENTO_CHOICES, default='Casal')

    pastor_conselheiro = models.CharField('Pastor / Conselheiro', max_length=100)
    observacoes = models.TextField('Observações da Sessão')
    nivel_crise = models.IntegerField('Nível de Crise (1 a 5)', default=1, help_text="1: Saudável, 5: Alerta Vermelho / Separação")

    def __str__(self):
        return f"Aconselhamento {self.casal.nomes_juntos} em {self.data_sessao.strftime('%d/%m/%Y')}"

class CursoCasal(models.Model):
    nome = models.CharField('Nome do Curso', max_length=150)
    descricao = models.TextField('Descrição')

    def __str__(self):
        return self.nome

class TurmaCurso(models.Model):
    STATUS_TURMA = (
        ('Aberta', 'Aberta (Matrículas Abertas)'),
        ('Em Andamento', 'Em Andamento'),
        ('Concluída', 'Concluída'),
    )
    curso = models.ForeignKey(CursoCasal, on_delete=models.CASCADE, related_name='turmas')
    nome_turma = models.CharField('Nome/Número da Turma', max_length=100)
    data_inicio = models.DateField('Data de Início', blank=True, null=True)
    status = models.CharField('Status da Turma', max_length=50, choices=STATUS_TURMA, default='Aberta')

    # Configurações Movidas do Curso
    valor_curso = models.DecimalField('Valor do Material/Inscrição', max_digits=10, decimal_places=2, default=0.00)
    carga_horaria = models.IntegerField('Carga Horária Total (Horas)', default=10)
    dias_semana = models.CharField('Dias da Semana', max_length=150, blank=True, null=True, help_text="Ex: Segunda, Quarta")
    emite_certificado = models.BooleanField('Emite Certificado?', default=False)
    compra_camiseta = models.BooleanField('Requer Camiseta?', default=False)
    duracao_aula_horas = models.IntegerField('Duração por Aula (Horas)', default=2)

    # Regras de Aprovação
    limite_faltas = models.IntegerField('Limite Máximo de Faltas', default=3, help_text="Quantidade de faltas permitidas antes da reprovação")
    percentual_presenca_minimo = models.IntegerField('Percentual de Presença Mínimo (%)', default=75, help_text="Se atingir as duas regras (A e B), o aluno reprova por falta")

    def __str__(self):
        return f"{self.curso.nome} - {self.nome_turma}"


class ProfessorTurma(models.Model):
    turma = models.ForeignKey(TurmaCurso, on_delete=models.CASCADE, related_name='professores')
    professor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='turmas_lecionadas')

    def __str__(self):
        return f"{self.professor.get_full_name() or self.professor.username} - {self.turma}"

class AulaTurma(models.Model):
    turma = models.ForeignKey(TurmaCurso, on_delete=models.CASCADE, related_name='aulas')
    titulo = models.CharField('Título/Tema da Aula', max_length=150)
    data_aula = models.DateField('Data da Aula')
    realizada = models.BooleanField('Aula Realizada / Chamada Feita', default=False)

    def __str__(self):
        return f"{self.titulo} - {self.turma.nome_turma}"

class MatriculaCursoCasal(models.Model):
    STATUS_PAGAMENTO = (
        ('Pendente', 'Pendente'),
        ('Pago', 'Pago'),
        ('Bolsa Parcial', 'Bolsa Parcial'),
        ('Bolsa Integral', 'Bolsa Integral'),
    )

    STATUS_MATRICULA = (
        ('Ativa', 'Ativa'),
        ('Aprovado', 'Aprovado'),
        ('Reprovado por Falta', 'Reprovado por Falta'),
        ('Desistente', 'Desistente'),
    )

    turma = models.ForeignKey(TurmaCurso, on_delete=models.CASCADE, related_name='matriculas', null=True, blank=True)
    casal = models.ForeignKey(Casal, on_delete=models.CASCADE, related_name='matriculas_cursos')
    data_matricula = models.DateTimeField(auto_now_add=True)
    status_matricula = models.CharField('Status da Matrícula', max_length=50, choices=STATUS_MATRICULA, default='Ativa')

    status_pagamento = models.CharField('Status Financeiro', max_length=50, choices=STATUS_PAGAMENTO, default='Pendente')
    valor_pago = models.DecimalField('Valor Pago', max_digits=10, decimal_places=2, default=0.00)

    percentual_conclusao = models.IntegerField('Progresso (%)', default=0)
    aprovado = models.BooleanField('Aprovado / Certificado', default=False)
    certificado_arquivo = models.FileField('Arquivo do Certificado', upload_to='casais/certificados/', blank=True, null=True)

    # Autenticação Option B (Link Mágico)
    token_acesso = models.CharField('Token Mágico de Acesso', max_length=100, blank=True, null=True, unique=True)

    def __str__(self):
        return f"{self.casal.nomes_juntos} - {self.turma.curso.nome} ({self.turma.nome_turma})"

class PresencaAula(models.Model):
    aula = models.ForeignKey(AulaTurma, on_delete=models.CASCADE, related_name='presencas')
    matricula = models.ForeignKey(MatriculaCursoCasal, on_delete=models.CASCADE, related_name='historico_presenca')
    presente = models.BooleanField('Presente?', default=True)
    justificada = models.BooleanField('Falta Justificada/Abonada?', default=False)
    observacao = models.CharField('Observação', max_length=200, blank=True, null=True)

    def __str__(self):
        status = "Presente" if self.presente else ("Falta Justificada" if self.justificada else "Falta")
        return f"{self.matricula.casal.nomes_juntos} - {self.aula.titulo} - {status}"

class PostagemCurso(models.Model):
    TIPO_CHOICES = (
        ('Aviso', 'Aviso'),
        ('Material', 'Material de Estudo (Download)'),
        ('Tarefa', 'Tarefa / Atividade (Requer Envio)'),
    )
    turma = models.ForeignKey(TurmaCurso, on_delete=models.CASCADE, related_name='postagens')
    titulo = models.CharField('Título da Postagem', max_length=200)
    descricao = models.TextField('Descrição / Conteúdo', blank=True, null=True)
    tipo = models.CharField('Tipo', max_length=50, choices=TIPO_CHOICES, default='Aviso')
    alunos_especificos = models.ManyToManyField('MatriculaCursoCasal', blank=True, related_name='postagens_diretas', help_text="Se vazio, vai para todos da turma.")
    arquivo = models.FileField('Arquivo Anexo', upload_to='casais/cursos/materiais/', blank=True, null=True)
    data_postagem = models.DateTimeField(auto_now_add=True)
    data_limite = models.DateTimeField('Data Limite de Entrega (Para Tarefas)', blank=True, null=True)

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.titulo} - {self.turma.nome_turma}"

class EntregaAtividadeAluno(models.Model):
    postagem = models.ForeignKey(PostagemCurso, on_delete=models.CASCADE, related_name='entregas')
    matricula = models.ForeignKey(MatriculaCursoCasal, on_delete=models.CASCADE, related_name='entregas_tarefas')
    arquivo_enviado = models.FileField('Arquivo Enviado', upload_to='casais/cursos/entregas/')
    comentario_aluno = models.TextField('Comentário do Aluno', blank=True, null=True)
    data_entrega = models.DateTimeField(auto_now_add=True)
    nota = models.DecimalField('Nota (Opcional)', max_digits=5, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"Entrega de {self.matricula.casal.nomes_juntos} - {self.postagem.titulo}"

class PagamentoCursoCasal(models.Model):
    FORMAS_PAGAMENTO = (
        ('Dinheiro', 'Dinheiro'),
        ('PIX', 'PIX'),
        ('Cartão de Crédito', 'Cartão de Crédito'),
        ('Cartão de Débito', 'Cartão de Débito'),
        ('Transferência', 'Transferência'),
    )
    matricula = models.ForeignKey(MatriculaCursoCasal, on_delete=models.CASCADE, related_name='historico_pagamentos')
    valor_pago = models.DecimalField('Valor do Pagamento', max_digits=10, decimal_places=2)
    forma_pagamento = models.CharField('Forma de Pagamento', max_length=50, choices=FORMAS_PAGAMENTO)
    data_pagamento = models.DateTimeField('Data do Pagamento', auto_now_add=True)
    observacoes = models.TextField('Observações', blank=True, null=True)

    def __str__(self):
        return f"Pagamento de R$ {self.valor_pago} - {self.matricula.casal.nomes_juntos}"

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
