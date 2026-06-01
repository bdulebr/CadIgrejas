import io
from xhtml2pdf import pisa

def gerar_pdf(html_string, footer_text=None):
    """
    Gera um PDF a partir de uma string HTML usando xhtml2pdf.
    Retorna os bytes do PDF ou None em caso de erro.
    """
    if footer_text:
        html_string = html_string.replace('</body>', f'<div style="margin-top: 50px; text-align: center; font-size: 10px; color: #777;">{footer_text}</div></body>')

    buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(html_string), dest=buffer)

    if not pisa_status.err:
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    else:
        buffer.close()
        return None
