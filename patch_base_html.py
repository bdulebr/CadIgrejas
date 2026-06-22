import re

with open("core/templates/core/base.html", "r", encoding="utf-8") as f:
    content = f.read()

chat_widget = """
    <!-- Botão Flutuante Eversinho Help-Me -->
    <div x-data="{ chatOpen: false }" class="fixed bottom-6 right-6 z-[99999]">
        <!-- Botão Principal -->
        <button @click="chatOpen = !chatOpen"
                class="w-16 h-16 rounded-full bg-blue-600 border-4 border-white shadow-[0_0_20px_rgba(37,99,235,0.6)] hover:scale-110 transition-transform overflow-hidden animate-bounce" title="Precisa de ajuda? Fale comigo!">
            <img src="/static/img/eversinho/ever_joinha.png" alt="Eversinho IA" class="w-full h-full object-cover">
        </button>

        <!-- Janela do Chat -->
        <div x-show="chatOpen"
             x-transition:enter="transition ease-out duration-300 transform"
             x-transition:enter-start="opacity-0 translate-y-10 scale-95"
             x-transition:enter-end="opacity-100 translate-y-0 scale-100"
             x-transition:leave="transition ease-in duration-200 transform"
             x-transition:leave-start="opacity-100 translate-y-0 scale-100"
             x-transition:leave-end="opacity-0 translate-y-10 scale-95"
             @click.away="chatOpen = false"
             class="absolute bottom-20 right-0 w-[350px] bg-gray-900 border border-gray-700 rounded-2xl shadow-[0_10px_50px_rgba(0,0,0,0.8)] overflow-hidden flex flex-col" style="display: none; height: 500px;">

            <!-- Header do Chat -->
            <div class="bg-blue-700 p-4 flex items-center justify-between border-b border-blue-500 shadow-md">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full overflow-hidden border-2 border-white bg-blue-900">
                        <img src="/static/img/eversinho/ever_joinha.png" alt="Eversinho" class="w-full h-full object-cover">
                    </div>
                    <div>
                        <h3 class="font-bold text-white text-md">Eversinho IA</h3>
                        <p class="text-xs text-blue-200">Seu assistente virtual de Ajuda</p>
                    </div>
                </div>
                <button @click="chatOpen = false" class="text-white hover:text-gray-300">
                    <i data-lucide="x" class="w-5 h-5"></i>
                </button>
            </div>

            <!-- Corpo do Chat (Mensagens) -->
            <div id="eversinho-chat-body" class="flex-grow p-4 overflow-y-auto flex flex-col space-y-4 bg-gray-900 custom-scrollbar">
                <!-- Bolha de boas vindas -->
                <div class="flex justify-start animate-fade-in-up">
                    <div class="bg-gray-800 text-gray-200 p-3 rounded-xl rounded-tl-none max-w-[85%] shadow-md border border-gray-700">
                        <p class="text-sm">Olá! 👋 Eu sou o Eversinho! Eu li <b>todos os manuais e regras da Igreja</b> e estou pronto para te ajudar. Pode perguntar qualquer coisa sobre os módulos!</p>
                    </div>
                </div>
            </div>

            <!-- Input do Chat -->
            <div class="p-3 border-t border-gray-800 bg-gray-900">
                <form hx-post="/api/eversinho/chat/"
                      hx-target="#eversinho-chat-body"
                      hx-swap="beforeend"
                      hx-on::before-request="this.querySelector('button').disabled = true; this.querySelector('input').disabled = true; this.querySelector('button').innerHTML = '<i data-lucide=\\'loader-2\\' class=\\'w-4 h-4 animate-spin\\'></i>';"
                      hx-on::after-request="this.reset(); this.querySelector('button').disabled = false; this.querySelector('input').disabled = false; this.querySelector('button').innerHTML = '<i data-lucide=\\'send\\' class=\\'w-4 h-4\\'></i>'; let b = document.getElementById('eversinho-chat-body'); setTimeout(()=> b.scrollTop = b.scrollHeight, 100); lucide.createIcons();"
                      class="flex gap-2">
                    <input type="text" name="mensagem" required autocomplete="off" placeholder="Digite sua dúvida aqui..." class="flex-grow bg-gray-800 border border-gray-700 text-white rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm">
                    <button type="submit" class="bg-blue-600 hover:bg-blue-500 text-white w-10 h-10 rounded-xl flex items-center justify-center transition-colors shrink-0 shadow-md">
                        <i data-lucide="send" class="w-4 h-4"></i>
                    </button>
                </form>
            </div>
        </div>
    </div>
"""

if "Eversinho Help-Me" not in content:
    content = content.replace("<!-- Indicador Global HTMX -->", chat_widget + "\n    <!-- Indicador Global HTMX -->")
    with open("core/templates/core/base.html", "w", encoding="utf-8") as f:
        f.write(content)
    print("Widget adicionado!")
else:
    print("Já existe.")
