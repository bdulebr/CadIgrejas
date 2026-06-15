
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views

urlpatterns = [
    # Auth
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Perfil
    path('perfil/me/', views.PerfilLogadoView.as_view(), name='api_perfil_me'),

    # Escalas Pessoais e Departamento
    path('escalas/', views.MinhasEscalasView.as_view(), name='api_minhas_escalas'),
    path('escalas/departamento/', views.DepartamentoEscalasView.as_view(), name='api_depto_escalas'),
    path('escalas/ausencias/', views.AusenciasView.as_view(), name='api_ausencias'),
    path('escalas/motor-ia/', views.MotorIAView.as_view(), name='api_motor_ia'),

    # Lider
    path('lider/membros/', views.LiderMembrosView.as_view(), name='api_lider_membros'),
    path('lider/competencias/', views.LiderCompetenciasView.as_view(), name='api_lider_comps'),
    path('lider/competencias/<int:comp_id>/slots/', views.LiderCompetenciaSlotsView.as_view(), name='api_lider_comp_slots'),
]
