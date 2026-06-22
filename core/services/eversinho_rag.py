import os
import glob
import google.generativeai as genai
from django.conf import settings

def load_eversinho_docs():
    """
    Carrega o conteúdo de todos os arquivos .md da pasta 'docs/Eversinho Ajuda'
    """
    base_dir = os.path.join(settings.BASE_DIR, 'docs', 'Eversinho Ajuda')
    if not os.path.exists(base_dir):
        return ""

    md_files = glob.glob(os.path.join(base_dir, "*.md"))
    content = ""
    for file in md_files:
        with open(file, 'r', encoding='utf-8') as f:
            content += f"\n\n--- Arquivo: {os.path.basename(file)} ---\n"
            content += f.read()
    return content

def ask_eversinho(user_query: str) -> str:
    """
    Função principal de RAG do Eversinho.
    Busca contexto nos arquivos Markdown locais e formula uma resposta usando Gemini.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return "Olá! Eu sou o Eversinho, mas parece que estou sem voz no momento (A chave GEMINI_API_KEY não foi configurada no `.env`). Peça ao SysAdmin para me dar vida!"

    genai.configure(api_key=api_key)

    # Modelo focado em contexto vasto e velocidade (1.5 Flash suporta 1M tokens)
    model = genai.GenerativeModel('gemini-1.5-flash')

    docs_context = load_eversinho_docs()

    system_prompt = f"""
Você é o "Eversinho", o amigável mascote de Inteligência Artificial e Assistente Virtual da Intranet da Palavra de Vida Enseada (PV Enseada).
Você SEMPRE responde em Português do Brasil de forma prestativa, clara e levemente animada (use emojis).
Sua principal função é ajudar os membros, líderes e pastores a entenderem como usar o sistema.

Abaixo está a SUA BASE DE CONHECIMENTO, extraída da pasta 'docs/Eversinho Ajuda'.
Toda e qualquer instrução de como os módulos funcionam, atalhos, integrações e Regras de Negócio/LGPD estão aí.
USE ESTA BASE para responder a pergunta do usuário.

====== INÍCIO DA BASE DE CONHECIMENTO ======
{docs_context}
====== FIM DA BASE DE CONHECIMENTO ======

Regras de Resposta:
1. Responda DIRETAMENTE à pergunta usando a Base de Conhecimento.
2. Não diga que você leu um arquivo, apenas passe a instrução como se fosse você mesmo quem soubesse.
3. Se a pergunta não estiver na base, diga educadamente que você ainda não aprendeu sobre isso, mas vai anotar para o Sysadmin te ensinar depois.
4. Mantenha respostas curtas e formatadas em Markdown ou HTML básico se for uma lista de passos.

Pergunta do Usuário: {user_query}
"""

    try:
        response = model.generate_content(system_prompt)
        return response.text
    except Exception as e:
        return f"Puxa, tive um pequeno curto-circuito ao pensar na resposta. Erro técnico: {str(e)}"
