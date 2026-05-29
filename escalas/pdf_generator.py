import os
from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from .models import CompetenciaEscala, Escala
from django.conf import settings

def gerar_pdf_competencia(competencia_id):
    competencia = CompetenciaEscala.objects.get(id=competencia_id)
    escalas = Escala.objects.filter(competencia=competencia).order_by('data_escala', 'horario_inicio')
    
    if not escalas.exists():
        return False

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    # Título Principal
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor("#1e3a8a"), # Azul escuro
        spaceAfter=5,
        alignment=1 # Center
    )
    
    sub_title_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        textColor=colors.HexColor("#4b5563"),
        spaceAfter=20,
        alignment=1
    )

    # Logo do Departamento
    if competencia.departamento.logo:
        try:
            img_path = competencia.departamento.logo.path
            img = Image(img_path)
            # Resize image maintaining aspect ratio
            img.drawWidth = 2 * inch
            img.drawHeight = (img.drawWidth / img.imageWidth) * img.imageHeight
            elements.append(img)
            elements.append(Spacer(1, 10))
        except Exception:
            pass # Ignora caso não consiga ler a logo
            
    elements.append(Paragraph(f"Escala Oficial - {competencia.departamento.nome}", title_style))
    elements.append(Paragraph(f"Competência: {competencia.mes_ano} | Gerado pelo Sistema PVE", sub_title_style))
    
    # Monta a tabela
    data = [['Data', 'Culto/Evento', 'Horário', 'Função', 'Voluntário']]
    
    for e in escalas:
        funcao_nome = e.funcao_alocada.nome if e.funcao_alocada else "-"
        voluntario_nome = e.membro_escalado.get_full_name()
        if e.status == 'falta_justificada':
            voluntario_nome += " (Falta Justificada)"
        elif e.status == 'substituido':
            voluntario_nome += " (Substituído)"
            
        data.append([
            e.data_escala.strftime('%d/%m/%Y'),
            e.get_tipo_evento_display(),
            f"{e.horario_inicio.strftime('%H:%M')} - {e.horario_fim.strftime('%H:%M')}",
            funcao_nome,
            voluntario_nome
        ])

    t = Table(data, repeatRows=1, colWidths=[65, 120, 80, 100, 150])
    
    # Estilização profissional e moderna
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2563eb")), # Cabeçalho azul vibrante
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]), # Zebra effect
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor("#1f2937")),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")), # Borda suave
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor("#1d4ed8")), # Linha forte abaixo do cabeçalho
    ]))
    
    elements.append(t)
    doc.build(elements)
    
    pdf_value = buffer.getvalue()
    buffer.close()
    
    # Salva no model
    nome_arquivo = f"escala_{competencia.departamento.id}_{competencia.mes_ano.replace('/','_')}.pdf"
    competencia.pdf_gerado.save(nome_arquivo, ContentFile(pdf_value), save=True)
    
    return True
