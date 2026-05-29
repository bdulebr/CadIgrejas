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
    TIPO_EVENTO_CHOICES = (
        ('segunda_oracao', 'Segunda: Culto de Oração (20:00 - 21:00)'),
        ('quarta_profetica', 'Quarta: Quarta Profética (20:00 - 22:00)'),
        ('quinta_saber', 'Quinta: Quinta do Saber (19:30 - 20:30)'),
        ('domingo_manha', 'Domingo da Família: Manhã (09:30 - 11:30)'),
        ('domingo_noite', 'Domingo da Família: Noite (19:30 - 21:30)'),
        ('eventos', 'Eventos Extraordinários'),
    )

    STATUS_CHOICES = (
        ('confirmado', 'Confirmado'),
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
    
    tipo_evento = models.CharField(max_length=20, choices=TIPO_EVENTO_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmado')
    
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

    def __str__(self):
        return f"{self.membro_escalado.get_full_name()} em {self.data_escala.strftime('%d/%m/%Y')}"
