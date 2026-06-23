"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: core/middleware.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
import threading
from django.shortcuts import render, redirect
from django.urls import reverse
from core.models import ConfiguracaoSistema

_thread_locals = threading.local()

def get_current_request():
    return getattr(_thread_locals, 'request', None)

class RequestMiddleware:
    """
    Middleware para capturar o request globalmente por thread.
    Isso permite que os models saibam quem é o usuário e qual é o IP sem precisarem
    receber o request explicitamente em cada view.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        response = self.get_response(request)
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
        return response


class MaintenanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow access to sysadmin and admin panels unconditionally for admins
        if request.path.startswith('/sysadmin/') or request.path.startswith('/admin/'):
            return self.get_response(request)

        try:
            config = ConfiguracaoSistema.objects.get(id=1)
            is_maintenance = config.is_maintenance
        except Exception:
            is_maintenance = False

        if is_maintenance:
            # Allow static files and login/logout
            if request.path.startswith('/static/') or request.path in [reverse('login'), reverse('logout')]:
                return self.get_response(request)

            # Allow super_admins
            if request.user.is_authenticated:
                if request.user.nivel_hierarquico == 'super_admin' or request.user.is_superuser:
                    return self.get_response(request)

            # Everyone else gets maintenance page
            return render(request, 'core/pages/maintenance.html', status=503)

        return self.get_response(request)


class ForcarTrocaSenhaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Pula checagem nas rotas estaticas ou rotas permitidas (logout, e a propria troca de senha)
            if not request.path.startswith('/static/') and not request.path.startswith('/admin/'):
                allowed_paths = [
                    reverse('forcar_troca_senha'),
                    reverse('logout'),
                ]
                if request.path not in allowed_paths:
                    # Checa se o membro tem a flag
                    if getattr(request.user, 'senha_padrao', False):
                        return redirect('forcar_troca_senha')

        return self.get_response(request)

class AIAutoEngineerMiddleware:
    """
    Middleware que atua como Cão de Guarda (Watchdog).
    Se o sistema estourar um erro fatal 500 para um usuário,
    este middleware intercepta o crash e engatilha o Motor de IA Autônoma
    no background para caçar e corrigir o erro imediatamente.
    """
"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: core/middleware.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
import threading
from django.shortcuts import render, redirect
from django.urls import reverse
from core.models import ConfiguracaoSistema

_thread_locals = threading.local()

def get_current_request():
    return getattr(_thread_locals, 'request', None)

class RequestMiddleware:
    """
    Middleware para capturar o request globalmente por thread.
    Isso permite que os models saibam quem é o usuário e qual é o IP sem precisarem
    receber o request explicitamente em cada view.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        response = self.get_response(request)
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
        return response


class MaintenanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow access to sysadmin and admin panels unconditionally for admins
        if request.path.startswith('/sysadmin/') or request.path.startswith('/admin/'):
            return self.get_response(request)

        try:
            config = ConfiguracaoSistema.objects.get(id=1)
            is_maintenance = config.is_maintenance
        except Exception:
            is_maintenance = False

        if is_maintenance:
            # Allow static files and login/logout
            if request.path.startswith('/static/') or request.path in [reverse('login'), reverse('logout')]:
                return self.get_response(request)

            # Allow super_admins
            if request.user.is_authenticated:
                if request.user.nivel_hierarquico == 'super_admin' or request.user.is_superuser:
                    return self.get_response(request)

            # Everyone else gets maintenance page
            return render(request, 'core/pages/maintenance.html', status=503)

        return self.get_response(request)


class ForcarTrocaSenhaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Pula checagem nas rotas estaticas ou rotas permitidas (logout, e a propria troca de senha)
            if not request.path.startswith('/static/') and not request.path.startswith('/admin/'):
                allowed_paths = [
                    reverse('forcar_troca_senha'),
                    reverse('logout'),
                ]
                if request.path not in allowed_paths:
                    # Checa se o membro tem a flag
                    if getattr(request.user, 'senha_padrao', False):
                        return redirect('forcar_troca_senha')

        return self.get_response(request)

class AIAutoEngineerMiddleware:
    """
    Middleware que atua como Cão de Guarda (Watchdog).
    Se o sistema estourar um erro fatal 500 para um usuário,
    este middleware intercepta o crash e engatilha o Motor de IA Autônoma
    no background para caçar e corrigir o erro imediatamente.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # INTERCEPTA ERROS HTTP QUE NÃO GERAM EXCEPTION (400 e 403)
        if response.status_code in [400, 403]:
            # Ignora rotas de login que dão 400 por senha errada
            if '/login/' not in request.path:
                from core.models import AIEngineerLog
                import logging
                logger = logging.getLogger(__name__)
                erro_str = f"HTTP Error {response.status_code} gerado como Response na rota: {request.path}\nMethod: {request.method}"

                pending_log = AIEngineerLog.objects.filter(status='PENDENTE', erro_analisado=erro_str).first()
                if not pending_log:
                    novo_log = AIEngineerLog.objects.create(
                        erro_analisado=erro_str,
                        status='PENDENTE',
                        detalhes=erro_str
                    )
                    log_id = novo_log.id
                    logger.error(f"AI Watchdog interceptou {response.status_code} e enviou para IA.")
                else:
                    log_id = pending_log.id
                return render(request, 'core/pages/eversinho_500.html', {'log_id': log_id}, status=response.status_code)

        return response

    def process_exception(self, request, exception):
        from django.http import Http404
        from django.core.exceptions import PermissionDenied

        # Filtro Inteligente de Erros 404 (Ignora 404 para não acionar a IA à toa quando dados não existem)
        if isinstance(exception, Http404):
            return None

        # A fatal bug happened! Put it in the queue for the AI Daemon.
        from core.models import AIEngineerLog
        import logging
        import traceback

        logger = logging.getLogger(__name__)
        erro_str = f"Exception: {str(exception)}\nPath: {request.path}\nTraceback: {traceback.format_exc()}"
        log_id = None

        # Só insere na fila se não houver erro igual pendente para evitar spam
        pending_log = AIEngineerLog.objects.filter(status='PENDENTE', erro_analisado=str(exception)).first()
        if not pending_log:
            novo_log = AIEngineerLog.objects.create(
                erro_analisado=str(exception),
                status='PENDENTE',
                detalhes=erro_str[:2000] # Limita tamanho no banco
            )
            log_id = novo_log.id
            logger.error(f"AI Watchdog inseriu novo erro na fila do AI Daemon: {str(exception)}")
        else:
            log_id = pending_log.id

        # Renderizar tela dinâmica do Eversinho
        return render(request, 'core/pages/eversinho_500.html', {'log_id': log_id}, status=500)
