import os
import re

def rewrite_offline_fallback():
    filepath = 'C:/Users/MarcosLira/Desktop/Marcos/Projeto/escalas/views.py'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # The block we want to rewrite starts after the 'for m in membros_funcao:' loop starts, line 708
    pattern = r'(membros_disponiveis = \[\]\s*for m in membros_funcao:.*?if membros_disponiveis:\s*escolhido = random\.choice\(membros_disponiveis\).*?status=\'rascunho\'\s*\)\s*slots_criados \+= 1)'

    replacement = '''membros_disponiveis = []
                        for m in membros_funcao:
                            is_indisponivel = Indisponibilidade.objects.filter(
                                membro=m, data_inicio__lte=data_atual, data_fim__gte=data_atual
                            ).exists()

                            count_mes = Escala.objects.filter(
                                membro_escalado=m,
                                data_escala__year=ano,
                                data_escala__month=mes
                            ).count()

                            # Trava Global de Dia Único: Previne burnout impedindo 2 cultos no MESMO DIA, em qualquer departamento
                            ja_escalado_hoje = Escala.objects.filter(
                                membro_escalado=m,
                                data_escala=data_atual
                            ).exists()

                            is_trabalho = is_trabalhando(m, data_atual, start_time, end_time)

                            import datetime
                            ja_escalado_recentemente = Escala.objects.filter(
                                membro_escalado=m,
                                data_escala__gte=data_atual - datetime.timedelta(days=6),
                                data_escala__lt=data_atual
                            ).exists()

                            if not is_indisponivel and count_mes < 4 and not ja_escalado_hoje and not is_trabalho:
                                if not ja_escalado_recentemente:
                                    membros_disponiveis.append((count_mes, m))

                        # If strict cooldown leaves no one available, relax the cooldown
                        if not membros_disponiveis:
                            for m in membros_funcao:
                                is_indisponivel = Indisponibilidade.objects.filter(
                                    membro=m, data_inicio__lte=data_atual, data_fim__gte=data_atual
                                ).exists()
                                count_mes = Escala.objects.filter(
                                    membro_escalado=m, data_escala__year=ano, data_escala__month=mes
                                ).count()
                                ja_escalado_hoje = Escala.objects.filter(
                                    membro_escalado=m, data_escala=data_atual
                                ).exists()
                                is_trabalho = is_trabalhando(m, data_atual, start_time, end_time)

                                if not is_indisponivel and count_mes < 4 and not ja_escalado_hoje and not is_trabalho:
                                    membros_disponiveis.append((count_mes, m))

                        if membros_disponiveis:
                            # Distribuição Matemática: Ordena por quem tem MENOS escalas no mês
                            membros_disponiveis.sort(key=lambda x: x[0])
                            
                            # Filtra apenas os que têm o número mínimo de escalas (em caso de empate)
                            min_count = membros_disponiveis[0][0]
                            empatados = [item[1] for item in membros_disponiveis if item[0] == min_count]
                            
                            # Escolhe aleatoriamente entre os que estão empatados com o menor número de escalas
                            escolhido = random.choice(empatados)

                            Escala.objects.create(
                                competencia=comp,
                                membro_escalado=escolhido,
                                departamento_alocado=comp.departamento,
                                funcao_alocada=config.funcao,
                                data_escala=data_atual,
                                horario_inicio=start_time,
                                horario_fim=end_time,
                                tipo_evento=evento,
                                status='rascunho'
                            )
                            slots_criados += 1'''

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

rewrite_offline_fallback()
print("Refactored offline fallback to use mathematical distribution.")
