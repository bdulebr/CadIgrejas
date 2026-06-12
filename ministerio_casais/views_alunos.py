from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Q
from .models import Casal, MatriculaCursoCasal, TurmaCurso, PostagemCurso, EntregaAtividadeAluno

def aluno_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'aluno_id' in request.session:
            return view_func(request, *args, **kwargs)
        # Check Magic Link
        token = request.GET.get('token')
        if token:
            matricula = MatriculaCursoCasal.objects.filter(token_acesso=token).first()
            if matricula:
                request.session['aluno_id'] = matricula.casal.id
                return redirect('portal_aluno')
        return redirect('login_aluno')
    return _wrapped_view

def login_aluno(request):
    token = request.GET.get('token')
    if token:
        matricula = MatriculaCursoCasal.objects.filter(token_acesso=token).first()
        if matricula:
            request.session['aluno_id'] = matricula.casal.id
            return redirect('portal_aluno')

    if 'aluno_id' in request.session:
        return redirect('portal_aluno')

    return render(request, 'ministerio_casais/alunos/login.html')

def logout_aluno(request):
    if 'aluno_id' in request.session:
        del request.session['aluno_id']
    return redirect('login_aluno')

@aluno_required
def trocar_senha_aluno(request):
    casal = get_object_or_404(Casal, id=request.session['aluno_id'])

    if request.method == 'POST':
        nova_senha = request.POST.get('nova_senha')
        confirmar_senha = request.POST.get('confirmar_senha')

        if nova_senha == confirmar_senha and len(nova_senha) >= 6:
            casal.senha = make_password(nova_senha)
            casal.precisa_trocar_senha = False
            casal.save()
            messages.success(request, 'Senha alterada com sucesso! Bem-vindo(a) ao portal.')
            return redirect('portal_aluno')
        else:
            messages.error(request, 'As senhas não coincidem ou são muito curtas (mín. 6 caracteres).')

    return render(request, 'ministerio_casais/alunos/trocar_senha.html', {'casal': casal})

@aluno_required
def portal_aluno(request):
    casal = get_object_or_404(Casal, id=request.session['aluno_id'])
    matriculas = MatriculaCursoCasal.objects.filter(casal=casal).select_related('turma__curso')

    return render(request, 'ministerio_casais/alunos/portal.html', {
        'casal': casal,
        'matriculas': matriculas
    })

@aluno_required
def sala_de_aula_aluno(request, turma_id):
    casal = get_object_or_404(Casal, id=request.session['aluno_id'])
    matricula = get_object_or_404(MatriculaCursoCasal, casal=casal, turma_id=turma_id)
    turma = matricula.turma
    # Filtrar postagens: ou são públicas (sem alunos específicos) ou foram enviadas diretamente para este aluno
    postagens = turma.postagens.filter(
        Q(alunos_especificos__isnull=True) | Q(alunos_especificos=matricula)
    ).distinct().order_by('-data_postagem')

    entregas = EntregaAtividadeAluno.objects.filter(matricula=matricula)
    entregas_map = {e.postagem_id: e for e in entregas}

    for post in postagens:
        post.entrega_aluno = entregas_map.get(post.id)

    return render(request, 'ministerio_casais/alunos/sala_de_aula.html', {
        'casal': casal,
        'matricula': matricula,
        'turma': turma,
        'postagens': postagens
    })

@aluno_required
def enviar_tarefa_aluno(request, postagem_id):
    if request.method == 'POST':
        postagem = get_object_or_404(PostagemCurso, id=postagem_id)
        casal = get_object_or_404(Casal, id=request.session['aluno_id'])
        matricula = get_object_or_404(MatriculaCursoCasal, casal=casal, turma=postagem.turma)

        arquivo = request.FILES.get('arquivo')
        comentario = request.POST.get('comentario')

        if arquivo:
            entrega, created = EntregaAtividadeAluno.objects.get_or_create(
                postagem=postagem,
                matricula=matricula,
                defaults={'arquivo_enviado': arquivo, 'comentario_aluno': comentario}
            )
            if not created:
                entrega.arquivo_enviado = arquivo
                if comentario:
                    entrega.comentario_aluno = comentario
                entrega.save()
            messages.success(request, 'Atividade enviada com sucesso!')
        else:
            messages.error(request, 'Nenhum arquivo foi anexado.')

    return redirect('sala_de_aula_aluno', turma_id=postagem.turma.id)
