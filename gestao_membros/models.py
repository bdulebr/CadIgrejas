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
    logo = models.ImageField(upload_to='departamentos/logos/', null=True, blank=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'svg', 'webp'])])
    
    lideres = models.ManyToManyField(Membro, related_name='departamentos_liderados', blank=True)
    sub_lideres = models.ManyToManyField(Membro, related_name='departamentos_subliderados', blank=True)
    membros_ativos = models.ManyToManyField(Membro, related_name='departamentos_ativos', blank=True)
    
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
    TIPO_EVENTO_CHOICES = [
        ('segunda_oracao', 'Segunda: Culto de Oração (20:00 - 21:00)'),
        ('quarta_profetica', 'Quarta: Quarta Profética (20:00 - 22:00)'),
        ('quinta_saber', 'Quinta: Quinta do Saber (19:30 - 20:30)'),
        ('domingo_manha', 'Domingo da Família: Manhã (09:30 - 11:30)'),
        ('domingo_noite', 'Domingo da Família: Noite (19:30 - 21:30)'),
        ('eventos', 'Eventos Extraordinários'),
    ]
    
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='configuracao_slots')
    tipo_evento = models.CharField(max_length=50, choices=TIPO_EVENTO_CHOICES)
    funcao = models.ForeignKey('Funcao', on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)
    
    class Meta:
        unique_together = ('departamento', 'tipo_evento', 'funcao')

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
