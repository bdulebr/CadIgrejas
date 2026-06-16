from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import timedelta
from permissoes.decorators import requer_permissao
from .models import PessoaAtendimento, AgendamentoPastoral, SessaoAtendimento
from django.core.paginator import Paginator
from django.db.models import Q
import json

def is_owner(request, sessao):
    return request.user == sessao.pastor

@login_required
@requer_permissao('atendimento_pastoral', 'ver')
def dashboard_agenda(request):
    """
    Exibe o calendário mensal em blocos e permite alternar para detalhes.
    Como é renderizado pelo FullCalendar no template, mandamos os dados via JSON aqui ou no próprio render.
    """
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        start = request.GET.get('start')
        end = request.GET.get('end')

        # Filtra os agendamentos do pastor logado.
        # *Regra de Privacidade*: Pastor só vê sua própria agenda no painel.
        agendamentos = AgendamentoPastoral.objects.filter(
            pastor=request.user,
        )

        if start and end:
            agendamentos = agendamentos.filter(data_agendamento__gte=start, data_agendamento__lte=end)

        events = []
        for ag in agendamentos:
            color = "#3b82f6" # Azul (Agendado)
            if ag.status == "Realizado": color = "#10b981" # Verde
            elif ag.status == "Cancelado": color = "#ef4444" # Vermelho
            elif ag.status == "Faltou": color = "#f59e0b" # Laranja

            events.append({
                'id': ag.id,
                'title': ag.pessoa.nome_completo,
                'start': f"{ag.data_agendamento.isoformat()}T{ag.hora_inicio.isoformat()}",
                'end': f"{ag.data_agendamento.isoformat()}T{ag.hora_fim.isoformat()}",
                'color': color,
                'url': f"/gabinete-pastoral/pessoa/{ag.pessoa.id}/", # Link para o prontuário
                'extendedProps': {
                    'local': ag.local,
                    'status': ag.status,
                    'whatsapp': ag.pessoa.telefone
                }
            })
        return JsonResponse(events, safe=False)

    return render(request, 'atendimento_pastoral/dashboard_agenda.html')

@login_required
@requer_permissao('atendimento_pastoral', 'ver')
def lista_pessoas(request):
    query = request.GET.get('q', '')
    pessoas_list = PessoaAtendimento.objects.all().order_by('-data_cadastro')

    if query:
        pessoas_list = pessoas_list.filter(
            Q(nome_completo__icontains=query) |
            Q(telefone__icontains=query) |
            Q(email__icontains=query)
        )

    paginator = Paginator(pessoas_list, 20)
    page_number = request.GET.get('page')
    pessoas = paginator.get_page(page_number)

    return render(request, 'atendimento_pastoral/lista_pessoas.html', {'pessoas': pessoas, 'query': query})

@login_required
@requer_permissao('atendimento_pastoral', 'editar')
def criar_pessoa(request):
    if request.method == 'POST':
        nome = request.POST.get('nome_completo')
        telefone = request.POST.get('telefone')
        email = request.POST.get('email')
        endereco = request.POST.get('endereco')
        estado_civil = request.POST.get('estado_civil')
        data_nasc = request.POST.get('data_nascimento')
        anotacoes = request.POST.get('anotacoes_gerais')

        tags = request.POST.getlist('tags_risco')

        pessoa = PessoaAtendimento.objects.create(
            nome_completo=nome,
            telefone=telefone,
            email=email,
            endereco=endereco,
            estado_civil=estado_civil,
            data_nascimento=data_nasc if data_nasc else None,
            anotacoes_gerais=anotacoes,
            tags_risco=tags
        )
        messages.success(request, 'Cadastro criado com sucesso!')
        return redirect('atendimento_pastoral:prontuario_pessoa', pessoa_id=pessoa.id)

    return render(request, 'atendimento_pastoral/form_pessoa.html')

@login_required
@requer_permissao('atendimento_pastoral', 'ver')
def prontuario_pessoa(request, pessoa_id):
    pessoa = get_object_or_404(PessoaAtendimento, id=pessoa_id)

    # Listar as sessões dessa pessoa.
    # REGRA CRÍTICA DE PRIVACIDADE: O pastor só vê as sessões que ELE mesmo atendeu.
    # Mesmo o Super Admin NÃO pode ver as sessões de outros pastores se a regra for restrita.
    todas_sessoes = SessaoAtendimento.objects.filter(pessoa=pessoa).order_by('-data_sessao')

    sessoes_permitidas = []
    for s in todas_sessoes:
        if s.is_restrito and s.pastor != request.user:
            continue # Pula
        else:
            sessoes_permitidas.append(s)

    agendamentos = AgendamentoPastoral.objects.filter(pessoa=pessoa, pastor=request.user).order_by('-data_agendamento')

    # WhatsApp Link Dinâmico
    # Remove tudo que não for número
    import re
    telefone_limpo = re.sub(r'\D', '', str(pessoa.telefone))
    whatsapp_link = f"https://wa.me/55{telefone_limpo}?text=Olá%20{pessoa.nome_completo},%20aqui%20é%20do%20Gabinete%20Pastoral." if telefone_limpo else None

    context = {
        'pessoa': pessoa,
        'sessoes': sessoes_permitidas,
        'agendamentos': agendamentos,
        'whatsapp_link': whatsapp_link
    }
    return render(request, 'atendimento_pastoral/prontuario_pessoa.html', context)

