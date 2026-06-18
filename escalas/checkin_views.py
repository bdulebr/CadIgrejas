"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: escalas/checkin_views.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 18/06/2026 13:20
* LOG DE ALTERAÇÕES:
* - 18/06/2026 13:20: Auditoria e padronização global (Goal)
"""
import json
import math
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from core.models import Membro
from escalas.models import Escala
from gestao_membros.models import AcaoDisciplinar, Indisponibilidade

# Coordenadas da Igreja (Av. Abílio dos Santos Branco, 585)
IGREJA_LAT = -23.98354
IGREJA_LNG = -46.23635
RAIO_PERMITIDO_METROS = 100  # Raio de 100 metros de tolerância para o GPS

def calcular_distancia_haversine(lat1, lon1, lat2, lon2):
    R = 6371000 # Raio da terra em metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def apenas_numeros(texto):
    if not texto: return ""
    return ''.join(filter(str.isdigit, texto))

def checkin_page(request):
    """
    Renderiza a interface mobile para o Check-in via QR Code.
    """
    return render(request, 'escalas/app/checkin.html')

@csrf_exempt
def api_processar_checkin(request):
    """
    API do Motor Zero-Trust que recebe os dados do celular e processa a presença.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método não permitido.'}, status=405)

    try:
        data = json.loads(request.body)
        digitos_telefone = apenas_numeros(data.get('digitos_telefone', ''))
        digitos_doc = apenas_numeros(data.get('digitos_documento', ''))
        lat = data.get('lat')
        lng = data.get('lng')

        if not lat or not lng:
            return JsonResponse({'status': 'error', 'message': 'GPS Inativo. Você precisa permitir a localização para bater o ponto.'})

        # 1. Validação do GPS
        distancia = calcular_distancia_haversine(float(lat), float(lng), IGREJA_LAT, IGREJA_LNG)
        if distancia > RAIO_PERMITIDO_METROS:
            return JsonResponse({
                'status': 'error',
                'message': f'Você está muito longe da Igreja ({int(distancia)}m). O check-in só é permitido num raio de {RAIO_PERMITIDO_METROS}m.'
            })

        if not digitos_telefone or len(digitos_telefone) != 4:
            return JsonResponse({'status': 'error', 'message': 'Informe exatamente os 4 últimos dígitos do celular.'})

        # 2. Busca Fuzzy (Aproximação por dígitos finais)
        todos_membros = Membro.objects.filter(is_active=True)
        candidatos = []
        for m in todos_membros:
            tel_limpo = apenas_numeros(m.telefone)
            if tel_limpo.endswith(digitos_telefone):
                candidatos.append(m)

        if not candidatos:
            return JsonResponse({'status': 'error', 'message': 'Nenhum membro encontrado com este final de telefone.'})

        membro_alvo = None

        if len(candidatos) > 1:
            # Colisão detectada
            if not digitos_doc:
                return JsonResponse({'status': 'collision', 'message': 'Mais de uma pessoa com o mesmo final de telefone! Precisamos do CPF/RG para desempatar.'})

            # Desempate pelo documento
            for m in candidatos:
                cpf_limpo = apenas_numeros(m.cpf)
                rg_limpo = apenas_numeros(m.rg)
                if cpf_limpo.endswith(digitos_doc) or rg_limpo.endswith(digitos_doc):
                    membro_alvo = m
                    break

            if not membro_alvo:
                return JsonResponse({'status': 'error', 'message': 'Desempate falhou. Documento não corresponde.'})
        else:
            membro_alvo = candidatos[0]

        # 3. Motor Zero-Trust de RH
        hoje = timezone.now().date()

        # A. Checar Suspensões
        suspensao_ativa = AcaoDisciplinar.objects.filter(
            membro=membro_alvo,
            tipo__in=['suspensao', 'expulsao'],
            data_fim_suspensao__gte=hoje
        ).first()

        if suspensao_ativa:
            return JsonResponse({'status': 'rh_blocked', 'message': 'Acesso Bloqueado pelo RH: Ação Disciplinar Vigente.'})

        # B. Checar Indisponibilidade Registrada
        indisponibilidade_ativa = Indisponibilidade.objects.filter(
            membro=membro_alvo,
            data_inicio__lte=hoje,
            data_fim__gte=hoje
        ).first()

        if indisponibilidade_ativa:
            return JsonResponse({'status': 'rh_blocked', 'message': f'Acesso Bloqueado: Você tem uma ausência aprovada para hoje ({indisponibilidade_ativa.motivo}).'})

        # C. Checar a Escala (Ele tem mesmo escala pra hoje?)
        escalas_hoje = Escala.objects.filter(membro_escalado=membro_alvo, data_escala=hoje)
        if not escalas_hoje.exists():
            return JsonResponse({'status': 'error', 'message': f'Nenhuma escala encontrada para {membro_alvo.get_full_name()} no dia de hoje.'})

        # D. Confirmar o Check-in e Disparar Notificação/Email
        escala_alvo = escalas_hoje.first()
        if escala_alvo.checkin_realizado:
             return JsonResponse({'status': 'error', 'message': 'Você já realizou o check-in hoje!'})

        escala_alvo.checkin_realizado = True
        escala_alvo.data_hora_checkin = timezone.now()
        escala_alvo.status = 'presente'
        escala_alvo.save()

        # Disparar Email
        from core.models import EmailLog
        import threading

        def enviar_email_presenca(email, nome, data_str, horario_str, dept):
            try:
                assunto = f"Confirmação de Presença ({dept})"
                mensagem = f"Olá {nome},\n\nSeu check-in foi registrado com sucesso em {data_str} às {horario_str}.\nObrigado por servir no departamento de {dept}!\n\nLiderança PV Enseada."

                # Mock de envio de email. O sistema idealmente tem um core.utils.send_system_email.
                # Aqui vamos registrar direto no Log para o Sysadmin ver.
                EmailLog.objects.create(
                    destinatario=email,
                    assunto=assunto,
                    status='enviado',
                    erro_mensagem=mensagem
                )
            except Exception as e:
                print(f"Erro ao enviar email de checkin: {e}")

        if membro_alvo.email:
            threading.Thread(target=enviar_email_presenca, args=(
                membro_alvo.email,
                membro_alvo.get_full_name(),
                escala_alvo.data_escala.strftime("%d/%m/%Y"),
                escala_alvo.data_hora_checkin.strftime("%H:%M"),
                escala_alvo.departamento_alocado.nome
            )).start()

        return JsonResponse({
            'status': 'success',
            'message': f'Check-in confirmado para {membro_alvo.get_full_name()}!'
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Erro interno: {str(e)}'})

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import qrcode
from io import BytesIO

@login_required
def baixar_qrcode_checkin(request):
    """
    SysAdmin/Líder baixa o QR Code oficial para imprimir.
    """
    if request.user.nivel_hierarquico not in ['super_admin', 'pastor_regente', 'pastor', 'lider']:
        return HttpResponse("Acesso Negado", status=403)

    # URL pública do check-in
    url_base = request.build_absolute_uri('/escalas/checkin/')

    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(url_base)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1E3A8A", back_color="white") # Azul Escuro

    buffer = BytesIO()
    img.save(buffer, format="PNG")

    response = HttpResponse(buffer.getvalue(), content_type="image/png")
    response['Content-Disposition'] = 'attachment; filename="qrcode_ponto_intranet.png"'
    return response

@login_required
def checkin_manual_lider(request, escala_id):
    """
    O Líder do departamento pode forçar um check-in manual para quem esqueceu.
    """
    if request.method == 'POST':
        from django.shortcuts import get_object_or_404, redirect
        from django.contrib import messages
        from core.models import LogAuditoria

        escala = get_object_or_404(Escala, id=escala_id)

        # Valida se o usuário logado é líder do departamento desta escala
        from escalas.app_views import is_lider_any_dept
        if not is_lider_any_dept(request.user):
            messages.error(request, "Acesso Negado.")
            return redirect('checkins_hoje_desktop')

        is_owner = False
        if request.user.nivel_hierarquico in ['super_admin', 'pastor']:
            is_owner = True
        elif request.user.departamentos_liderados.filter(id=escala.departamento_alocado.id).exists():
            is_owner = True

        if not is_owner:
            messages.error(request, "Acesso Negado para este departamento.")
            return redirect('checkins_hoje_desktop')

        escala.checkin_realizado = True
        escala.data_hora_checkin = timezone.now()
        escala.status = 'presente'
        escala.save()

        LogAuditoria.objects.create(
            usuario_acao=request.user,
            acao_realizada='CHECKIN_MANUAL',
            tabela_afetada='Escala',
            diferenca_json={"escala_id": escala.id, "membro": escala.membro_escalado.get_full_name()}
        )

        messages.success(request, f"Check-in manual realizado para {escala.membro_escalado.get_full_name()}!")
        return redirect('checkins_hoje_desktop')

    from django.shortcuts import redirect
    from django.contrib import messages
    messages.error(request, "Método não permitido.")
    return redirect('checkins_hoje_desktop')

@login_required
def checkin_manual_avulso(request):
    if request.method == 'POST':
        membro_id = request.POST.get('membro_id')
        culto_id = request.POST.get('culto_id')
        departamento_id = request.POST.get('departamento_id')

        if membro_id and culto_id and departamento_id:
            membro = get_object_or_404(Membro, id=membro_id)
            from core.models import CultoEvento, Departamento
            from escalas.models import Escala
            culto = get_object_or_404(CultoEvento, id=culto_id)
            departamento = get_object_or_404(Departamento, id=departamento_id)

            escala = Escala.objects.create(
                membro_escalado=membro,
                departamento_alocado=departamento,
                data_escala=timezone.now().date(),
                horario_inicio=culto.horario_inicio,
                horario_fim=culto.horario_fim,
                checkin_realizado=True,
                data_hora_checkin=timezone.now(),
                tipo_checkin='MANUAL'
            )
            from django.contrib import messages
            messages.success(request, f'Presença Extra registrada para {membro.first_name}!')

    return redirect('checkins_hoje_desktop')
