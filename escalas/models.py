"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: escalas/models.py
* DESCRIÇÃO: Modelos base para o sistema de escalas e Motor de Conflitos Zero-Trust.
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 25/05/2026 14:00
* LOG DE ALTERAÇÕES:
* - 25/05/2026 14:00: Criação inicial e Constraint
"""

from django.db import models
from core.models import Membro
from gestao_membros.models import Departamento, Funcao

class CultoEvento(models.Model):
    TIPO_CHOICES = (
        ('padrao', 'Padrão (Recorrente)'),
        ('extra', 'Extraordinário (Único / Data Específica)'),
    )

    nome = models.CharField(max_length=150, help_text="Ex: Culto de Oração, Santa Ceia, Atendimento Pastoral")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='padrao')

    # Para recorrentes: em qual dia da semana acontece?
    # 0=Segunda, 1=Terça, 2=Quarta, 3=Quinta, 4=Sexta, 5=Sábado, 6=Domingo
    dia_semana = models.IntegerField(null=True, blank=True, help_text="0=Seg, 1=Ter, 2=Qua, 3=Qui, 4=Sex, 5=Sáb, 6=Dom")

    # Para extraordinários: data específica
    data_evento = models.DateField(null=True, blank=True)

    # Horário padrão
    horario_inicio = models.TimeField(default="19:30")
    horario_fim = models.TimeField(default="21:30")

    # Chave de slug para mapeamento de registros existentes/estáticos
    chave_slug = models.CharField(max_length=50, unique=True, null=True, blank=True)

    class Meta:
        verbose_name = 'Tipo de Culto / Evento'
        verbose_name_plural = 'Tipos de Cultos e Eventos'

    def save(self, *args, **kwargs):
        if self.chave_slug == '':
            self.chave_slug = None
        super().save(*args, **kwargs)

    def get_dia_semana_str(self):
        dias = {0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira', 3: 'Quinta-feira', 4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo'}
        return dias.get(self.dia_semana, 'N/A')

    def __str__(self):
        if self.tipo == 'extra':
            return f"{self.nome} ({self.data_evento.strftime('%d/%m/%Y')} {self.horario_inicio.strftime('%H:%M')})"
        return f"{self.nome} - {self.get_dia_semana_str()} ({self.horario_inicio.strftime('%H:%M')})"

class CompetenciaEscala(models.Model):
    STATUS_CHOICES = (
        ('rascunho', 'Rascunho (Não visível)'),
        ('publicada', 'Publicada'),
    )

    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='competencias_escala')
    mes_ano = models.CharField(max_length=7, help_text="Ex: 05/2026")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho')
    pdf_gerado = models.FileField(upload_to='escalas/pdfs/', null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Competência de Escala'
        verbose_name_plural = 'Competências de Escalas'
        unique_together = ('departamento', 'mes_ano')

    def __str__(self):
        return f"{self.departamento.nome} - {self.mes_ano}"

class Escala(models.Model):
    STATUS_CHOICES = (
        ('confirmado', 'Confirmado'),
        ('presente', 'Presente (Check-in Realizado)'),
        ('substituido', 'Substituído'),
        ('falta_justificada', 'Falta Justificada'),
    )

    competencia = models.ForeignKey(CompetenciaEscala, on_delete=models.CASCADE, related_name='escalas', null=True)
    membro_escalado = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='escalas_individuais')
    departamento_alocado = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='escalas_individuais')
    funcao_alocada = models.ForeignKey(Funcao, on_delete=models.SET_NULL, null=True, blank=True, related_name='escalas_individuais')

    data_escala = models.DateField()
    horario_inicio = models.TimeField()
    horario_fim = models.TimeField()

    tipo_evento = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmado')

    checkin_realizado = models.BooleanField(default=False)
    data_hora_checkin = models.DateTimeField(null=True, blank=True)

    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Escala'
        verbose_name_plural = 'Escalas'
        # MOTOR ANTI-CONFLITO DIRETO NO BANCO:
        # A mesma pessoa NÃO PODE ser inserida no mesmo dia e no mesmo horário de início,
        # independentemente do departamento que ela for alocada.
        constraints = [
            models.UniqueConstraint(
                fields=['membro_escalado', 'data_escala', 'horario_inicio'],
                name='unique_membro_escala_horario_zerotrust'
            )
        ]

    def get_tipo_evento_display(self):
        if not self.tipo_evento:
            return ""
        if self.tipo_evento.isdigit():
            evento = CultoEvento.objects.filter(id=int(self.tipo_evento)).first()
        else:
            evento = CultoEvento.objects.filter(chave_slug=self.tipo_evento).first()
        return evento.nome if evento else self.tipo_evento

    def __str__(self):
        return f"{self.membro_escalado.get_full_name()} em {self.data_escala.strftime('%d/%m/%Y')}"
