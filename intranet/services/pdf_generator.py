from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.core.files.base import ContentFile
import io
import re

def gerar_pdf_contrato(documento_gerado):
    """
    Pega um DocumentoGerado, substitui as variáveis (ex: {{NOME}})
    pelos dados_preenchidos, e salva no arquivo_pdf_final.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=colors.HexColor("#111827"),
        spaceAfter=20,
        alignment=1 # Center
    )
    
    text_style = ParagraphStyle(
        'TextStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        textColor=colors.HexColor("#374151"),
        leading=16,
        spaceAfter=12,
        alignment=4 # Justify
    )

    elements.append(Paragraph(documento_gerado.template.titulo, title_style))
    elements.append(Spacer(1, 10))

    # Processar o conteudo base
    conteudo = documento_gerado.template.conteudo_base
    dados = documento_gerado.dados_preenchidos or {}
    
    # Substituir variáveis como {{NOME}}
    for match in re.finditer(r'\{\{(.*?)\}\}', conteudo):
        campo = match.group(1).strip()
        valor = dados.get(campo, f"[{campo} não preenchido]")
        conteudo = conteudo.replace(match.group(0), str(valor))
        
    # Quebras de linha para Paragrafos
    paragrafos = conteudo.split('\n')
    for p in paragrafos:
        if p.strip():
            elements.append(Paragraph(p.strip(), text_style))
            
    elements.append(Spacer(1, 30))
    
    # Assinatura Block
    assinatura_style = ParagraphStyle('Assinatura', parent=styles['Normal'], alignment=1, fontSize=10)
    elements.append(Paragraph("___________________________________________________", assinatura_style))
    
    nome_assinante = documento_gerado.nome_destino or documento_gerado.email_destino
    elements.append(Paragraph(f"Assinado Eletronicamente por: {nome_assinante}", assinatura_style))
    elements.append(Paragraph(f"E-mail: {documento_gerado.email_destino}", assinatura_style))
    if documento_gerado.data_assinatura:
        elements.append(Paragraph(f"Data/Hora: {documento_gerado.data_assinatura.strftime('%d/%m/%Y %H:%M:%S')}", assinatura_style))
    if documento_gerado.ip_assinatura:
        elements.append(Paragraph(f"IP Registrado: {documento_gerado.ip_assinatura}", assinatura_style))
    elements.append(Paragraph(f"Autenticidade (Hash Único): {documento_gerado.token_acesso}", assinatura_style))

    doc.build(elements)
    
    pdf_content = buffer.getvalue()
    buffer.close()
    
    filename = f"{documento_gerado.template.titulo[:30]}_{documento_gerado.token_acesso.hex[:8]}.pdf".replace(' ', '_')
    documento_gerado.arquivo_pdf_final.save(filename, ContentFile(pdf_content), save=True)
    return True
