import os

pwa_code = """
# ==========================================
# PWA VIEWS (RECOVERED)
# ==========================================
def pwa_manifest(request):
    return render(request, 'pwa/manifest.json', content_type='application/json')

def pwa_service_worker(request):
    return render(request, 'pwa/sw.js', content_type='application/javascript')
"""

with open(r'c:\Users\MarcosLira\Desktop\Marcos\Projeto\core\views.py', 'a', encoding='utf-8') as f:
    f.write(pwa_code)
