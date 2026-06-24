import os
from google import genai
from google.genai import types
from django.conf import settings
from .eversinho_tools import gerenciar_membros, gerenciar_escalas, gerenciar_dossie, gerenciar_drive
from .eversinho_rag import load_eversinho_docs

def ask_eversinho_agent(user_query: str, request_user, history: list = None) -> str:
    """
    Motor do Eversinho Agentic AI. Usa Google GenAI (Gemini) com Function Calling.
    O `request_user` é o usuário logado e será injetado nas chamadas de ferramentas.
    `history` é a lista de mensagens anteriores do tipo types.Content.
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

=== GESTÃO DE ARQUIVOS (PV DRIVE) ===
Se o usuário lhe enviar uma mensagem dizendo que enviou um anexo (o sistema informará o ID do anexo), e pedir para guardar em uma pasta, use a ferramenta 'gerenciar_drive' com acao='mover_anexo' passando o arquivo_id e o pasta_id destino. Você pode usar acao='listar' primeiro para descobrir os IDs das pastas caso não saiba.

=== BASE DE CONHECIMENTO (RAG) ===
{docs_context}
================================

Se o usuário pedir para criar, listar ou modificar algo, SEMPRE tente usar uma ferramenta (Tool) se aplicável.
Se a ferramenta retornar "Deus tá vendo! Você não tem autorização", repasse a negativa ao usuário com humor leve, lembrando que a segurança do sistema bloqueou a ação.
"""

    if history:
        hist_str = "\\n".join([f"{h['role'].upper()}: {h['text']}" for h in history])
        system_prompt += f"\\n\\n=== HISTÓRICO DA CONVERSA NESTA SESSÃO ===\\n{hist_str}"

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

    def tool_gerenciar_drive(acao: str, nome: str = None, pasta_id: int = None, arquivo_id: int = None, membro_alvo_id: int = None, nivel_permissao: str = 'leitor') -> str:
        """Gerencia o sistema de arquivos (PV Drive). acao='listar', 'criar_pasta', 'renomear_pasta', 'excluir_pasta', 'excluir_arquivo', 'compartilhar_pasta', 'mover_anexo'."""
        return gerenciar_drive(request_user, acao, nome, pasta_id, arquivo_id, membro_alvo_id, nivel_permissao)

    tools = [tool_gerenciar_membros, tool_gerenciar_escalas, tool_gerenciar_dossie, tool_gerenciar_drive]

    openai_key = os.environ.get("OPENAI_API_KEY", "")

    import time
    max_retries = 3

    # Define tools schema for OpenAI
    tools_openai = [
        {"type": "function", "function": {"name": "tool_gerenciar_membros", "description": "Gerencia membros e voluntários. Permite listar ou criar.", "parameters": {"type": "object", "properties": {"acao": {"type": "string"}, "nome": {"type": "string"}, "email": {"type": "string"}, "telefone": {"type": "string"}}, "required": ["acao"]}}},
        {"type": "function", "function": {"name": "tool_gerenciar_escalas", "description": "Gerencia escalas. acao='listar' ou 'criar_escala_membro'.", "parameters": {"type": "object", "properties": {"acao": {"type": "string"}, "departamento_id": {"type": "integer"}, "mes_ano": {"type": "string"}, "membro_id": {"type": "integer"}, "data_escala": {"type": "string"}, "horario_inicio": {"type": "string"}, "horario_fim": {"type": "string"}, "tipo_evento": {"type": "string"}}, "required": ["acao"]}}},
        {"type": "function", "function": {"name": "tool_gerenciar_dossie", "description": "Gerencia dossiês confidenciais (casais). acao='listar' ou 'criar'.", "parameters": {"type": "object", "properties": {"acao": {"type": "string"}, "casal_id": {"type": "integer"}, "pastor": {"type": "string"}, "observacoes": {"type": "string"}, "nivel_crise": {"type": "integer"}, "atendimento_para": {"type": "string"}}, "required": ["acao"]}}},
        {"type": "function", "function": {"name": "tool_gerenciar_drive", "description": "Gerencia o sistema de arquivos (PV Drive). acao='listar', 'criar_pasta', 'renomear_pasta', 'excluir_pasta', 'excluir_arquivo', 'compartilhar_pasta', 'mover_anexo'.", "parameters": {"type": "object", "properties": {"acao": {"type": "string"}, "nome": {"type": "string"}, "pasta_id": {"type": "integer"}, "arquivo_id": {"type": "integer"}, "membro_alvo_id": {"type": "integer"}, "nivel_permissao": {"type": "string"}}, "required": ["acao"]}}}
    ]

    for attempt in range(max_retries):
        try:
            if openai_key and attempt == 0:
                # Tentativa primária com OpenAI (conforme planejado originalmente)
                from openai import OpenAI
                import json
                client_openai = OpenAI(api_key=openai_key)

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ]

                completion = client_openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=tools_openai
                )

                response_msg = completion.choices[0].message

                if response_msg.tool_calls:
                    messages.append(response_msg)
                    for tool_call in response_msg.tool_calls:
                        fn_name = tool_call.function.name
                        args = json.loads(tool_call.function.arguments)

                        result_str = ""
                        if fn_name == "tool_gerenciar_membros": result_str = tool_gerenciar_membros(**args)
                        elif fn_name == "tool_gerenciar_escalas": result_str = tool_gerenciar_escalas(**args)
                        elif fn_name == "tool_gerenciar_dossie": result_str = tool_gerenciar_dossie(**args)
                        elif fn_name == "tool_gerenciar_drive": result_str = tool_gerenciar_drive(**args)
                        else: result_str = f"Tool {fn_name} não implementada."

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": fn_name,
                            "content": result_str
                        })

                    second_response = client_openai.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages
                    )
                    return second_response.choices[0].message.content
                else:
                    return response_msg.content

            else:
                # Fallback para Gemini (ou se OpenAI falhou no attempt 0)
                if not gemini_key:
                    raise Exception("Sem chaves de API disponíveis.")

                chat = client.chats.create(
                    model="gemini-2.5-flash",
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        tools=tools,
                        temperature=0.7,
                    )
                )

                response = chat.send_message(user_query)

                if response.function_calls:
                    for function_call in response.function_calls:
                        fn_name = function_call.name
                        args = function_call.args

                        result_str = ""
                        if fn_name == "tool_gerenciar_membros": result_str = tool_gerenciar_membros(**args)
                        elif fn_name == "tool_gerenciar_escalas": result_str = tool_gerenciar_escalas(**args)
                        elif fn_name == "tool_gerenciar_dossie": result_str = tool_gerenciar_dossie(**args)
                        elif fn_name == "tool_gerenciar_drive": result_str = tool_gerenciar_drive(**args)
                        else: result_str = f"Tool {fn_name} não implementada."

                        response = chat.send_message(
                            types.Part.from_function_response(
                                name=fn_name,
                                response={"result": result_str}
                            )
                        )

                return response.text

        except Exception as e:
            error_str = str(e)
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return f"Puxa, tive um pequeno curto-circuito ao pensar na resposta. Erro técnico: {error_str}"
