"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: escalas/pdf_generator.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
import os
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from .models import CompetenciaEscala, Escala
from core.models import ConfiguracaoSistema

def gerar_pdf_competencia(competencia_id):
    competencia = CompetenciaEscala.objects.get(id=competencia_id)
    escalas = Escala.objects.filter(competencia=competencia).order_by('data_escala', 'horario_inicio')

    if not escalas.exists():
        return False

    config_sys = ConfiguracaoSistema.objects.first()

    from django.template.loader import render_to_string
    import datetime

    # 1. Preparar dados para o contexto
    from collections import defaultdict
    agrupamento = defaultdict(list)

    dias_semana = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']

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

    linhas_escala = []
    for (data_str, evento_str), lista_colab in agrupamento.items():
        colabs_str = "<br>".join(lista_colab)
        linhas_escala.append({
            'data_str': data_str,
            'evento_str': evento_str,
            'colabs_str': colabs_str
        })

    # 2. Preparar as variáveis e os logos
    logo_path = ''
    if config_sys and config_sys.igreja_logo:
        logo_path = config_sys.igreja_logo.url
    else:
        logo_path = settings.STATIC_URL + 'img/logo.jpg'

    departamento_logo = ''
    if competencia.departamento.logo:
        departamento_logo = competencia.departamento.logo.url

    igreja_nome = config_sys.igreja_nome if config_sys else "Igreja Local"
    igreja_cnpj = config_sys.cnpj if config_sys else "00.000.000/0000-00"

    # 3. Renderizar o template
    context = {
        'logo_path': logo_path,
        'departamento_logo': departamento_logo,
        'IGREJA_NOME': igreja_nome,
        'IGREJA_CNPJ': igreja_cnpj,
        'competencia': competencia,
        'linhas_escala': linhas_escala,
        'mes_ano': competencia.mes_ano,
        'data_geracao': datetime.datetime.now()
    }

    full_html = render_to_string('escalas/pdf_escala.html', context)

    # 5. Gerar PDF via xhtml2pdf
    from xhtml2pdf import pisa

    def fetch_resources(uri, rel):
        if uri.startswith(settings.MEDIA_URL):
            return os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
        elif uri.startswith(settings.STATIC_URL):
            return os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))
        return uri

    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(full_html, dest=buffer, link_callback=fetch_resources)

    if pisa_status.err:
        return False

    pdf_value = buffer.getvalue()
    buffer.close()

    # 6. Salvar no model
    nome_arquivo = f"escala_{competencia.departamento.id}_{competencia.mes_ano.replace('/', '_')}.pdf"
    competencia.pdf_gerado.save(nome_arquivo, ContentFile(pdf_value), save=True)

    return True
