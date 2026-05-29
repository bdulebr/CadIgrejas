import requests
from django.utils import timezone
from core.models import LogAuditoria

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def registrar_log_forense(request, acao, tabela, diff_json, usuario=None):
    """
    Registra um log na blockchain local (Zero-Trust) com captura avançada 
    de IP, Geolocation e User-Agent.
    """
    if request:
        ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Desconhecido')[:250]
        usuario_acao = usuario or (request.user if request.user.is_authenticated else None)
    else:
        ip = '127.0.0.1'
        user_agent = 'System Daemon / Background'
        usuario_acao = usuario
        
    cidade = 'Desconhecida'
    isp = 'Desconhecido'
    
    # Busca GeoIP (Não falha se der erro de rede)
    if ip and ip not in ['127.0.0.1', 'localhost']:
        try:
            # IP-API é público e não requer chave (limitado a 45 requisições por minuto)
            resp = requests.get(f'http://ip-api.com/json/{ip}', timeout=1.5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') == 'success':
                    cidade = f"{data.get('city', '')} - {data.get('region', '')} / {data.get('countryCode', '')}"
                    isp = data.get('isp', '')[:145]
        except Exception:
            pass # Failsafe: continua a gravar o log mesmo sem net
            
    LogAuditoria.objects.create(
        usuario_acao=usuario_acao,
        acao_realizada=acao,
        tabela_afetada=tabela,
        ip_origem=ip,
        cidade_origem=cidade[:100],
        isp_origem=isp,
        user_agent=user_agent,
        diferenca_json=diff_json
    )
