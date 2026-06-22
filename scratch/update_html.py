with open('almoxarifado/templates/almoxarifado/inventario.html', 'r', encoding='utf-8') as f:
    content = f.read()

btn_ai = '''<button hx-get="{% url 'ai_insights_almoxarifado' %}" hx-target="#ai-insights-container" hx-swap="innerHTML" class="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-lg font-bold shadow-lg shadow-blue-500/30 transition-all flex items-center gap-2" onclick="document.getElementById('ai-insights-container').innerHTML='<div class=\\'text-blue-300 font-medium p-4\\'>✨ A LPU da Groq está analisando o estoque...</div>'">
                    ✨ Groq Insights
                </button>'''

content = content.replace(
    '<button @click="openNovoAtivo = true" class="px-4 py-2 bg-brand-600',
    f"{btn_ai}\n                <button @click=\"openNovoAtivo = true\" class=\"px-4 py-2 bg-brand-600"
)

div_ai = '''        <!-- AI INSIGHTS CONTAINER -->
        <div id="ai-insights-container" class="mb-8"></div>
        
        <!-- DASHBOARD CARDS -->'''

content = content.replace('<!-- DASHBOARD CARDS -->', div_ai)

with open('almoxarifado/templates/almoxarifado/inventario.html', 'w', encoding='utf-8') as f:
    f.write(content)
