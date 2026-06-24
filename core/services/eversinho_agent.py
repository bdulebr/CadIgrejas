import os
from google import genai
from google.genai import types
from django.conf import settings
from .eversinho_tools import gerenciar_membros, gerenciar_escalas, gerenciar_dossie
from .eversinho_rag import load_eversinho_docs

def ask_eversinho_agent(user_query: str, request_user) -> str:
    """
    Motor do Eversinho Agentic AI. Usa Google GenAI (Gemini) com Function Calling.
    O `request_user` é o usuário logado e será injetado nas chamadas de ferramentas.
    """
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_key:
        return "Olá! Eu sou o Eversinho, mas parece que estou sem voz no momento (Nenhuma API Key foi configurada no `.env`)."

    docs_context = load_eversinho_docs()

    system_prompt = f"""
Você é o "Eversinho", o assistente de Inteligência Artificial da Intranet da Palavra de Vida Enseada (CadIgrejas).
Você tem a capacidade de EXECUTAR AÇÕES no sistema usando as ferramentas disponíveis.
Você atua em nome do usuário logado: {request_user.get_full_name()} (Username: {request_user.username}).

=== INSTRUÇÕES DE UI ===
Você PODE responder usando marcação HTML direta combinada com TailwindCSS para apresentar resultados ricos.
Exemplo: Se você for mostrar uma lista de membros, você pode usar:
<div class="bg-gray-800 p-4 rounded-xl shadow-lg">
    <h3 class="text-white font-bold mb-2">Membros</h3>
    <ul class="text-gray-300">...</ul>
</div>
Se não precisar formatar HTML, use Markdown normal.

=== BASE DE CONHECIMENTO (RAG) ===
{docs_context}
================================

Se o usuário pedir para criar, listar ou modificar algo, SEMPRE tente usar uma ferramenta (Tool) se aplicável.
Se a ferramenta retornar "Deus tá vendo! Você não tem autorização", repasse a negativa ao usuário com humor leve, lembrando que a segurança do sistema bloqueou a ação.
"""

    client = genai.Client(api_key=gemini_key)

    # Declarando as ferramentas sem o parâmetro "user" para o LLM não se confundir
    def tool_gerenciar_membros(acao: str, nome: str = None, email: str = None, telefone: str = None) -> str:
        """Gerencia membros e voluntários. Permite listar ou criar."""
        return gerenciar_membros(request_user, acao, nome, email, telefone)

    def tool_gerenciar_escalas(acao: str, departamento_id: int = None, mes_ano: str = None, membro_id: int = None, data_escala: str = None, horario_inicio: str = "19:30:00", horario_fim: str = "21:30:00", tipo_evento: str = "1") -> str:
        """Gerencia escalas. acao='listar' ou 'criar_escala_membro'."""
        return gerenciar_escalas(request_user, acao, departamento_id, mes_ano, membro_id, data_escala, horario_inicio, horario_fim, tipo_evento)

    def tool_gerenciar_dossie(acao: str, casal_id: int = None, pastor: str = None, observacoes: str = None, nivel_crise: int = 1, atendimento_para: str = "Casal") -> str:
        """Gerencia dossiês confidenciais (casais). acao='listar' ou 'criar'."""
        return gerenciar_dossie(request_user, acao, casal_id, pastor, observacoes, nivel_crise, atendimento_para)

    tools = [tool_gerenciar_membros, tool_gerenciar_escalas, tool_gerenciar_dossie]

    try:
        chat = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                tools=tools,
                temperature=0.7,
            )
        )

        # Primeiro loop de conversa
        response = chat.send_message(user_query)

        # Verifica se o modelo decidiu usar uma ferramenta
        if response.function_calls:
            for function_call in response.function_calls:
                fn_name = function_call.name
                args = function_call.args

                # Executa a função
                result_str = ""
                if fn_name == "tool_gerenciar_membros":
                    result_str = tool_gerenciar_membros(**args)
                elif fn_name == "tool_gerenciar_escalas":
                    result_str = tool_gerenciar_escalas(**args)
                elif fn_name == "tool_gerenciar_dossie":
                    result_str = tool_gerenciar_dossie(**args)
                else:
                    result_str = f"Tool {fn_name} não implementada."

                # Manda o resultado da função de volta pro LLM
                response = chat.send_message(
                    types.Part.from_function_response(
                        name=fn_name,
                        response={"result": result_str}
                    )
                )

        return response.text

    except Exception as e:
        return f"Puxa, tive um pequeno curto-circuito ao pensar na resposta. Erro técnico: {str(e)}"
