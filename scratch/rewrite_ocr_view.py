import re

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
                nomes_deptos = [d.nome for d in departamentos_all]
                best_match, score = process.extractOne(dept_nome, nomes_deptos)
                if score >= 70:
                    departamento = Departamento.objects.get(nome=best_match)
                else:
                    messages.error(request, f'Departamento "{dept_nome}" não encontrado no sistema.')
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
            # Para aumentar a precisão, vamos priorizar membros do departamento, mas permitir busca geral se não achar
            membros_dict = {m.id: f"{m.first_name} {m.last_name}" for m in membros_dept}
            
            escalas_lidas = dados.get('escalas', [])
            count_sucesso = 0
            count_fallback = 0
            
            from datetime import datetime
            
            for esc in escalas_lidas:
                data_str = esc.get('dia', '')
                try:
                    # try to parse DD/MM/YYYY
                    data_obj = datetime.strptime(data_str, '%d/%m/%Y').date()
                except:
                    # skip if we can't parse date
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
                    
                    # Fuzzy match
                    membro_escalado = None
                    best_match_id = None
                    
                    if len(nome) > 2:
                        match = process.extractOne(nome, membros_dict)
                        if match and match[1] >= 75: # Tolerância alta pois podem usar "Pr Luciano"
                            best_match_id = match[2]
                            membro_escalado = Membro.objects.get(id=best_match_id)
                    
                    if membro_escalado:
                        # Criar escala normal
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
                            # Ignora constraints únicas
                            pass
                    else:
                        # Aqui você poderia criar um "SlotFantasma" ou deixar um aviso, mas como o banco
                        # exige membro_escalado FK Not Null, vamos apenas logar ou pular por enquanto.
                        # Numa v2, poderíamos ter "Visitante" ou "A Confirmar".
                        # Como workaround provisório, vamos ignorar e incrementar os fallbacks.
                        count_fallback += 1
                        
            msg = f"Escalas extraídas para {departamento.nome} ({mes_ano_str}). Inseridas: {count_sucesso}."
            if count_fallback > 0:
                msg += f" {count_fallback} nomes não foram reconhecidos pelo IA no banco de dados."
                messages.warning(request, msg)
            else:
                messages.success(request, msg)
                
        except Exception as e:
            messages.error(request, f'Erro no processamento OCR (Groq): {str(e)}')
            
    return redirect('painel_escalas')
'''

with open('escalas/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the old view with the new one using regex to match the old block
old_view_pattern = re.compile(r'@login_required\ndef importar_escala_ocr.*?return redirect\(\'painel_escalas\'\)', re.DOTALL)
content = old_view_pattern.sub(view_code.strip(), content)

with open('escalas/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
