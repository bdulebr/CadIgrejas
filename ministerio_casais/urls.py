from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_casais, name='dashboard_casais'),
    path('perfil/<int:casal_id>/', views.perfil_casal, name='perfil_casal'),
    path('certificado/<int:matricula_id>/', views.exportar_certificados, name='exportar_certificados'),
]
