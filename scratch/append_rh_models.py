import os

models_code = """
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
"""

with open(r'c:\Users\MarcosLira\Desktop\Marcos\Projeto\gestao_membros\models.py', 'a', encoding='utf-8') as f:
    f.write(models_code)
