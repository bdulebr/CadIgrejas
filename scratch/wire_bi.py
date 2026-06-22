import os

# 1. Update core/views.py
views_bi_code = '''
@login_required
def ai_insights_bi(request):
    try:
        from intranet.services.groq_ai import obter_client_groq
        client = obter_client_groq()
        if not client:
            return HttpResponse('<div class="p-4 bg-red-900/50 text-red-200 rounded-lg">Erro: Chave do Groq não configurada.</div>')
            
        # Coletar estatísticas globais
        from core.models import Membro
        from gestao_membros.models import Departamento
        from escalas.models import CompetenciaEscala
        from almoxarifado.models import Ativo, Emprestimo
        from django.utils import timezone
        
        hoje = timezone.now().date()
        total_membros = Membro.objects.filter(is_active=True).count()
        membros_inativos = Membro.objects.filter(is_active=False).count()
        total_deptos = Departamento.objects.count()
        escalas_ativas = CompetenciaEscala.objects.filter(status='publicada').count()
        ativos = Ativo.objects.count()
        
        import json
        context_data = {
            'membros_ativos': total_membros,
            'membros_inativos': membros_inativos,
            'total_departamentos': total_deptos,
            'escalas_publicadas': escalas_ativas,
            'itens_patrimonio': ativos
        }
        
        prompt = f"""
        Você é um Diretor de Inteligência de Negócios (BI) e Estratégia de uma Igreja.
        Analise o resumo de dados operacionais abaixo e retorne um pequeno relatório de insights em HTML (sem usar tags Markdown como ```html).
        Use classes TailwindCSS (text-blue-400, font-bold, bg-gray-800, p-4, rounded-lg) para formatar a resposta. 
        Dê 3 insights valiosos de gestão para o pastor/diretoria baseados nestes números:
        
        {json.dumps(context_data)}
        """
        
        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.7
        )
        
        html_response = response.choices[0].message.content.replace('```html', '').replace('```', '')
        return HttpResponse(html_response)
        
    except Exception as e:
        return HttpResponse(f'<div class="p-4 bg-red-900/50 text-red-200 rounded-lg">Erro ao conectar com a LPU Groq: {str(e)}</div>')
'''

with open('core/views.py', 'a', encoding='utf-8') as f:
    f.write(views_bi_code)

# 2. Update core/urls.py
with open('core/urls.py', 'r', encoding='utf-8') as f:
    core_urls = f.read()

core_urls = core_urls.replace(']', "    path('bi/ai-insights/', views.ai_insights_bi, name='ai_insights_bi'),\n]")

with open('core/urls.py', 'w', encoding='utf-8') as f:
    f.write(core_urls)

# 3. Update core/templates/core/pages/bi_dashboard.html
with open('core/templates/core/pages/bi_dashboard.html', 'r', encoding='utf-8') as f:
    bi_html = f.read()

btn_ai = '''
        <!-- AI INSIGHTS -->
        <div class="mb-8">
            <div id="ai-insights-container">
                <button hx-get="{% url 'ai_insights_bi' %}" hx-target="#ai-insights-container" hx-swap="innerHTML" class="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl font-bold shadow-lg shadow-indigo-500/30 transition-all flex items-center gap-2" onclick="this.innerHTML='✨ O Groq está gerando a análise...' ">
                    <i data-lucide="brain-circuit" class="w-5 h-5"></i>
                    Gerar Inteligência Estratégica com IA
                </button>
            </div>
        </div>
'''

if "ai-insights-container" not in bi_html:
    bi_html = bi_html.replace('<div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">', f'{btn_ai}\n        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">')
    with open('core/templates/core/pages/bi_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(bi_html)
