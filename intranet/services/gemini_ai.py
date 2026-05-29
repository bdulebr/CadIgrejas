import os
import tempfile
from google import genai
from django.conf import settings

def obter_client_gemini():
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if api_key:
        return genai.Client(api_key=api_key)
    return None

def analisar_planilha_escalas(file_obj):
    """
    Usa o Gemini para extrair informações de escalas.
    Excel/CSV são lidos localmente e enviados como texto para maior precisão e rapidez.
    PDFs/Imagens são upados nativamente para a API de Visão do Gemini.
    """
    client = obter_client_gemini()
    if not client:
        raise Exception("Chave do Gemini não encontrada no arquivo Gemini_Ai.txt.")
        
    extensao = ".pdf"
    if hasattr(file_obj, 'name'):
        extensao = os.path.splitext(file_obj.name)[1].lower()

    prompt_base = """
    Você é um assistente de OCR focado em Escalas de Voluntários de Igreja.
    Extraia as informações de escalas e devolva ESTRITAMENTE em formato JSON (uma lista de objetos).
    Não use formatação markdown de código (ex: ```json), devolva apenas o JSON bruto válido.
    As chaves obrigatórias para cada objeto são:
    - "nome_membro": Nome completo da pessoa.
    - "dia": Data no formato YYYY-MM-DD.
    - "horario_inicio": Horário de início no formato HH:MM (ex: 09:30).
    - "departamento": Nome do departamento (ex: Midia, Louvor, Portaria).
    
    Se houver várias pessoas, retorne todas. Se um campo faltar, deduza inteligentemente.
    """

    conteudos_envio = []
    tmp_path = None

    try:
        if extensao in ['.xlsx', '.xls']:
            # Leitura nativa e envio em texto
            import openpyxl
            wb = openpyxl.load_workbook(file_obj, data_only=True)
            text_data = ""
            for sheet in wb.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    row_str = " | ".join([str(v) for v in row if v is not None])
                    if row_str.strip():
                        text_data += row_str + "\n"
            
            prompt_final = prompt_base + f"\n\nDados extraídos da planilha:\n{text_data}"
            conteudos_envio = [prompt_final]
            
        elif extensao == '.csv':
            # Leitura nativa e envio em texto
            text_data = file_obj.read().decode('utf-8', errors='ignore')
            prompt_final = prompt_base + f"\n\nDados extraídos do CSV:\n{text_data}"
            conteudos_envio = [prompt_final]
            
        else:
            # Upload visual (PDF, Imagens)
            if not extensao: extensao = ".pdf"
            with tempfile.NamedTemporaryFile(delete=False, suffix=extensao) as tmp:
                for chunk in file_obj.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name
                
            arquivo_gemini = client.files.upload(file=tmp_path)
            conteudos_envio = [arquivo_gemini, prompt_base]

        # Chamada ao Gemini 2.5 Flash
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=conteudos_envio
        )
        
        texto_limpo = response.text.replace('```json', '').replace('```', '').strip()
        
        # Corrige erro se vier vazio
        if not texto_limpo: return []
        
        import json
        dados = json.loads(texto_limpo)
        return dados
        
    except Exception as e:
        print("Erro no motor Gemini OCR:", str(e))
        return []
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass
