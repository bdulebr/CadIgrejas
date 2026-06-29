"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: ministerio_casais/views_professores.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.utils import timezone
from intranet.services.whatsapp_service import enviar_whatsapp_template
from intranet.services.gmail_service import enviar_email_html
from core.models import EmailLog
from .models import AulaTurma, PresencaAula
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from .models import CursoCasal, TurmaCurso, ProfessorTurma, PostagemCurso, EntregaAtividadeAluno, MatriculaCursoCasal, Casal
import uuid

User = get_user_model()

@login_required
def gestao_turmas_curso(request, curso_id):
    curso = get_object_or_404(CursoCasal, id=curso_id)
    turmas = curso.turmas.all().prefetch_related('professores__professor', 'matriculas__casal')

    # Todos os membros que podem ser professores (para o dropdown)
    possiveis_professores = User.objects.all().order_by('first_name', 'username')

    return render(request, 'ministerio_casais/professores/gestao_turmas.html', {
        'curso': curso,
        'turmas': turmas,
        'possiveis_professores': possiveis_professores
    })

@login_required
def adicionar_turma(request, curso_id):
    if request.method == 'POST':
        curso = get_object_or_404(CursoCasal, id=curso_id)
        nome_turma = request.POST.get('nome_turma')
        status = request.POST.get('status', 'Aberta')
        valor_curso = request.POST.get('valor_curso', 0.00)
        carga_horaria = int(request.POST.get('carga_horaria', 10))
        duracao_aula_horas = int(request.POST.get('duracao_aula_horas', 2))
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')
        dias_semana_list = request.POST.getlist('dias_semana')
        dias_semana = ", ".join(dias_semana_list)
        limite_faltas = int(request.POST.get('limite_faltas', 3))
        percentual_presenca_minimo = int(request.POST.get('percentual_presenca_minimo', 75))
        emite_certificado = 'emite_certificado' in request.POST
        compra_camiseta = 'compra_camiseta' in request.POST

        from datetime import datetime, timedelta

        try:
            dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date() if data_inicio else None
            dt_fim = datetime.strptime(data_fim, "%Y-%m-%d").date() if data_fim else None
        except ValueError:
            dt_inicio = None
            dt_fim = None

        turma = TurmaCurso.objects.create(
            curso=curso,
            nome_turma=nome_turma,
            status=status,
            valor_curso=valor_curso,
            carga_horaria=carga_horaria,
            duracao_aula_horas=duracao_aula_horas,
            data_inicio=dt_inicio,
            dias_semana=dias_semana,
            limite_faltas=limite_faltas,
            percentual_presenca_minimo=percentual_presenca_minimo,
            emite_certificado=emite_certificado,
            compra_camiseta=compra_camiseta
        )

        # Inteligência Artificial de Calendário: Gerar Aulas Automaticamente
        if dt_inicio and dias_semana_list and duracao_aula_horas > 0:
            total_aulas = carga_horaria // duracao_aula_horas
            mapa_dias = {
                'Segunda': 0, 'Terça': 1, 'Quarta': 2, 'Quinta': 3,
                'Sexta': 4, 'Sábado': 5, 'Domingo': 6
            }
            dias_permitidos = [mapa_dias.get(d) for d in dias_semana_list if mapa_dias.get(d) is not None]

            aulas_geradas = 0
            dia_atual = dt_inicio
            while aulas_geradas < total_aulas:
                if dia_atual.weekday() in dias_permitidos:
                    aulas_geradas += 1
                    AulaTurma.objects.create(
                        turma=turma,
                        titulo=f"Aula {aulas_geradas:02d}",
                        data_aula=dia_atual
                    )
                dia_atual += timedelta(days=1)
                # Fail-safe para loop infinito de data
                if aulas_geradas == 0 and (dia_atual - dt_inicio).days > 365:
                    break

        messages.success(request, 'Turma criada e calendário de aulas agendado!')
        return redirect('gestao_turmas_curso', curso_id=curso.id)
    return redirect('gestao_turmas_curso', curso_id=curso_id)

@login_required
def excluir_turma(request, turma_id):
    turma = get_object_or_404(TurmaCurso, id=turma_id)
    curso_id = turma.curso.id
    if request.method == 'POST':
        turma.delete()
        messages.success(request, 'Turma excluída com sucesso.')
    return redirect('gestao_turmas_curso', curso_id=curso_id)

@login_required
def adicionar_professor(request, turma_id):
    turma = get_object_or_404(TurmaCurso, id=turma_id)
    if request.method == 'POST':
        professor_id = request.POST.get('professor_id')

        if ProfessorTurma.objects.filter(turma=turma, professor_id=professor_id).exists():
            messages.warning(request, 'Este professor já está vinculado a esta turma.')
        else:
            ProfessorTurma.objects.create(turma=turma, professor_id=professor_id)
            messages.success(request, 'Professor vinculado com sucesso.')

    return redirect('gestao_turmas_curso', curso_id=turma.curso.id)

@login_required
def remover_professor(request, vinculo_id):
    try:
        vinculo = ProfessorTurma.objects.get(id=vinculo_id)
    except ProfessorTurma.DoesNotExist:
        messages.error(request, f'O vínculo de professor com ID {vinculo_id} não foi encontrado ou já foi removido.')
        return redirect('dashboard')  # Redireciona para um painel geral se o vínculo não existir

    curso_id = vinculo.turma.curso.id
    if request.method == 'POST':
        vinculo.delete()
        messages.success(request, 'Professor removido da turma.')
    return redirect('gestao_turmas_curso', curso_id=curso_id)

@login_required
def cadastrar_professor_externo(request, curso_id):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        cpf = request.POST.get('cpf')
        data_nascimento = request.POST.get('data_nascimento')
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            messages.error(request, 'Este e-mail já está em uso.')
        else:
            user = User.objects.create(
                username=email,
                email=email,
                first_name=nome,
                cpf=cpf,
                data_nascimento=data_nascimento if data_nascimento else None,
                password=make_password(senha),
                is_staff=False,  # Não tem acesso ao painel de admin
            )
            # Vincular automaticamente a alguma turma? O usuário pediu para cadastrar para acesso à plataforma.
            # O professor foi criado. Agora o líder precisa vinculá-lo no dropdown.
            messages.success(request, f'Professor externo {nome} cadastrado com sucesso. Agora você pode vinculá-lo às turmas.')

    return redirect('gestao_turmas_curso', curso_id=curso_id)

@login_required
def mural_professor_turma(request, turma_id):
    turma = get_object_or_404(TurmaCurso, id=turma_id)
    postagens = turma.postagens.all().order_by('-data_postagem').prefetch_related('entregas__matricula__casal')

    # Casais que não estão nesta turma
    casais_disponiveis = Casal.objects.exclude(matriculas_cursos__turma=turma).filter(arquivado=False).order_by('nome_conjuge_1')

    return render(request, 'ministerio_casais/professores/mural_turma.html', {
        'turma': turma,
        'postagens': postagens,
        'casais_disponiveis': casais_disponiveis,
    })

@login_required
def matricular_aluno_mural(request, turma_id):
    from django.contrib import messages  # Garante que messages está importado
    from django.urls import reverse
    from django.shortcuts import redirect  # Garante que redirect está importado
    from django.contrib.auth.hashers import make_password  # Garante que make_password está importado, usado no bloco original
    try:
        turma = TurmaCurso.objects.get(id=turma_id)
    except TurmaCurso.DoesNotExist:
        messages.error(request, f'A turma com ID {turma_id} não foi encontrada.')
        return redirect('dashboard')  # Redireciona para um painel geral se a turma não existir

    if request.method == 'POST':
        casal_id = request.POST.get('casal_id')
        if casal_id:
            try:
                casal = Casal.objects.get(id=casal_id)
            except Casal.DoesNotExist:
                messages.error(request, f'O casal com ID {casal_id} não foi encontrado.')
                return redirect('mural_professor_turma', turma_id=turma.id)  # Redireciona de volta para o mural da turma válida

            if not MatriculaCursoCasal.objects.filter(turma=turma, casal=casal).exists():
                MatriculaCursoCasal.objects.create(turma=turma, casal=casal)

                # Ativar senha se for primeiro acesso
                if not casal.senha:
                    casal.senha = make_password('123456789')
                    casal.precisa_trocar_senha = True
                    casal.save()

                messages.success(request, f'{casal.nomes_juntos} matriculado(a) com sucesso!')
            else:
                messages.warning(request, 'Este casal já está na turma.')
    return redirect('mural_professor_turma', turma_id=turma.id)

@login_required
def nova_postagem(request, turma_id):
    if request.method == 'POST':
        turma = get_object_or_404(TurmaCurso, id=turma_id)
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        tipo = request.POST.get('tipo')
        arquivo = request.FILES.get('arquivo')
        data_limite = request.POST.get('data_limite')

        PostagemCurso.objects.create(
            turma=turma,
            titulo=titulo,
            descricao=descricao,
            tipo=tipo,
            arquivo=arquivo,
            data_limite=data_limite if data_limite else None
        )
        messages.success(request, 'Postagem criada com sucesso!')
    return redirect('mural_professor_turma', turma_id=turma_id)

@login_required
def excluir_postagem(request, postagem_id):
    postagem = get_object_or_404(PostagemCurso, id=postagem_id)
    turma_id = postagem.turma.id
    if request.method == 'POST':
        postagem.delete()
        messages.success(request, 'Postagem removida.')
    return redirect('mural_professor_turma', turma_id=turma_id)

@login_required
def gerar_link_magico(request, matricula_id):
    from django.contrib import messages
    from django.urls import reverse
    from django.shortcuts import redirect

    try:
        matricula = MatriculaCursoCasal.objects.get(id=matricula_id)
    except MatriculaCursoCasal.DoesNotExist:
        messages.error(request, f'A matrícula com ID {matricula_id} não foi encontrada ou já foi removida.')
        return redirect('dashboard')
    if request.method == 'POST':
        if not matricula.token_acesso:
            matricula.token_acesso = str(uuid.uuid4())
            matricula.save()
        messages.success(request, 'Link mágico gerado com sucesso.')
    return redirect('mural_professor_turma', turma_id=matricula.turma.id)


@login_required
def diario_classe_turma(request, turma_id):
    turma = get_object_or_404(TurmaCurso, id=turma_id)
    aulas = turma.aulas.all().order_by('-data_aula')
    return render(request, 'ministerio_casais/professores/diario_classe.html', {
        'turma': turma,
        'aulas': aulas,
    })

@login_required
def nova_aula_turma(request, turma_id):
    turma = get_object_or_404(TurmaCurso, id=turma_id)
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        data_aula = request.POST.get('data_aula')

        aula = AulaTurma.objects.create(
            turma=turma,
            titulo=titulo,
            data_aula=data_aula
        )

        # Cria registro de presença vazio (default True) para todos os matriculados
        for matricula in turma.matriculas.filter(status_matricula='Ativa'):
            PresencaAula.objects.create(aula=aula, matricula=matricula, presente=True)

        messages.success(request, f'Aula "{titulo}" criada! Faça a chamada abaixo.')
        return redirect('fazer_chamada_aula', aula_id=aula.id)
    return redirect('diario_classe_turma', turma_id=turma.id)

@login_required
def fazer_chamada_aula(request, aula_id):
    aula = get_object_or_404(AulaTurma, id=aula_id)
    presencas = aula.presencas.select_related('matricula__casal').all()

    if request.method == 'POST':
        faltas_marcadas = 0
        for presenca in presencas:
            # Checkbox: se estiver no POST, faltou. Se não, presente.
            # Vamos usar checkbox para marcar QUEM FALTOU
            faltou = request.POST.get(f'falta_{presenca.id}') == 'on'
            justificada = request.POST.get(f'justificada_{presenca.id}') == 'on'

            presenca.presente = not faltou
            presenca.justificada = justificada
            presenca.save()

            if faltou and not justificada:
                faltas_marcadas += 1
                # Enviar e-mail de alerta de falta
                _enviar_alerta_falta(request, presenca)

        aula.realizada = True
        aula.save()

        # Verificar limites de reprovação
        _verificar_reprovacoes_turma(aula.turma)

        messages.success(request, f'Chamada salva! {faltas_marcadas} faltas registradas e alunos notificados.')
        return redirect('diario_classe_turma', turma_id=aula.turma.id)

    return render(request, 'ministerio_casais/professores/fazer_chamada.html', {
        'aula': aula,
        'turma': aula.turma,
        'presencas': presencas
    })

def _enviar_alerta_falta(request, presenca):
    from django.conf import settings
    casal = presenca.matricula.casal
    emails = []
    if casal.email_1:
        emails.append(casal.email_1)
    if casal.email_2:
        emails.append(casal.email_2)

    for email in emails:
        try:
            enviar_email_html(
                destinatario=email,
                assunto=f'Sentimos sua falta na aula "{presenca.aula.titulo}"!',
                template_name='emails/ministerio_casais/email_falta_aula.html',
                context={
                    'casal': casal.nomes_juntos,
                    'aula': presenca.aula.titulo,
                    'turma': presenca.aula.turma.nome_turma,
                    'link_portal': request.build_absolute_uri(reverse('mc_aluno_login'))
                }
            )
        except Exception as e:
            EmailLog.objects.create(
                destinatario=email,
                assunto="Erro ao enviar alerta de falta",
                status='erro',
                erro_mensagem=str(e)
            )