@login_required
@requer_permissao('atendimento_pastoral', 'editar')
def criar_agendamento(request):
    if request.method == 'POST':
        pessoa_id = request.POST.get('pessoa_id')
        data_agendamento = request.POST.get('data_agendamento')
        hora_inicio = request.POST.get('hora_inicio')
        hora_fim = request.POST.get('hora_fim')
        local = request.POST.get('local')

        pessoa = get_object_or_404(PessoaAtendimento, id=pessoa_id)

        AgendamentoPastoral.objects.create(
            pessoa=pessoa,
            pastor=request.user,
            data_agendamento=data_agendamento,
            hora_inicio=hora_inicio,
            hora_fim=hora_fim,
            local=local
        )
        messages.success(request, 'Agendamento salvo com sucesso!')
        return redirect('atendimento_pastoral:prontuario_pessoa', pessoa_id=pessoa.id)

    pessoas = PessoaAtendimento.objects.all().order_by('nome_completo')
    return render(request, 'atendimento_pastoral/form_agendamento.html', {'pessoas': pessoas})

@login_required
@requer_permissao('atendimento_pastoral', 'editar')
def alterar_status_agendamento(request, agendamento_id):
    ag = get_object_or_404(AgendamentoPastoral, id=agendamento_id, pastor=request.user)
    if request.method == 'POST':
        novo_status = request.POST.get('status')
        if novo_status in dict(AgendamentoPastoral.STATUS_CHOICES):
            ag.status = novo_status
            ag.save()
            messages.success(request, f'Status alterado para {novo_status}')
    return redirect(request.META.get('HTTP_REFERER', 'atendimento_pastoral:dashboard_agenda'))

@login_required
@requer_permissao('atendimento_pastoral', 'editar')
def iniciar_sessao(request, agendamento_id):
    ag = get_object_or_404(AgendamentoPastoral, id=agendamento_id, pastor=request.user)

    # Verifica se já existe sessão
    if hasattr(ag, 'sessao_realizada'):
        return redirect('atendimento_pastoral:detalhes_sessao', sessao_id=ag.sessao_realizada.id)

    if request.method == 'POST':
        resumo = request.POST.get('resumo_sessao')
        nivel = request.POST.get('nivel_crise', 1)
        retorno = request.POST.get('exige_retorno_em_dias')

        sessao = SessaoAtendimento.objects.create(
            agendamento=ag,
            pessoa=ag.pessoa,
            pastor=request.user,
            resumo_sessao=resumo,
            nivel_crise=nivel,
            exige_retorno_em_dias=retorno if retorno else None,
            is_restrito=True
        )
        ag.status = 'Realizado'
        ag.save()
        messages.success(request, 'Prontuário salvo com sucesso!')
        return redirect('atendimento_pastoral:prontuario_pessoa', pessoa_id=ag.pessoa.id)

    return render(request, 'atendimento_pastoral/form_sessao.html', {'agendamento': ag, 'pessoa': ag.pessoa})

@login_required
@requer_permissao('atendimento_pastoral', 'editar')
def sessao_avulsa(request):
    """Permite iniciar um atendimento sem agendamento prévio."""
    if request.method == 'POST':
        pessoa_id = request.POST.get('pessoa_id')
        resumo = request.POST.get('resumo_sessao')
        nivel = request.POST.get('nivel_crise', 1)
        retorno = request.POST.get('exige_retorno_em_dias')

        pessoa = get_object_or_404(PessoaAtendimento, id=pessoa_id)

        sessao = SessaoAtendimento.objects.create(
            pessoa=pessoa,
            pastor=request.user,
            resumo_sessao=resumo,
            nivel_crise=nivel,
            exige_retorno_em_dias=retorno if retorno else None,
            is_restrito=True
        )
        messages.success(request, 'Atendimento Avulso registrado!')
        return redirect('atendimento_pastoral:prontuario_pessoa', pessoa_id=pessoa.id)

    pessoas = PessoaAtendimento.objects.all().order_by('nome_completo')
    return render(request, 'atendimento_pastoral/form_sessao_avulsa.html', {'pessoas': pessoas})

