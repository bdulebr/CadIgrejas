import os

# 1. Update escalas/views.py
views_escalas_code = '''
@login_required
def importar_escala_ocr(request):
    if request.method == 'POST':
        arquivo = request.FILES.get('arquivo_escala')
        if not arquivo:
            messages.error(request, 'Você deve selecionar um arquivo PDF, Excel ou CSV.')
            return redirect('painel_escalas')
            
        try:
            from intranet.services.groq_ai import analisar_planilha_escalas_groq
            dados_escala = analisar_planilha_escalas_groq(arquivo)
            
            if not dados_escala:
                messages.warning(request, 'O Groq não conseguiu extrair nenhuma escala do arquivo.')
                return redirect('painel_escalas')
                
            # Salvar os dados na sessão ou gerar a escala diretamente
            # Para manter simples, vamos avisar que processou X registros
            messages.success(request, f'O Groq processou {len(dados_escala)} registros de escala com sucesso! A integração final de salvamento requer alinhamento do formato de saída.')
            
        except Exception as e:
            messages.error(request, f'Erro no processamento OCR (Groq): {str(e)}')
            
    return redirect('painel_escalas')
'''

with open('escalas/views.py', 'a', encoding='utf-8') as f:
    f.write(views_escalas_code)

# 2. Update escalas/urls.py
with open('escalas/urls.py', 'r', encoding='utf-8') as f:
    escalas_urls = f.read()

escalas_urls = escalas_urls.replace(']', "    path('escalas/importar-ocr/', views.importar_escala_ocr, name='importar_escala_ocr'),\n]")

with open('escalas/urls.py', 'w', encoding='utf-8') as f:
    f.write(escalas_urls)

# 3. Update escalas/templates/escalas/painel.html
with open('escalas/templates/escalas/painel.html', 'r', encoding='utf-8') as f:
    painel_html = f.read()

ocr_html = '''
            <!-- Importar via OCR -->
            <div class="bg-gray-900/80 backdrop-blur-xl p-6 rounded-3xl shadow-[0_0_30px_rgba(0,0,0,0.3)] border border-gray-700/50 h-fit relative overflow-hidden mt-6">
                <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-purple-600 to-pink-500"></div>
                
                <h3 class="text-xl font-bold mb-4 text-white flex items-center gap-2">
                    <i data-lucide="scan-text" class="w-5 h-5 text-purple-400"></i>
                    IA OCR Escalas
                </h3>
                
                <form method="POST" action="{% url 'importar_escala_ocr' %}" enctype="multipart/form-data" class="space-y-4">
                    {% csrf_token %}
                    <div>
                        <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Arquivo PDF, CSV ou Excel</label>
                        <input type="file" name="arquivo_escala" accept=".pdf,.xlsx,.xls,.csv" required class="w-full px-4 py-2 border border-gray-700/80 rounded-xl focus:ring-2 focus:ring-purple-500 outline-none bg-gray-950/60 text-gray-300">
                    </div>
                    <button type="submit" class="w-full py-3 mt-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(168,85,247,0.4)] flex items-center justify-center gap-2">
                        ✨ PROCESSAR COM GROQ
                    </button>
                </form>
            </div>
'''

painel_html = painel_html.replace('<!-- Listagem de Competências -->', f'{ocr_html}\n            <!-- Listagem de Competências -->')

with open('escalas/templates/escalas/painel.html', 'w', encoding='utf-8') as f:
    f.write(painel_html)
