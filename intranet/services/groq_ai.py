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
                    texto_final += row_str + "\n"

    elif extensao == '.csv':
        texto_final = file_obj.read().decode('utf-8', errors='ignore')

    elif extensao == '.pdf':
        with pdfplumber.open(file_obj) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    texto_final += text + "\n"
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
        Você é um assistente de extração de dados focado em Escalas de Voluntários de Igreja.
        Extraia as informações da seguinte escala em texto bruto e devolva ESTRITAMENTE em formato JSON.
        O JSON deve ser uma lista de objetos contendo as chaves:
        - "nome_membro" (string)
        - "dia" (string formato YYYY-MM-DD)
        - "horario_inicio" (string formato HH:MM)
        - "departamento" (string)

        Aqui está o conteúdo do arquivo lido localmente:
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

        # Como o response_format="json_object" obriga um dicionário, o modelo geralmente coloca
        # a lista dentro de uma chave como {"escalas": [...]}. Precisamos normalizar isso.
        dados = json.loads(texto_json)

        # Procurar pela primeira lista dentro do json
        if isinstance(dados, list):
            return dados
        elif isinstance(dados, dict):
            for k, v in dados.items():
                if isinstance(v, list):
                    return v

        return [dados] if isinstance(dados, dict) else []

    except Exception as e:
        print("Erro no motor Groq OCR:", str(e))
        return []
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass
