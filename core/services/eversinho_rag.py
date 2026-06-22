import os
import glob
from google import genai
from django.conf import settings

def load_eversinho_docs():
    """
    Carrega os documentos REAIS de regras de negócio e os guias passo-a-passo.
    Como os arquivos reais são pequenos e densos, podemos mandar todos para a IA sem esgotar o limite gratuito!
    """
    docs_dir = os.path.join(settings.BASE_DIR, 'docs')
    ajuda_dir = os.path.join(docs_dir, 'Eversinho Ajuda')

    content = "=== MANUAIS E REGRAS GLOBAIS ===\n"

    # 1. Carregar documentos-chave de regras (se existirem)
    core_files = [
        "Regras Globais.txt",
        "Modulos.txt",
        "4_Modulos_Em_Detalhes.md",
        "Usuarios admins e Lideres.txt"
    ]

    for filename in core_files:
        filepath = os.path.join(docs_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content += f"\n\n--- Documento: {filename} ---\n"
                content += f.read()

    # 2. Carregar Guias de Ajuda Passo-a-Passo criados pelo usuário
    content += "\n\n=== GUIAS PASSO-A-PASSO (EVERSINHO AJUDA) ===\n"
    if os.path.exists(ajuda_dir):
        md_files = glob.glob(os.path.join(ajuda_dir, "*.md"))
        for file in md_files:
            with open(file, 'r', encoding='utf-8') as f:
                content += f"\n\n--- Guia: {os.path.basename(file)} ---\n"
                content += f.read()

    return content

def ask_eversinho(user_query: str) -> str:
    """
    Função principal de RAG do Eversinho usando o ChatGPT (OpenAI) como motor principal,
    com fallback para o Gemini 2.5 Flash caso a chave não exista.
    """
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    gemini_key = os.environ.get("GEMINI_API_KEY", "")

    if not openai_key and not gemini_key:
        return "Olá! Eu sou o Eversinho, mas parece que estou sem voz no momento (Nenhuma API Key foi configurada no `.env`). Peça ao SysAdmin para me dar vida!"

    docs_context = load_eversinho_docs()

    system_prompt = f"""
Você é o "Eversinho", o mascote de IA super inteligente da Intranet da Palavra de Vida Enseada (PV Enseada).
Você SEMPRE responde em Português do Brasil de forma precisa, assertiva e levemente animada (use emojis).
Sua principal função é ajudar a usar o sistema baseado SOMENTE na documentação oficial.

=== MAPA DE LINKS RÁPIDOS ===
Use estes links (em formato Markdown [Nome](/url/)) sempre que ensinar o usuário a ir para uma tela:
- Gestão de Membros / Voluntários: `/membros/`
- Adicionar Membro / Voluntário: `/membros/adicionar/`
- Painel de Departamentos: `/departamentos/`
- Painel do Líder: `/painel-lider/`
- Módulo de RH do Líder: `/painel-lider/rh/`
- Escalas / Gerenciamento: `/escalas/`
- Minhas Escalas (Mobile): `/minhas-escalas/`
- Almoxarifado / Estoque: `/almoxarifado/`
- Mídia & LGPD (Termos): `/midia/`
- Tesouraria / Caixa: `/tesouraria/`
- Ponto de Venda (PDV): `/pdv/`
- Visitantes: `/visitantes/`
- Ministério de Casais: `/casais/`
- Gabinete Pastoral: `/gabinete-pastoral/`
- Painel SysAdmin: `/sysadmin/`
=============================

Abaixo está a SUA BASE DE CONHECIMENTO (Extraída dos arquivos originais do projeto).
Toda e qualquer instrução de como os módulos funcionam, atalhos, integrações e Regras de Negócio estão aí.
Exemplo: Para cadastrar voluntários, geralmente isso é feito no módulo de Membros ou através de cadastro específico. Leia o contexto e responda corretamente!

====== INÍCIO DA BASE DE CONHECIMENTO ======
{docs_context}
====== FIM DA BASE DE CONHECIMENTO ======

Regras de Resposta:
1. Responda DIRETAMENTE à pergunta sendo MUITO INTELIGENTE e preciso com base no contexto.
2. Não invente passos genéricos. Use os detalhes técnicos e práticos da base de conhecimento.
3. SEMPRE QUE POSSÍVEL, inclua links clicáveis (Markdown) para a tela que você está explicando, consultando o Mapa de Links Rápidos acima! Lembre o usuário de que ele precisa ter as permissões necessárias.
4. Se perguntarem algo não especificado na base, deduza pela lógica dos módulos apresentados ou informe que o manual detalhado daquele módulo ainda será escrito na pasta 'Eversinho Ajuda'.
5. Seja conciso. Use negritos e listas quando for passo-a-passo.
"""

    try:
        if openai_key:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            try:
                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_query}
                    ]
                )
                return completion.choices[0].message.content
            except Exception as openai_e:
                print(f"Erro no OpenAI ({openai_e}), acionando fallback Gemini...")
                if not gemini_key:
                    raise openai_e

        # Se não tem OpenAI key ou falhou no try acima, vai pro Gemini
        client = genai.Client(api_key=gemini_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[system_prompt, f"Pergunta do Usuário: {user_query}"]
        )
        return response.text

    except Exception as e:
        return f"Puxa, tive um pequeno curto-circuito ao pensar na resposta. Erro técnico: {str(e)}"
