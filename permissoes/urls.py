from django.urls import path
from . import views

app_name = 'permissoes'

urlpatterns = [
    path('', views.painel_permissoes, name='dashboard'),
    path('membro/<int:membro_id>/salvar/', views.salvar_permissoes_membro, name='salvar_membro'),
    path('departamento/<int:departamento_id>/salvar/', views.salvar_permissoes_departamento, name='salvar_departamento'),
]
