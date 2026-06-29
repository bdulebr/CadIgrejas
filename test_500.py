import os
import django
import sys
from django.test import RequestFactory

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "intranet.settings")
django.setup()

from django.contrib.auth import get_user_model
from ministerio_casais.views_eventos import dashboard_eventos
from ministerio_casais.views_financeiro import painel_financeiro

User = get_user_model()
user = User.objects.filter(is_superuser=True).first()

factory = RequestFactory()

print("--- Testando Eventos ---")
request = factory.get('/casais/eventos/')
request.user = user
# Adicionar session
from django.contrib.sessions.middleware import SessionMiddleware
middleware = SessionMiddleware(lambda r: None)
middleware.process_request(request)
request.session.save()
# Adicionar messages
from django.contrib.messages.middleware import MessageMiddleware
msg_middleware = MessageMiddleware(lambda r: None)
msg_middleware.process_request(request)

try:
    response = dashboard_eventos(request)
    print("Dashboard Eventos OK", response.status_code)
except Exception as e:
    import traceback
    traceback.print_exc()

print("\n--- Testando Financeiro ---")
request_fin = factory.get('/casais/painel-financeiro/')
request_fin.user = user
middleware.process_request(request_fin)
request_fin.session.save()
msg_middleware.process_request(request_fin)

try:
    response_fin = painel_financeiro(request_fin)
    print("Painel Financeiro OK", response_fin.status_code)
except Exception as e:
    import traceback
    traceback.print_exc()