@login_required
@requer_permissao('atendimento_pastoral', 'ver')
def detalhes_sessao(request, sessao_id):
    sessao = get_object_or_404(SessaoAtendimento, id=sessao_id)

    # Validação de Privacidade Extrema
    if sessao.is_restrito and not is_owner(request, sessao):
        messages.error(request, 'ACESSO NEGADO. Este prontuário é estritamente confidencial ao pastor que realizou o atendimento.')
        return redirect('dashboard')

    return render(request, 'atendimento_pastoral/detalhes_sessao.html', {'sessao': sessao})

@login_required
@requer_permissao('atendimento_pastoral', 'editar')
def gerar_resumo_ia(request, sessao_id):
    sessao = get_object_or_404(SessaoAtendimento, id=sessao_id, pastor=request.user)

    if request.method == 'POST':
        # IA Integrada via Gemini
        from intranet.services.gemini_ai import IAEngine

        anotacoes_brutas = sessao.resumo_sessao
        prompt = f"""
        Sou um Pastor e acabei de fazer um atendimento. Minhas anotações brutas: "{anotacoes_brutas}".
        Reescreva isso como um Prontuário Pastoral profissional, formal, empático, preservando todas as informações importantes,
        estruturado em:
        - Motivo do Aconselhamento
        - Diagnóstico Espiritual/Emocional
        - Orientação Dada
        - Passos Seguintes (Follow-up)
        Formate em texto limpo.
        """

        try:
            resposta_ia = IAEngine.gerar_texto(prompt)
            sessao.resumo_sessao = resposta_ia
            sessao.save()
            return JsonResponse({'status': 'success', 'novo_resumo': resposta_ia})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Método inválido'}, status=400)

@login_required
@requer_permissao('atendimento_pastoral', 'editar')
def gerar_aci_ia(request, sessao_id):
    sessao = get_object_or_404(SessaoAtendimento, id=sessao_id, pastor=request.user)

    if request.method == 'POST':
        from intranet.services.gemini_ai import IAEngine

        prontuario = sessao.resumo_sessao
        prompt = f"""
        Aja como um Psicólogo Sênior, especialista em análise comportamental, psicologia de relacionamentos interpessoais e avaliação clínica.
        Leia atentamente o relato de aconselhamento pastoral abaixo:

        "{prontuario}"

        Sua tarefa:
        1. Escreva uma "Análise Comportamental Inteligente (ACI)". Formule um parecer técnico, empático e investigativo, identificando raízes comportamentais, bloqueios emocionais, e sugerindo abordagens práticas baseadas na psicologia comportamental para ajudar essa pessoa.
        2. Identifique até 3 Tags Clínicas/Risco apropriadas (ex: "Crise Conjugal", "Risco de Suicídio", "Ansiedade Severa", "Luto", "Dependência Emocional").

        Responda ESTRITAMENTE em formato JSON com as seguintes chaves:
        "analise": "O seu texto de parecer comportamental aqui..."
        "tags": ["Tag1", "Tag2"]
        """

        try:
            # Pede para a IA retornar em JSON
            resposta_ia = IAEngine.gerar_texto(prompt)

            # Tentar fazer parse do JSON que a IA retornou (limpar crases se houver)
            import json
            import re

            clean_json = re.sub(r'```json|```', '', resposta_ia).strip()
            dados = json.loads(clean_json)

            nova_analise = dados.get('analise', '')
            novas_tags = dados.get('tags', [])

            sessao.analise_comportamental = nova_analise
            sessao.save(update_fields=['analise_comportamental'])

            # Adicionar as tags na pessoa se ainda não existirem
            pessoa = sessao.pessoa
            tags_atuais = set(pessoa.tags_risco)
            tags_atuais.update(novas_tags)
            pessoa.tags_risco = list(tags_atuais)
            pessoa.save(update_fields=['tags_risco'])

            return JsonResponse({
                'status': 'success',
                'analise': nova_analise,
                'novas_tags': novas_tags
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f"Erro ao processar IA: {str(e)}\nResposta bruta: {resposta_ia}"}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Método inválido'}, status=400)

@login_required
@requer_permissao('atendimento_pastoral', 'ver')
def gerar_pdf_sessao(request, sessao_id):
    sessao = get_object_or_404(SessaoAtendimento, id=sessao_id)

    if sessao.is_restrito and not is_owner(request, sessao):
        return HttpResponse('Acesso Negado (Sigilo Pastoral)', status=403)

    # Podemos retornar um HTML limpo otimizado para window.print()
    return render(request, 'atendimento_pastoral/pdf_sessao.html', {'sessao': sessao})
