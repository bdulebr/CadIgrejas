from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_casais, name='dashboard_casais'),
    path('kanban/', views.kanban_casais, name='kanban_casais'),
    path('cadastrar/', views.cadastrar_casal, name='cadastrar_casal'),
    path('perfil/<int:casal_id>/', views.perfil_casal, name='perfil_casal'),
    path('perfil/<int:casal_id>/editar/', views.editar_casal, name='editar_casal'),
    path('perfil/<int:casal_id>/sessao/add/', views.nova_sessao_aconselhamento, name='nova_sessao_aconselhamento'),
    path('perfil/<int:casal_id>/matricular/', views.matricular_casal, name='matricular_casal'),
    path('atualizar-status/<int:casal_id>/', views.atualizar_status_casal, name='atualizar_status_casal'),

    path('cursos/', views.cursos_dashboard, name='cursos_casais'),
    path('cursos/add/', views.adicionar_curso, name='adicionar_curso'),
    path('matricula/<int:matricula_id>/aprovar/', views.aprovar_matricula, name='aprovar_matricula'),

    path('certificado/<int:matricula_id>/', views.exportar_certificados, name='exportar_certificados'),
    path('exportar/geral/', views.relatorio_geral_casais, name='exportar_relatorio_geral_casais'),
]
