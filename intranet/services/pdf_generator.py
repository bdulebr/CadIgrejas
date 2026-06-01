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
    Suporta HTML complexo via xhtml2pdf.
    """
    import io
    import re
    from django.core.files.base import ContentFile
    
    html = documento_gerado.template.html_canva
    css = documento_gerado.template.css_canva
    conteudo = documento_gerado.template.conteudo_base
    dados = documento_gerado.dados_preenchidos or {}
    
    if html:
        # Modo Avançado (Canva / GrapesJS)
        from xhtml2pdf import pisa
        
        # Substituir variáveis no HTML
        for match in re.finditer(r'\{\{(.*?)\}\}', html):
            campo = match.group(1).strip()
            valor = dados.get(campo, f"[{campo} não preenchido]")
            html = html.replace(match.group(0), str(valor))
            
        assinatura_base64 = dados.get('assinatura_base64', '')
        assinatura_img_html = f'<img src="{assinatura_base64}" style="max-height: 100px; display: block; margin: 0 auto; margin-bottom: 10px;">' if assinatura_base64 else '<p>___________________________________________________</p>'
        
        assinatura_block = f'''
        <div style="margin-top: 50px; text-align: center;">
            {assinatura_img_html}
            <p><strong>Assinado Eletronicamente por:</strong> {documento_gerado.nome_destino or documento_gerado.email_destino}</p>
            <p><strong>E-mail:</strong> {documento_gerado.email_destino}</p>
            <p><strong>Data/Hora:</strong> {documento_gerado.data_assinatura.strftime('%d/%m/%Y %H:%M:%S') if documento_gerado.data_assinatura else ''}</p>
            <p><strong>IP:</strong> {documento_gerado.ip_assinatura or ''}</p>
            <p><strong>Autenticidade (Hash Único):</strong> {documento_gerado.token_acesso}</p>
        </div>
        '''
        
        full_html = f'''
        <html>
        <head>
            <style>
                body {{ font-family: Helvetica, Arial, sans-serif; font-size: 14px; color: #333; }}
                {css}
            </style>
        </head>
        <body>
            {html}
            {assinatura_block}
        </body>
        </html>
        '''
        
        buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.StringIO(full_html), dest=buffer)
        
        if not pisa_status.err:
            pdf_content = buffer.getvalue()
            buffer.close()
            
            filename = f"{documento_gerado.template.titulo[:30]}_{documento_gerado.token_acesso.hex[:8]}.pdf".replace(' ', '_')
            documento_gerado.arquivo_pdf_final.save(filename, ContentFile(pdf_content), save=True)
            return True
        else:
            buffer.close()
            # Fallback for errors if needed

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
    
    assinatura_base64 = dados.get('assinatura_base64', '')
    if assinatura_base64 and ',' in assinatura_base64:
        from reportlab.platypus import Image
        import base64
        try:
            # Separar o cabeçalho "data:image/png;base64,"
            formato, imgstr = assinatura_base64.split(';base64,')
            img_data = base64.b64decode(imgstr)
            img_io = io.BytesIO(img_data)
            elements.append(Image(img_io, width=200, height=80))
        except Exception:
            elements.append(Paragraph("___________________________________________________", assinatura_style))
    else:
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
