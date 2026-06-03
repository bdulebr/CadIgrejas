import os
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from .models import CompetenciaEscala, Escala
from midia_lgpd.models import DocumentoTemplate
from core.models import ConfiguracaoSistema

def gerar_pdf_competencia(competencia_id):
    competencia = CompetenciaEscala.objects.get(id=competencia_id)
    escalas = Escala.objects.filter(competencia=competencia).order_by('data_escala', 'horario_inicio')

    if not escalas.exists():
        return False

    config_sys = ConfiguracaoSistema.objects.first()

    # 1. Obter o template do banco
    template_doc = DocumentoTemplate.objects.filter(identificador_sistema='pdf_escala_padrao', ativo=True).first()
    if not template_doc:
        print("Template de PDF da Escala não encontrado no banco de dados!")
        return False

    html = template_doc.html_canva
    css = template_doc.css_canva

    # 2. Gerar a tabela de escalas em HTML
    tabela_html = '''
    <table class="tabela-escala">
        <thead>
            <tr>
                <th style="width: 35%; text-align: center;">DATA / EVENTO</th>
                <th style="width: 65%; text-align: left;">COLABORADORES</th>
            </tr>
        </thead>
        <tbody>
    '''

    from collections import defaultdict
    agrupamento = defaultdict(list)

    dias_semana = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']

    for e in escalas:
        dia_str = dias_semana[e.data_escala.weekday()]
        data_str = f"{dia_str} {e.data_escala.strftime('%d/%m')}"
        evento_str = e.get_tipo_evento_display()

        chave = (data_str, evento_str)

        funcao_nome = e.funcao_alocada.nome.upper() if e.funcao_alocada else "-"
        # Usa o primeiro nome ou o nome completo
        voluntario_nome = e.membro_escalado.get_full_name().upper()

        if e.status == 'falta_justificada':
            voluntario_nome += " (FALTA)"
        elif e.status == 'substituido':
            voluntario_nome += " (SUBSTITUÍDO)"

        agrupamento[chave].append(f"{funcao_nome}: {voluntario_nome}")

    for (data_str, evento_str), lista_colab in agrupamento.items():
        colabs_str = "<br>".join(lista_colab)
        tabela_html += f'''
            <tr>
                <td style="text-align: center; vertical-align: middle;">
                    <strong>{data_str}</strong><br>
                    <span style="font-size: 10px; color: #444;">{evento_str}</span>
                </td>
                <td style="vertical-align: middle;">{colabs_str}</td>
            </tr>
        '''

    tabela_html += '</tbody></table>'

    # 3. Preparar as variáveis e os logos
    igreja_logo = ''
    if config_sys and config_sys.igreja_logo:
        igreja_logo = settings.BASE_URL + config_sys.igreja_logo.url

    departamento_logo = ''
    if competencia.departamento.logo:
        departamento_logo = settings.BASE_URL + competencia.departamento.logo.url

    igreja_nome = config_sys.igreja_nome if config_sys else "Igreja Local"
    igreja_cnpj = config_sys.cnpj if config_sys else "00.000.000/0000-00"

    # 4. Substituir as tags
    html = html.replace('{{IGREJA_LOGO}}', igreja_logo)
    html = html.replace('{{DEPARTAMENTO_LOGO}}', departamento_logo)
    html = html.replace('{{NOME_DEPARTAMENTO}}', competencia.departamento.nome)
    html = html.replace('{{COMPETENCIA}}', competencia.mes_ano)
    html = html.replace('{{IGREJA_NOME}}', igreja_nome)
    html = html.replace('{{IGREJA_CNPJ}}', igreja_cnpj)
    html = html.replace('{{ESCALA_TABELA_HTML}}', tabela_html)

    full_html = f'''
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Helvetica, Arial, sans-serif; }}
            {css}
        </style>
    </head>
    <body>
        {html}
    </body>
    </html>
    '''

    # 5. Gerar PDF via xhtml2pdf
    from xhtml2pdf import pisa

    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(full_html, dest=buffer)

    if pisa_status.err:
        return False

    pdf_value = buffer.getvalue()
    buffer.close()

    # 6. Salvar no model
    nome_arquivo = f"escala_{competencia.departamento.id}_{competencia.mes_ano.replace('/','_')}.pdf"
    competencia.pdf_gerado.save(nome_arquivo, ContentFile(pdf_value), save=True)

    return True
