from django.urls import path
from . import views

app_name = 'atendimento_pastoral'

urlpatterns = [
    path('dashboard/', views.dashboard_agenda, name='dashboard_agenda'),
    path('pessoas/', views.lista_pessoas, name='lista_pessoas'),
    path('pessoa/nova/', views.criar_pessoa, name='criar_pessoa'),
    path('pessoa/<int:pessoa_id>/', views.prontuario_pessoa, name='prontuario_pessoa'),

    path('agendamento/novo/', views.criar_agendamento, name='criar_agendamento'),
    path('agendamento/<int:agendamento_id>/iniciar/', views.iniciar_sessao, name='iniciar_sessao'),
    path('agendamento/<int:agendamento_id>/alterar-status/', views.alterar_status_agendamento, name='alterar_status_agendamento'),

    path('sessao/nova/avulsa/', views.sessao_avulsa, name='sessao_avulsa'),
    path('sessao/<int:sessao_id>/', views.detalhes_sessao, name='detalhes_sessao'),
    path('sessao/<int:sessao_id>/gerar-ia/', views.gerar_resumo_ia, name='gerar_resumo_ia'),
    path('sessao/<int:sessao_id>/gerar-aci/', views.gerar_aci_ia, name='gerar_aci_ia'),
    path('sessao/<int:sessao_id>/pdf/', views.gerar_pdf_sessao, name='gerar_pdf_sessao'),
]
