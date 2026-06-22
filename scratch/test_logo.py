import os
import django
from io import BytesIO

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
django.setup()

from xhtml2pdf import pisa
from core.models import ConfiguracaoSistema
from django.conf import settings

config_sys = ConfiguracaoSistema.objects.first()

def fetch_resources(uri, rel):
    print(f"fetch_resources called with uri: {uri}, rel: {rel}")
    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    elif uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))
    else:
        path = uri
    
    print(f"Resolved path: {path}")
    print(f"Path exists: {os.path.exists(path)}")
    return path

# let's try with relative uri
logo_uri = config_sys.igreja_logo.url

html = f"""
<html>
<body>
    <h1>Test</h1>
    <img src="{logo_uri}">
</body>
</html>
"""

result = BytesIO()
pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, link_callback=fetch_resources)

if pdf.err:
    print("Error")
else:
    print("Success")
