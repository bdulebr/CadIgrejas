"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: core/urls.py
* DESCRIÇÃO: Rotas do módulo core.
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 25/05/2026 13:50
* LOG DE ALTERAÇÕES:
* - 25/05/2026 13:50: Criação inicial
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import webhooks

urlpatterns = [
    path('', views.login_view, name='login'),
    path('mfa-challenge/', views.mfa_challenge, name='mfa_challenge'),
    path('mfa/setup/', views.setup_mfa, name='setup_mfa'),
    path('mfa/desativar/', views.desativar_mfa, name='desativar_mfa'),
    path('api/eversinho-status/<int:log_id>/', views.eversinho_status_api, name='eversinho_status_api'),
    path('api/eversinho/chat/', views.eversinho_chat_api, name='eversinho_chat_api'),
    # Recuperação de Senha Segura
    path('recuperar-senha/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('recuperar-senha/bloqueado/', views.password_reset_blocked, name='password_reset_blocked'),
    path('recuperar-senha/enviado/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('recuperar-senha/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('recuperar-senha/completo/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('notificacao/<int:notificacao_id>/ler/', views.ler_notificacao, name='ler_notificacao'),
    path('notificacoes/ler_todas/', views.ler_todas_notificacoes, name='ler_todas_notificacoes'),
    path('perfil/', views.editar_perfil, name='editar_perfil'),
    path('seguranca/trocar-senha/', views.forcar_troca_senha, name='forcar_troca_senha'),
    path('sysadmin/', views.sysadmin_dashboard, name='sysadmin_dashboard'),
    path('pesquisa/', views.pesquisa_global_api, name='pesquisa_global_api'),
    path('sysadmin/toggle-manutencao/', views.sysadmin_toggle_manutencao, name='sysadmin_toggle_manutencao'),
    path('sysadmin/toggle-email/', views.sysadmin_toggle_email, name='sysadmin_toggle_email'),
    path('sysadmin/toggle-whatsapp/', views.sysadmin_toggle_whatsapp, name='sysadmin_toggle_whatsapp'),
    path('sysadmin/salvar-whatsapp/', views.sysadmin_salvar_whatsapp, name='sysadmin_salvar_whatsapp'),
    path('sysadmin/backup/baixar/', views.sysadmin_baixar_backup, name='sysadmin_baixar_backup'),
    path('sysadmin/backup/<int:backup_id>/baixar/', views.sysadmin_baixar_backup, name='sysadmin_baixar_backup_id'),
    path('sysadmin/backup/subir/', views.sysadmin_subir_backup, name='sysadmin_subir_backup'),
    path('sysadmin/backup/gdrive/', views.sysadmin_backup_gdrive, name='sysadmin_backup_gdrive'),
    path('sysadmin/backup/<int:backup_id>/gdrive/', views.sysadmin_backup_gdrive, name='sysadmin_backup_gdrive_id'),
    path('sysadmin/backup/gerar/', views.sysadmin_gerar_backup_local, name='sysadmin_gerar_backup'),
    path('sysadmin/backup/<int:backup_id>/deletar/', views.sysadmin_deletar_backup, name='sysadmin_deletar_backup'),
    path('sysadmin/backup/<int:backup_id>/restaurar/', views.sysadmin_restaurar_backup, name='sysadmin_restaurar_backup'),
    path('sysadmin/zerar/', views.sysadmin_zerar_banco, name='sysadmin_zerar_banco'),
    path('sysadmin/desbloquear-ip/', views.sysadmin_desbloquear_ip, name='sysadmin_desbloquear_ip'),
    path('sysadmin/limpar-cache/', views.sysadmin_limpar_cache, name='sysadmin_limpar_cache'),
    path('sysadmin/toggle-debug/', views.sysadmin_toggle_debug, name='sysadmin_toggle_debug'),
    path('sysadmin/salvar-env/', views.sysadmin_salvar_env, name='sysadmin_salvar_env'),
    path('sysadmin/deploy/', views.sysadmin_deploy_producao, name='sysadmin_deploy_producao'),
    path('sysadmin/salvar-igreja/', views.sysadmin_salvar_igreja, name='sysadmin_salvar_igreja'),
    path('sysadmin/salvar-alertas-invasao/', views.sysadmin_salvar_alertas_invasao, name='sysadmin_salvar_alertas_invasao'),

    # Motor de E-mail
    path('sysadmin/salvar-config-email/', views.sysadmin_salvar_config_email, name='sysadmin_salvar_config_email'),
    path('sysadmin/email/reenviar/<int:log_id>/', views.sysadmin_reenviar_email_id, name='sysadmin_reenviar_email_id'),
    path('sysadmin/email/reenviar-falhas/', views.sysadmin_reenviar_falhas, name='sysadmin_reenviar_falhas'),

    # Motor de WhatsApp
    path('sysadmin/whatsapp/reenviar/<int:log_id>/', views.sysadmin_reenviar_whatsapp_id, name='sysadmin_reenviar_whatsapp_id'),
    path('sysadmin/whatsapp/reenviar-falhas/', views.sysadmin_reenviar_whatsapp_falhas, name='sysadmin_reenviar_whatsapp_falhas'),

    # Links Rápidos
    path('sysadmin/links/salvar/', views.sysadmin_link_salvar, name='sysadmin_link_salvar'),
    path('sysadmin/links/<int:link_id>/deletar/', views.sysadmin_link_deletar, name='sysadmin_link_deletar'),

    # Auditoria Zero-Trust Forense
    path('sysadmin/logs/', views.sysadmin_logs_list, name='sysadmin_logs'),
    path('sysadmin/logs/tracker/', views.sysadmin_ux_tracker, name='sysadmin_ux_tracker'),

    # Webhooks Externos
    path('webhook/whatsapp/', webhooks.whatsapp_webhook, name='whatsapp_webhook'),
    path('sysadmin/logs/<int:log_id>/pdf/', views.sysadmin_log_pdf, name='sysadmin_log_pdf'),

    # Spider Test
    path('sysadmin/rodar-spider/', views.sysadmin_rodar_spider, name='sysadmin_rodar_spider'),
    path('sysadmin/baixar-spider-log/<int:log_id>/', views.sysadmin_baixar_log_spider, name='sysadmin_baixar_log_spider'),

    # AI Auto Engineer
    path('sysadmin/rodar-ai-engineer/', views.sysadmin_rodar_ai_engineer, name='sysadmin_rodar_ai_engineer'),
]
