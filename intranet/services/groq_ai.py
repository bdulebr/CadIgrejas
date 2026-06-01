import os
import json
import tempfile
import openpyxl
import pdfplumber
from groq import Groq
from django.conf import settings

def obter_client_groq():
    api_key = getattr(settings, 'GROQ_API_KEY', '')
    if api_key:
        return Groq(api_key=api_key)
    return None

def extrair_texto_arquivo(file_obj, extensao):
    texto_final = ""
    if extensao in ['.xlsx', '.xls']:
        wb = openpyxl.load_workbook(file_obj, data_only=True)
        for sheet in wb.worksheets:
            for row in sheet.iter_rows(values_only=True):
                row_str = " | ".join([str(v) for v in row if v is not None])
                if row_str.strip():
                    texto_final += row_str + ""

    elif extensao == '.csv':
        texto_final = file_obj.read().decode('utf-8', errors='ignore')

    elif extensao == '.pdf':
        with pdfplumber.open(file_obj) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    texto_final += text + ""
    else:
        # Se for imagem ou formato não suportado textualmente, podemos avisar
        texto_final = "Formato de arquivo não suportado para extração de texto direta."

    return texto_final

def analisar_planilha_escalas_groq(file_obj):
    """
    Extrai o texto do arquivo e envia para o Groq analisar a escala.
    """
    client = obter_client_groq()
    if not client:
        raise Exception("Chave do Groq não configurada no sistema.")

    extensao = ".pdf"
    if hasattr(file_obj, 'name'):
        extensao = os.path.splitext(file_obj.name)[1].lower()

    # Como pdfplumber precisa de um file path local, vamos salvar num temp file
    tmp_path = None
    with tempfile.NamedTemporaryFile(delete=False, suffix=extensao) as tmp:
        for chunk in file_obj.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        with open(tmp_path, 'rb') as f_obj:
            text_data = extrair_texto_arquivo(f_obj, extensao)

        prompt = f"""
        Você é um Assistente de IA de OCR Avançado focado em Escalas de Voluntários de Igreja.
        Vou te passar o texto cru extraído de um PDF contendo uma escala.
        As tabelas podem estar em formatos variados (com colunas como "NOITE", "COLABORADORES", "Tema", "INTERCESSORES").

        Você DEVE extrair as informações e retornar ESTRITAMENTE o seguinte formato JSON:
        {{
          "departamento": "Nome do Departamento (Ex: Adolescentes, Audiovisual, Intercessão, Live)",
          "mes": "Mês por extenso ou número (Ex: Junho ou 06)",
          "ano": "Ano (deduza ser o ano atual se não houver)",
          "escalas": [
            {{
              "dia": "DD/MM/YYYY (converta o que achar, ex: Domingo 07/06 para 07/06/2026)",
              "turno": "Manhã ou Noite (se especificado)",
              "funcao": "Papel/Função específica (Ex: Câmera, Geral, Sonoplastia, Projeção). Deixe vazio se não houver.",
              "membros_nomes": ["Lista", "De", "Nomes", "Separados"],
              "observacao": "Qualquer tema, versículo ou nota daquele dia"
            }}
          ]
        }}

        - SE houver divisões claras de papel no mesmo dia (Ex: CÂMERA: ARTHUR / GERAL: PEDRO), você DEVE criar objetos JSON separados para cada Função.
        - SE houver divisões de turnos (Ex: Manhã: João / Noite: Maria), crie objetos separados.
        - Limpe e separe os nomes perfeitamente na lista 'membros_nomes' (tire "Miss", "Pr", etc, ou mantenha se não tiver certeza).

        Conteúdo lido:
        ========================================
        {text_data}
        ========================================
        """

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0
        )

        texto_json = response.choices[0].message.content
        dados = json.loads(texto_json)
        return dados

    except Exception as e:
        print("Erro no motor Groq OCR:", str(e))
        return []
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass

def gerar_escala_inteligente_groq(departamento_nome, mes, ano, membros, eventos, regras):
    """
    Usa a LPU Groq para gerar uma escala inteligente, balanceada e sem conflitos.
    """
    client = obter_client_groq()
    if not client:
        raise Exception("Chave do Groq não configurada.")

    prompt = f"""
    Você é um Motor de Inteligência Artificial de Alocação de Escalas (Workforce Management).
    Sua missão é gerar a escala do mês de {mes}/{ano} para o departamento '{departamento_nome}'.

    REGRAS DO MOTOR:
    1. Respeite estritamente os REQUISITOS (habilidades) de cada Função.
    2. Não aloque membros que estejam indisponíveis nas datas informadas.
    3. BALANCEAMENTO: Distribua a carga. Não aloque a mesma pessoa muitas vezes se houver outros disponíveis.
    4. Limite máximo geral: {regras.get('limite_mensal', 4)} vezes no mês por pessoa.
    5. Ninguém pode estar em dois lugares no mesmo dia/turno.

    MEMBROS ELEGÍVEIS (IDs, Nomes, Habilidades, Indisponibilidades):
    {json.dumps(membros, ensure_ascii=False)}

    EVENTOS DO MÊS E SLOTS NECESSÁRIOS:
    {json.dumps(eventos, ensure_ascii=False)}

    Você DEVE retornar ESTRITAMENTE o resultado no seguinte formato JSON, resolvendo o quebra-cabeça da alocação:
    {{
      "alocacoes": [
        {{
          "evento_id": "id do evento na lista",
          "data": "YYYY-MM-DD",
          "horario_inicio": "HH:MM",
          "funcao_id": "id da funcao",
          "membro_id": "ID INTEIRO do membro alocado"
        }}
      ]
    }}
    Retorne o dicionário completo.
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.2 # Baixa temperatura para lógica precisa
    )

    texto_json = response.choices[0].message.content
    dados = json.loads(texto_json)
    return dados
