import os

view_code = '''
@login_required
@user_passes_test(is_lider)
def gerar_escala_automatica(request):
    if request.method == 'POST':
        comp_id = request.POST.get('comp_id')
        comp = get_object_or_404(CompetenciaEscala, id=comp_id)
        deps_permitidos = get_departamentos_permitidos(request.user)
        if comp.departamento not in deps_permitidos:
            messages.error(request, 'Sem permissão.')
            return redirect('painel_escalas')
            
        from gestao_membros.models import ConfiguracaoSlotEscala
        from django.db.models import Q
        import calendar
        from datetime import date
        
        configuracoes = ConfiguracaoSlotEscala.objects.filter(departamento=comp.departamento)
        if not configuracoes.exists():
            messages.error(request, 'O Motor falhou: Este departamento não possui nenhuma Configuração de Slot definida.')
            return redirect('editor_escala_manual', comp_id=comp.id)
            
        mes, ano = map(int, comp.mes_ano.split('/'))
        num_days = calendar.monthrange(ano, mes)[1]
        
        from core.models import Membro
        from escalas.models import CultoEvento, Escala, Indisponibilidade
        from gestao_membros.models import Funcao
        
        membros_elegiveis = Membro.objects.filter(
            Q(is_active=True) & 
            (Q(departamentos_ativos=comp.departamento) | Q(departamentos_liderados=comp.departamento) | Q(departamentos_subliderados=comp.departamento))
        ).distinct()
        
        # 1. Coletar dados para o Groq
        membros_data = []
        for m in membros_elegiveis:
            indisp = Indisponibilidade.objects.filter(membro=m, data_inicio__year=ano, data_inicio__month=mes)
            datas_indisp = []
            for i in indisp:
                delta = (i.data_fim - i.data_inicio).days
                for d in range(delta + 1):
                    datas_indisp.append((i.data_inicio.replace(day=i.data_inicio.day + d)).strftime('%Y-%m-%d'))
                    
            membros_data.append({
                'id': m.id,
                'nome': f"{m.first_name} {m.last_name}",
                'habilidades_ids': list(m.habilidades.values_list('id', flat=True)),
                'datas_indisponiveis': datas_indisp
            })
            
        eventos_data = []
        for day in range(1, num_days + 1):
            data_atual = date(ano, mes, day)
            dia_semana = data_atual.weekday()
            
            recorrentes = CultoEvento.objects.filter(tipo='padrao', dia_semana=dia_semana)
            extras = CultoEvento.objects.filter(tipo='extra', data_evento=data_atual)
            
            for ev in list(recorrentes) + list(extras):
                key_ev = ev.chave_slug if ev.chave_slug else str(ev.id)
                configs = configuracoes.filter(tipo_evento=key_ev)
                for config in configs:
                    for _ in range(config.quantidade):
                        eventos_data.append({
                            'evento_id': key_ev,
                            'data': data_atual.strftime('%Y-%m-%d'),
                            'horario_inicio': ev.horario_inicio.strftime('%H:%M'),
                            'horario_fim': ev.horario_fim.strftime('%H:%M'),
                            'funcao_id': config.funcao.id,
                            'funcao_nome': config.funcao.nome,
                            'requisitos_habilidades': list(config.funcao.requisitos.values_list('id', flat=True))
                        })
                        
        if not eventos_data:
            messages.warning(request, 'Não há eventos neste mês para serem escalados com as configurações atuais.')
            return redirect('editor_escala_manual', comp_id=comp.id)

        try:
            from intranet.services.groq_ai import gerar_escala_inteligente_groq
            
            regras = {'limite_mensal': 4}
            resultado = gerar_escala_inteligente_groq(
                departamento_nome=comp.departamento.nome,
                mes=mes,
                ano=ano,
                membros=membros_data,
                eventos=eventos_data,
                regras=regras
            )
            
            alocacoes = resultado.get('alocacoes', [])
            slots_criados = 0
            
            for aloc in alocacoes:
                try:
                    membro_id = int(aloc.get('membro_id'))
                    data_obj = date.fromisoformat(aloc.get('data'))
                    funcao_obj = Funcao.objects.get(id=int(aloc.get('funcao_id')))
                    membro_obj = Membro.objects.get(id=membro_id)
                    
                    Escala.objects.create(
                        competencia=comp,
                        membro_escalado=membro_obj,
                        departamento_alocado=comp.departamento,
                        funcao_alocada=funcao_obj,
                        data_escala=data_obj,
                        horario_inicio=aloc.get('horario_inicio', '19:30'),
                        horario_fim=aloc.get('horario_fim', '21:30'),
                        tipo_evento=aloc.get('evento_id'),
                        status='confirmado'
                    )
                    slots_criados += 1
                except Exception as e:
                    pass
                    
            messages.success(request, f'✨ Motor LPU Groq finalizado! A IA analisou as restrições e alocou {slots_criados} voluntários com precisão matemática.')
            
        except Exception as e:
            messages.error(request, f'Erro no processamento da Inteligência Artificial (Groq): {str(e)}')
            
        return redirect('editor_escala_manual', comp_id=comp.id)
    return redirect('painel_escalas')
'''

with open('escalas/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_func = False
for i, line in enumerate(lines):
    if line.strip() == '@login_required' and i+1 < len(lines) and '@user_passes_test(is_lider)' in lines[i+1] and 'def gerar_escala_automatica' in lines[i+2]:
        in_func = True
        new_lines.append("###GROQ_AUTO_SCHEDULER_MARKER###\\n")
        continue
        
    if in_func:
        # Stop skipping when we hit the next function definition (but ignore internal definitions, so check for root decorators or defs)
        if line.startswith('@') or line.startswith('def '):
            if not line.startswith('@login_required') and not line.startswith('def '):
                continue
            # We found the next function
            in_func = False
        else:
            continue
            
    if not in_func:
        new_lines.append(line)

content = "".join(new_lines)
content = content.replace("###GROQ_AUTO_SCHEDULER_MARKER###\\n", view_code)

# Let's clean up any possible double injection leftovers from previous failures
# Just to be safe, if we find the exact string `from gestao_membros.models import ConfiguracaoSlotEscala\n        from django.db.models import Q\n        import random\n        import calendar` we can delete it.

with open('escalas/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
