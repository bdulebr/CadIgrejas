import os
import re

def append_gemini_escala():
    filepath = 'C:/Users/MarcosLira/Desktop/Marcos/Projeto/intranet/services/gemini_ai.py'
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write('''
def gerar_escala_inteligente_gemini(departamento_nome, mes, ano, membros, eventos, regras):
    """
    Usa o Gemini 2.5 Flash para gerar uma escala inteligente, balanceada e sem conflitos.
    """
    client = get_gemini_client()

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
    Retorne apenas o JSON, sem marcações markdown.
    """

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )

    texto = response.text.strip()
    if texto.startswith("```json"):
        texto = texto[7:]
    if texto.endswith("```"):
        texto = texto[:-3]
    dados = json.loads(texto.strip())
    return dados
''')

append_gemini_escala()
print("Appended gerar_escala_inteligente_gemini to gemini_ai.py")