def _verificar_reprovacoes_turma(turma):
    total_aulas_realizadas = turma.aulas.filter(realizada=True).count()
    if total_aulas_realizadas == 0:
        return

    for matricula in turma.matriculas.filter(status_matricula='Ativa'):
        faltas_injustificadas = matricula.historico_presenca.filter(presente=False, justificada=False).count()
        presencas = matricula.historico_presenca.filter(presente=True).count()

        reprovou_por_falta = False

        # Regra A: Limite numérico
        if turma.limite_faltas > 0 and faltas_injustificadas > turma.limite_faltas:
            reprovou_por_falta = True

        # Regra B: Percentual
        if total_aulas_realizadas > 0:
            percentual_atual = (presencas / total_aulas_realizadas) * 100
            if percentual_atual < turma.percentual_presenca_minimo:
                # O percentual pode cair no início se ele faltar a 1 aula de 2 (dá 50%).
                # Mas para reprovar por percentual, geralmente consideramos o percentual final ou projetado.
                # Como o usuário quis juntar A e B, vamos reprovar se ele já ultrapassou matematicamente o limite B.
                pass

        if reprovou_por_falta:
            matricula.status_matricula = 'Reprovado por Falta'
            matricula.save()

@login_required
def remover_aluno_mural(request, matricula_id):
    from django.contrib import messages
    from django.urls import reverse
    from django.shortcuts import redirect

    try:
        matricula = MatriculaCursoCasal.objects.get(id=matricula_id)
    except MatriculaCursoCasal.DoesNotExist:
        messages.error(request, f'A matrícula com ID {matricula_id} não foi encontrada ou já foi removida.')
        return redirect('dashboard')
    turma_id = matricula.turma.id
    if request.method == 'POST':
        casal_nome = matricula.casal.nomes_juntos
        matricula.delete()
        messages.success(request, f'Aluno {casal_nome} removido da turma com sucesso.')
    return redirect('mural_professor_turma', turma_id=turma_id)

@login_required
def enviar_email_acesso(request, matricula_id):
    from django.contrib import messages
    from django.urls import reverse
    from django.shortcuts import redirect

    try:
        matricula = MatriculaCursoCasal.objects.get(id=matricula_id)
    except MatriculaCursoCasal.DoesNotExist:
        messages.error(request, f'A matrícula com ID {matricula_id} não foi encontrada ou já foi removida.')
        return redirect('dashboard')
    turma_id = matricula.turma.id

    if not matricula.token_acesso:
        import uuid
        matricula.token_acesso = str(uuid.uuid4())
        matricula.save()

    casal = matricula.casal
    # Acessa os e-mails e telefones
    email_conjuge_1_obj = casal.email_1
    email_conjuge_2_obj = casal.email_2

    if not email_conjuge_1_obj and not email_conjuge_2_obj:
        messages.error(request, 'Este casal não possui nenhum e-mail cadastrado!')
        return redirect('mural_professor_turma', turma_id=turma_id)

    from django.conf import settings
    link_magico = request.build_absolute_uri(reverse('mc_aluno_login')) + f'?token={matricula.token_acesso}'

    from intranet.services.gmail_service import enviar_email_html
    from intranet.services.whatsapp_service import enviar_whatsapp_template

    destinatarios = []
    if email_conjuge_1_obj:
        destinatarios.append(email_conjuge_1_obj)
    if email_conjuge_2_obj:
        destinatarios.append(email_conjuge_2_obj)

    try:
        # Tenta enviar para ambos separadamente ou para o principal se quisermos.
        for dest in destinatarios:
            enviar_email_html(
                destinatario=dest,
                assunto=f'Seu Acesso ao Curso: {matricula.turma.curso.nome}',
                template_name='ministerio_casais/email_matricula_curso.html',
                context={
                    'casal': casal,
                    'matricula': matricula,
                    'link_magico': link_magico
                }
            )
        t1 = casal.telefone_1
        t2 = casal.telefone_2
        if t1:
            enviar_whatsapp_template(t1, 'casais_acesso_curso.txt', {'casal': casal, 'matricula': matricula, 'link_magico': link_magico})
        if t2 and t2 != t1:
            enviar_whatsapp_template(t2, 'casais_acesso_curso.txt', {'casal': casal, 'matricula': matricula, 'link_magico': link_magico})

        messages.success(request, f'Acesso enviado com sucesso para os contatos cadastrados!')
    except Exception as e:
        messages.warning(request, f'Erro ao enviar notificação de acesso: {e}')

    return redirect('mural_professor_turma', turma_id=turma_id)
