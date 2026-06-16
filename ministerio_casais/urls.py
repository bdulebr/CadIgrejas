"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: ministerio_casais/urls.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.urls import path
from . import views
from . import views_alunos
from . import views_professores

urlpatterns = [
    path('dashboard/', views.dashboard_casais, name='dashboard_casais'),
    path('cadastrar/', views.cadastrar_casal, name='cadastrar_casal'),
    path('perfil/<int:casal_id>/', views.perfil_casal, name='perfil_casal'),
    path('casal/<int:casal_id>/nova-sessao/', views.nova_sessao_aconselhamento, name='nova_sessao_aconselhamento'),
    path('casal/<int:casal_id>/editar/', views.editar_casal, name='editar_casal'),
    path('casal/<int:casal_id>/pdf-individual/', views.exportar_relatorio_individual_casais, name='exportar_relatorio_individual_casais'),

    # Painel Pastoral
    path('painel/', views.painel_pastoral_casais, name='painel_pastoral_casais'),
    path('casal/<int:casal_id>/atualizar-status/', views.atualizar_status_casal, name='atualizar_status_casal'),
    path('casal/<int:casal_id>/arquivar/', views.arquivar_casal, name='arquivar_casal'),
    path('casal/<int:casal_id>/excluir/', views.excluir_casal, name='excluir_casal'),

    # Cursos e Certificados
    path('cursos/', views.cursos_dashboard, name='cursos_casais'),
    path('cursos/adicionar/', views.adicionar_curso, name='adicionar_curso'),
    path('cursos/<int:curso_id>/editar/', views.editar_curso, name='editar_curso'),
    path('cursos/<int:curso_id>/excluir/', views.excluir_curso, name='excluir_curso'),
    path('casal/<int:casal_id>/matricular/', views.matricular_casal, name='matricular_casal'),
    path('matricula/<int:matricula_id>/aprovar/', views.aprovar_matricula, name='aprovar_matricula'),
    path('matricula/<int:matricula_id>/desfazer-aprovacao/', views.desfazer_aprovacao_matricula, name='desfazer_aprovacao_matricula'),
    path('matricula/<int:matricula_id>/upload-certificado/', views.upload_certificado, name='upload_certificado'),

    # Gestão Financeira de Cursos
    path('cursos/financeiro/', views.gestao_financeira_cursos, name='gestao_financeira_cursos'),
    path('matricula/<int:matricula_id>/registrar-pagamento/', views.registrar_pagamento_curso, name='registrar_pagamento_curso'),
    path('matricula/<int:matricula_id>/disparar-cobranca/', views.disparar_cobranca_curso, name='disparar_cobranca_curso'),
    path('cursos/financeiro/pdf/', views.pdf_relatorio_financeiro_cursos, name='pdf_relatorio_financeiro_cursos'),

    path('exportar/geral/', views.relatorio_geral_casais, name='exportar_relatorio_geral_casais'),

    # Gestão de Turmas e Professores (LMS - Admin)
    path('cursos/<int:curso_id>/turmas/', views_professores.gestao_turmas_curso, name='gestao_turmas_curso'),
    path('cursos/<int:curso_id>/turmas/adicionar/', views_professores.adicionar_turma, name='adicionar_turma_curso'),
    path('turmas/<int:turma_id>/excluir/', views_professores.excluir_turma, name='excluir_turma_curso'),
    path('turmas/<int:turma_id>/professor/adicionar/', views_professores.adicionar_professor, name='adicionar_professor_turma'),
    path('professor/vinculo/<int:vinculo_id>/remover/', views_professores.remover_professor, name='remover_professor_turma'),
    path('cursos/<int:curso_id>/professor/externo/', views_professores.cadastrar_professor_externo, name='cadastrar_professor_externo'),
    path('turmas/<int:turma_id>/mural/', views_professores.mural_professor_turma, name='mural_professor_turma'),
    path('turmas/<int:turma_id>/postar/', views_professores.nova_postagem, name='nova_postagem_turma'),
    path('postagem/<int:postagem_id>/excluir/', views_professores.excluir_postagem, name='excluir_postagem_turma'),
    path('matricula/<int:matricula_id>/link-magico/', views_professores.gerar_link_magico, name='gerar_link_magico'),
    path('turma/<int:turma_id>/matricular/', views_professores.matricular_aluno_mural, name='matricular_aluno_mural'),
    path('matricula/<int:matricula_id>/remover/', views_professores.remover_aluno_mural, name='remover_aluno_mural'),
    path('matricula/<int:matricula_id>/enviar-email/', views_professores.enviar_email_acesso, name='enviar_email_acesso_aluno'),
    path('turma/<int:turma_id>/diario/', views_professores.diario_classe_turma, name='diario_classe_turma'),
    path('turma/<int:turma_id>/aula/nova/', views_professores.nova_aula_turma, name='nova_aula_turma'),
    path('aula/<int:aula_id>/chamada/', views_professores.fazer_chamada_aula, name='fazer_chamada_aula'),

    # Portal do Aluno (LMS)
    path('aluno/login/', views_alunos.login_aluno, name='login_aluno'),
    path('aluno/logout/', views_alunos.logout_aluno, name='logout_aluno'),
    path('aluno/trocar-senha/', views_alunos.trocar_senha_aluno, name='trocar_senha_aluno'),
    path('aluno/portal/', views_alunos.portal_aluno, name='portal_aluno'),
    path('aluno/sala/<int:turma_id>/', views_alunos.sala_de_aula_aluno, name='sala_de_aula_aluno'),
    path('aluno/tarefa/<int:postagem_id>/enviar/', views_alunos.enviar_tarefa_aluno, name='enviar_tarefa_aluno'),
]
