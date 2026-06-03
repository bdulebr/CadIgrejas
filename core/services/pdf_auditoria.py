import io
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from django.utils import timezone

def gerar_laudo_pericial_pdf(log):
    """
    Gera um PDF forense baseado em um LogAuditoria.
    Retorna os bytes do PDF gerado.
    """
    buffer = io.BytesIO()

    # Configura documento PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom Styles
    style_title = ParagraphStyle(
        name='TitleStyle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=16,
        spaceAfter=15,
        textColor=colors.HexColor('#1E293B')
    )

    style_normal = ParagraphStyle(
        name='NormalStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8,
        leading=14
    )

    style_mono = ParagraphStyle(
        name='MonoStyle',
        parent=styles['Code'],
        fontSize=9,
        textColor=colors.HexColor('#0F172A'),
        backColor=colors.HexColor('#F1F5F9'),
        borderPadding=5,
    )

    story = []

    # Cabeçalho Oficial
    story.append(Paragraph("LAUDO DE AUDITORIA FORENSE - ZERO TRUST", style_title))
    story.append(Paragraph("SISTEMA DE INTRANET - IGREJA PALAVRA DE VIDA ENSEADA", ParagraphStyle(name='SubTitle', parent=style_title, fontSize=12)))
    story.append(Spacer(1, 0.2 * inch))

    # Identificação do Documento
    story.append(Paragraph(f"<b>ID do Registro (DB):</b> #{log.id}", style_normal))
    story.append(Paragraph(f"<b>Data e Hora da Geração:</b> {timezone.localtime(log.data_hora).strftime('%d/%m/%Y %H:%M:%S')} (Hora de Brasília)", style_normal))

    # Informações do Usuário (Ator)
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("1. DADOS DO AUTOR (ATOR)", styles['Heading3']))

    if log.usuario_acao:
        u = log.usuario_acao
        story.append(Paragraph(f"<b>Nome Registrado:</b> {u.get_full_name()} ({u.username})", style_normal))
        story.append(Paragraph(f"<b>E-mail Principal:</b> {u.email}", style_normal))
        story.append(Paragraph(f"<b>Nível Hierárquico no Sistema:</b> {u.get_nivel_hierarquico_display()}", style_normal))
    else:
        story.append(Paragraph("<b>Autor:</b> SISTEMA INTERNO / ROTINA BACKGROUND", style_normal))

    # Informações do Ambiente (Rede e Dispositivo)
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("2. VETOR DE ORIGEM (REDE E DISPOSITIVO)", styles['Heading3']))
    story.append(Paragraph(f"<b>Endereço IP Localizado:</b> {log.ip_origem or 'N/A'}", style_normal))
    story.append(Paragraph(f"<b>Geolocalização (Estimada):</b> {log.cidade_origem or 'N/A'}", style_normal))
    story.append(Paragraph(f"<b>Provedor de Internet (ISP):</b> {log.isp_origem or 'N/A'}", style_normal))
    story.append(Paragraph(f"<b>Impressão Digital do Aparelho (User-Agent):</b>", style_normal))
    story.append(Paragraph(str(log.user_agent or 'N/A'), style_mono))

    # O que foi feito
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("3. DESCRIÇÃO DA AÇÃO REALIZADA", styles['Heading3']))
    story.append(Paragraph(f"<b>Módulo/Tabela Interceptada:</b> {log.tabela_afetada}", style_normal))
    story.append(Paragraph(f"<b>Tipo de Operação:</b> {log.acao_realizada}", style_normal))

    # JSON Parsing para leitura legível
    diferenca = log.diferenca_json
    if isinstance(diferenca, str):
        try:
            diferenca = json.loads(diferenca)
        except json.JSONDecodeError:
            pass

    diff_formatado = json.dumps(diferenca, indent=4, ensure_ascii=False)
    story.append(Paragraph("<b>Payload Completo / Intenção de UX:</b>", style_normal))
    story.append(Paragraph(diff_formatado.replace('\n', '<br/>').replace(' ', '&nbsp;'), style_mono))

    # Criptografia (Validade Jurídica)
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("4. ASSINATURA CRIPTOGRÁFICA (HASH CHAIN ZERO-TRUST)", styles['Heading3']))
    story.append(Paragraph("Este registro é matematicamente imutável. Qualquer adulteração direta no banco de dados quebraria o elo entre o 'Hash Anterior' e o 'Hash Atual'.", style_normal))
    story.append(Paragraph("<b>Hash do Bloco Anterior:</b>", style_normal))
    story.append(Paragraph(log.hash_anterior, style_mono))
    story.append(Paragraph("<b>Hash Deste Bloco (Assinatura SHA-256):</b>", style_normal))
    story.append(Paragraph(log.hash_atual, style_mono))

    # Termo de Responsabilidade
    story.append(Spacer(1, 0.5 * inch))
    termo = ("Este documento possui validade sistêmica interna e serve como peça pericial/investigativa. "
             "De acordo com a Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018), os dados aqui contidos devem ser mantidos em estrito sigilo.")
    story.append(Paragraph(termo, ParagraphStyle(name='Small', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#64748B'), alignment=TA_JUSTIFY)))

    doc.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
