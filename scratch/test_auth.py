import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
django.setup()

from django.contrib.auth import authenticate
from django.http import HttpRequest

request = HttpRequest()
request.META['REMOTE_ADDR'] = '127.0.0.1'

user = authenticate(request=request, username='admin@pvenseada.org', password='LMAr261614@2025')
print("Authenticated user:", user)
