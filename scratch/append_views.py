import sys

code = '''
@login_required
@user_passes_test(can_edit_almoxarifado)
def ai_insights_almoxarifado(request):
    try:
        from intranet.services.groq_ai import obter_client_groq
        client = obter_client_groq()
        if not client:
            return HttpResponse('<div class="p-4 bg-red-900/50 text-red-200 rounded-lg">Erro: Chave do Groq não configurada.</div>')
            
        # Coletar estatísticas do almoxarifado
        from .models import Ativo, Emprestimo, AlimentoLote
        from django.db.models import Sum
        from django.utils import timezone
        
        total_ativos = Ativo.objects.count()
        valor_total = Ativo.objects.aggregate(total=Sum('valor'))['total'] or 0
        ativos_quebrados = Ativo.objects.filter(status='quebrado').count()
        ativos_manutencao = Ativo.objects.filter(status='manutencao').count()
        
        hoje = timezone.now().date()
        emprestimos_atrasados = Emprestimo.objects.filter(data_devolucao_prevista__lt=hoje, data_devolucao_real__isnull=True).count()
        alimentos_vencidos = AlimentoLote.objects.filter(data_vencimento__lt=hoje).exclude(status__in=['Vencido', 'Consumido']).count()
        alimentos_vencendo_breve = AlimentoLote.objects.filter(data_vencimento__gte=hoje, data_vencimento__lte=hoje + timezone.timedelta(days=15)).count()
        
        import json
        context_data = {
            'total_ativos_cadastrados': total_ativos,
            'valor_total_estimado': float(valor_total),
            'itens_quebrados': ativos_quebrados,
            'itens_em_manutencao': ativos_manutencao,
            'emprestimos_atrasados': emprestimos_atrasados,
            'lotes_alimentos_vencidos': alimentos_vencidos,
            'lotes_alimentos_vencendo_15_dias': alimentos_vencendo_breve
        }
        
        prompt = f"""
        Você é um Consultor Sênior de Logística e Almoxarifado da Igreja. 
        Analise o resumo do estoque abaixo e retorne um pequeno relatório de insights em HTML (sem usar tags de Markdown como ```html).
        Use classes do TailwindCSS (como text-blue-400, font-bold, mb-2, p-4, bg-gray-800, rounded-lg) para formatar a resposta. 
        Dê 3 dicas acionáveis para o líder do almoxarifado com base nestes números:
        
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

with open('almoxarifado/views.py', 'a', encoding='utf-8') as f:
    f.write(code)
