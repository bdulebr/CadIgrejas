import os

with open("core/views.py", "a", encoding="utf-8") as f:
    f.write("""

@login_required
@csrf_exempt
def eversinho_chat_api(request):
    import time
    from core.services.eversinho_rag import ask_eversinho

    if request.method == 'POST':
        user_msg = request.POST.get('mensagem', '').strip()
        if not user_msg:
            return HttpResponse("Bolha de erro: mensagem vazia.")

        # Call RAG logic
        resposta_ia = ask_eversinho(user_msg)

        # Return an HTML fragment with two bubbles: User bubble + AI bubble
        # HTMX will append this to the chat window
        html = f'''
        <div class="flex justify-end mb-4 animate-fade-in-up">
            <div class="bg-blue-600 text-white p-3 rounded-xl rounded-tr-none max-w-[80%] shadow-md">
                <p class="text-sm">{user_msg}</p>
            </div>
        </div>
        <div class="flex justify-start mb-4 animate-fade-in-up stagger-1">
            <div class="flex-shrink-0 mr-3">
                <div class="w-8 h-8 rounded-full bg-blue-900 border border-blue-400 flex items-center justify-center overflow-hidden">
                    <img src="/static/img/eversinho/ever_joinha.png" alt="Eversinho" class="w-full h-full object-cover">
                </div>
            </div>
            <div class="bg-gray-800 text-gray-200 p-3 rounded-xl rounded-tl-none max-w-[80%] shadow-md border border-gray-700">
                <div class="text-sm prose prose-invert prose-sm max-w-none">{resposta_ia}</div>
            </div>
        </div>
        '''
        return HttpResponse(html)
    return HttpResponse("Método não permitido.")
""")

print("View adicionada!")
