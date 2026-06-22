import os
import re

settings_path = r'C:\Users\MarcosLira\Desktop\Marcos\Projeto\intranet\settings.py'

with open(settings_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add to INSTALLED_APPS
if "'rest_framework'" not in content:
    installed_apps_block = """    'django_htmx',
    'axes',
    
    # API & Mobile App Ready
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'api',"""
    content = content.replace("'django_htmx',\n    'axes',", installed_apps_block)
    
# Add to MIDDLEWARE
if "'corsheaders.middleware.CorsMiddleware'" not in content:
    middleware_block = """MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',"""
    content = content.replace("MIDDLEWARE = [\n    'django.middleware.security.SecurityMiddleware',\n    'whitenoise.middleware.WhiteNoiseMiddleware',", middleware_block)

# Add REST_FRAMEWORK and SIMPLE_JWT Configs at the end
if "REST_FRAMEWORK" not in content:
    drf_config = """

# ==============================================================================
# CONFIGURAÇÕES DA API REST PARA MOBILE APP E FUTUROS MÓDULOS
# ==============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Habilitar CORS para permitir comunicação do App Mobile
CORS_ALLOW_ALL_ORIGINS = True # Mudar para False em produção e especificar os domínios
"""
    content += drf_config

with open(settings_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Settings updated successfully!")
