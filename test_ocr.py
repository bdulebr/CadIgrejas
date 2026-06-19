import os
import django
import sys
import json
from dotenv import load_dotenv

# Configurar Django para script standalone
project_root = r'C:\Users\MarcosLira\Desktop\Marcos\Projeto'
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
load_dotenv(os.path.join(project_root, '.env'))
django.setup()

from intranet.services.gemini_ai import analisar_escala_gemini
from gestao_membros.models import Departamento
from core.models import Membro
from django.core.files.uploadedfile import SimpleUploadedFile

def test_ocr():
    from escalas.models import CompetenciaEscala, Escala
    import json
    import re
    from datetime import datetime

    dept_list = [{'id': d.id, 'nome': d.nome} for d in Departamento.objects.all()]
    membros_list = [{'id': m.id, 'nome': f"{m.first_name} {m.last_name} ({m.apelido or ''})".strip()} for m in Membro.objects.filter(is_active=True)]

    dept = Departamento.objects.get(id=18)
    comp, _ = CompetenciaEscala.objects.get_or_create(departamento=dept, mes_ano="06/2026", defaults={'status':'rascunho'})

    with open("C:\\Users\\MarcosLira\\Desktop\\Marcos\\Projeto\\docs\\TREINO IA\\Live.pdf", 'rb') as f:
        file_obj = SimpleUploadedFile("Live.pdf", f.read(), content_type="application/pdf")

    dados = analisar_escala_gemini(file_obj, dept_list, membros_list)
    escalas_lidas = dados.get('escalas', [])
    print(f"Lidas {len(escalas_lidas)} escalas do Gemini.")

    mes_ano_input = "06/2026"
    for esc in escalas_lidas:
        data_str_raw = esc.get('dia', '')
        match = re.search(r'(\d{2}/\d{2})', data_str_raw)
        if not match:
            print(f"Match failed for {data_str_raw}")
            continue

        dia_mes = match.group(1)
        ano_escala = mes_ano_input.split('/')[1]
        data_str_forced = f"{dia_mes}/{ano_escala}"
        try:
            data_obj = datetime.strptime(data_str_forced, '%d/%m/%Y').date()
        except ValueError:
            print(f"ValueError parsing {data_str_forced}")
            continue

        turno = esc.get('turno', '').lower()
        horario_inicio = "19:30" if turno == "noite" else "09:00"
        horario_fim = "21:30" if turno == "noite" else "11:30"

        membros_ids = esc.get('membros_ids', [])
        if not isinstance(membros_ids, list):
            membros_ids = [membros_ids]

        for m_id in membros_ids:
            try:
                m_id = int(m_id)
                membro_escalado = Membro.objects.get(id=m_id)
                Escala.objects.create(
                    competencia=comp,
                    membro_escalado=membro_escalado,
                    departamento_alocado=dept,
                    funcao_alocada=None,
                    data_escala=data_obj,
                    horario_inicio=horario_inicio,
                    horario_fim=horario_fim,
                    tipo_evento=esc.get('funcao', '')
                )
                print(f"Inserido {membro_escalado.first_name} em {data_obj} {horario_inicio}")
            except Exception as e:
                print(f"Erro ao inserir {m_id} em {data_obj}: {type(e).__name__} - {str(e)}")

test_ocr()
