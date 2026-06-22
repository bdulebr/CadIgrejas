import os
import re

def refactor_escalas_engine():
    filepath = 'C:/Users/MarcosLira/Desktop/Marcos/Projeto/escalas/views.py'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # We need to replace the logic inside gerar_escala_automatica from line 570 up to 618.
    
    # Locate the try block for Groq in the old code.
    pattern = r'(try:\s*from intranet\.services\.groq_ai import gerar_escala_inteligente_groq.*?)return redirect\(\'editor_escala_manual\', comp_id=comp\.id\)'
    
    replacement = '''try:
            from intranet.services.gemini_ai import gerar_escala_inteligente_gemini
            from intranet.services.groq_ai import gerar_escala_inteligente_groq

            regras = {'limite_mensal': 4}
            resultado = None
            motor_usado = ""

            try:
                resultado = gerar_escala_inteligente_gemini(
                    departamento_nome=comp.departamento.nome,
                    mes=mes,
                    ano=ano,
                    membros=membros_data,
                    eventos=eventos_data,
                    regras=regras
                )
                motor_usado = "Gemini 2.5 Flash"
            except Exception as e_gemini:
                import logging
                logging.getLogger(__name__).warning(f"Erro no Motor Gemini: {e_gemini}. Acionando Fallback Groq...")
                resultado = gerar_escala_inteligente_groq(
                    departamento_nome=comp.departamento.nome,
                    mes=mes,
                    ano=ano,
                    membros=membros_data,
                    eventos=eventos_data,
                    regras=regras
                )
                motor_usado = "LPU Groq"

            alocacoes = resultado.get('alocacoes', [])
            slots_criados = 0

            for aloc in alocacoes:
                try:
                    membro_id = int(aloc.get('membro_id'))
                    data_obj = date.fromisoformat(aloc.get('data'))
                    funcao_obj = Funcao.objects.get(id=int(aloc.get('funcao_id')))
                    membro_obj = Membro.objects.get(id=membro_id)

                    # Trava Anti-Hallucination: Se a IA errar e tentar escalar duas vezes no mesmo dia
                    if Escala.objects.filter(membro_escalado=membro_obj, data_escala=data_obj).exists():
                        continue

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
                    import logging
                    logging.getLogger(__name__).warning(f"Erro ao salvar alocacao da IA: {e}")

            messages.success(request, f'✨ Motor IA ({motor_usado}) finalizado! {slots_criados} voluntários alocados.')

        except Exception as e:
            messages.warning(request, f'Motores de IA falharam ({str(e)}). Acionando Motor Offline de emergência...')
            return gerar_escala_automatica_fallback(request)

        return redirect('editor_escala_manual', comp_id=comp.id)'''

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

refactor_escalas_engine()
print("Refactored AI engine logic in escalas/views.py")
