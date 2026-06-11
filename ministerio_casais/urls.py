from django.urls import path
from . import views

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

    # Cursos e Certificados
    path('cursos/', views.cursos_dashboard, name='cursos_casais'),
    path('cursos/adicionar/', views.adicionar_curso, name='adicionar_curso'),
    path('casal/<int:casal_id>/matricular/', views.matricular_casal, name='matricular_casal'),
    path('matricula/<int:matricula_id>/aprovar/', views.aprovar_matricula, name='aprovar_matricula'),
    path('matricula/<int:matricula_id>/upload-certificado/', views.upload_certificado, name='upload_certificado'),
    path('exportar/geral/', views.relatorio_geral_casais, name='exportar_relatorio_geral_casais'),
]
