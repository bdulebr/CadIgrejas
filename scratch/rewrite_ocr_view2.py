view_code = '''
@login_required
def importar_escala_ocr(request):
    if request.method == 'POST':
        arquivo = request.FILES.get('arquivo_escala')
        if not arquivo:
            messages.error(request, 'Você deve selecionar um arquivo PDF, Excel ou CSV.')
            return redirect('painel_escalas')
            
        try:
            from intranet.services.groq_ai import analisar_planilha_escalas_groq
            dados = analisar_planilha_escalas_groq(arquivo)
            
            if not dados or not isinstance(dados, dict) or 'escalas' not in dados:
                messages.warning(request, 'O Groq não conseguiu extrair os dados no formato esperado.')
                return redirect('painel_escalas')
            
            dept_nome = dados.get('departamento', '')
            mes = str(dados.get('mes', '')).strip().lower()
            ano = str(dados.get('ano', '')).strip()
            
            # Map month name to number
            mes_map = {'janeiro': '01', 'fevereiro': '02', 'março': '03', 'marco': '03', 
                       'abril': '04', 'maio': '05', 'junho': '06', 'julho': '07',
                       'agosto': '08', 'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'}
                       
            mes_num = mes_map.get(mes, mes.zfill(2))
            if not ano:
                from django.utils import timezone
                ano = str(timezone.now().year)
                
            mes_ano_str = f"{mes_num}/{ano}"
            
            # Find department
            from gestao_membros.models import Departamento
            departamento = Departamento.objects.filter(nome__icontains=dept_nome).first()
            if not departamento:
                # Tentar achar algum que ocupe pelo menos metade das palavras
                departamentos_all = Departamento.objects.all()
                from thefuzz import process
                nomes_deptos = {d.id: d.nome for d in departamentos_all}
                best_match = process.extractOne(dept_nome, nomes_deptos)
                if best_match and best_match[1] >= 65:
                    departamento = Departamento.objects.get(id=best_match[2])
                else:
                    messages.error(request, f'Departamento "{dept_nome}" não encontrado no sistema. Crie o departamento primeiro.')
                    return redirect('painel_escalas')
                    
            from .models import CompetenciaEscala, Escala
            
            competencia, created = CompetenciaEscala.objects.get_or_create(
                departamento=departamento,
                mes_ano=mes_ano_str,
                defaults={'status': 'rascunho'}
            )
            
            # Fuzzy match setup for Members
            from core.models import Membro
            membros_dept = Membro.objects.filter(is_active=True)
            # Para aumentar a precisão, priorizamos membros do sistema, mas permitimos busca geral
            membros_dict = {m.id: f"{m.first_name} {m.last_name}" for m in membros_dept}
            
            escalas_lidas = dados.get('escalas', [])
            count_sucesso = 0
            count_fallback = 0
            
            from datetime import datetime
            from thefuzz import process
            
            for esc in escalas_lidas:
                data_str = esc.get('dia', '')
                try:
                    # try to parse DD/MM/YYYY
                    data_obj = datetime.strptime(data_str, '%d/%m/%Y').date()
                except:
                    continue
                    
                turno = esc.get('turno', '').lower()
                horario_inicio = "19:30" if turno == "noite" else "09:00"
                horario_fim = "21:30" if turno == "noite" else "11:30"
                
                nomes = esc.get('membros_nomes', [])
                if isinstance(nomes, str):
                    nomes = [nomes]
                    
                for nome in nomes:
                    nome = nome.strip()
                    if not nome: continue
                    
                    # Limpar títulos comuns
                    nome_limpo = nome.lower().replace('miss ', '').replace('miss. ', '').replace('pr ', '').replace('pr. ', '').replace('ev ', '').strip()
                    
                    # Fuzzy match
                    membro_escalado = None
                    best_match_id = None
                    
                    if len(nome_limpo) > 2:
                        match = process.extractOne(nome_limpo, membros_dict)
                        if match and match[1] >= 75: # Tolerância alta (ex: Kauãzinho vs Kauã)
                            best_match_id = match[2]
                            membro_escalado = Membro.objects.get(id=best_match_id)
                    
                    if membro_escalado:
                        try:
                            Escala.objects.create(
                                competencia=competencia,
                                membro_escalado=membro_escalado,
                                departamento_alocado=departamento,
                                data_escala=data_obj,
                                horario_inicio=horario_inicio,
                                horario_fim=horario_fim,
                                tipo_evento=esc.get('observacao', '') or esc.get('funcao', '')
                            )
                            count_sucesso += 1
                        except:
                            # Ignora erro de constraint única no BD
                            pass
                    else:
                        count_fallback += 1
                        # Adicionar slot fantasma (se possivel) ou apenas ignorar
                        # Como Escala exige membro_escalado, vamos apenas ignorar e incrementar contador
                        
            msg = f"Escalas extraídas para {departamento.nome} ({mes_ano_str}). Inseridas: {count_sucesso}."
            if count_fallback > 0:
                msg += f" {count_fallback} nomes não foram reconhecidos com precisão (Fuzzy Matching)."
                messages.warning(request, msg)
            else:
                messages.success(request, msg)
                
        except Exception as e:
            messages.error(request, f'Erro no processamento OCR (Groq): {str(e)}')
            
    return redirect('painel_escalas')
'''

with open('escalas/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = lines[:795]

with open('escalas/views.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
    f.write('\\n')
    f.write(view_code)
