with open("core/views.py", "r", encoding="utf-8") as f:
    content = f.read()

injection = """
    # Check Envs Masked
"""

replacement = """
    # Cache Status
    from django.core.cache import cache
    is_redis_ativo = getattr(settings, 'USE_REDIS', False)
    cache_motor = "Redis (Ativo)" if is_redis_ativo else "RAM Local (Fallback)"
    cache_tamanho = "0 KB"
    try:
        if is_redis_ativo:
            info = cache.client.get_client().info('memory')
            cache_tamanho = info.get('used_memory_human', '0 MB')
        else:
            import sys
            size_bytes = sys.getsizeof(cache._cache)
            cache_tamanho = f"{(size_bytes / 1024):.2f} KB"
    except Exception:
        cache_tamanho = "Erro ao medir"

    # Check Envs Masked
"""

if "cache_motor" not in content:
    content = content.replace(injection, replacement)

# Now inject it into the context dictionary which is around line 410. Let's find context definition.
# It usually looks like:
#     context = {
#         'config': config,
#         'cpu_percent': cpu_percent,

ctx_inject = """    context = {
        'config': config,"""

ctx_replacement = """    context = {
        'config': config,
        'cache_motor': cache_motor,
        'cache_tamanho': cache_tamanho,
        'is_redis_ativo': is_redis_ativo,"""

if "cache_motor': cache_motor" not in content:
    content = content.replace(ctx_inject, ctx_replacement)

# Also patch deploy
deploy_old = """    try:
        # 1. Migrate"""

deploy_new = """    try:
        # 0. Redis Activation
        ativar_redis = request.POST.get('ativar_redis') == 'on'
        env_path = os.path.join(settings.BASE_DIR, '.env')
        if ativar_redis and os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                env_text = f.read()
            if 'USE_REDIS' not in env_text:
                env_text += "\\nUSE_REDIS=True\\nREDIS_URL=redis://127.0.0.1:6379/1\\n"
            else:
                import re
                env_text = re.sub(r'USE_REDIS=.*', 'USE_REDIS=True', env_text)
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(env_text)

        # 1. Migrate"""

if "# 0. Redis Activation" not in content:
    content = content.replace(deploy_old, deploy_new)


with open("core/views.py", "w", encoding="utf-8") as f:
    f.write(content)

print("core/views.py patched.")
