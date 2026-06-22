import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
django.setup()

from django.conf import settings
from django.core.cache import cache

print("--- DIAGNOSTICO DE CACHE ---")
print(f"USE_REDIS (from env): {getattr(settings, 'USE_REDIS', False)}")
print(f"Cache Backend Class: {cache.__class__.__name__}")

try:
    # Test setting and getting
    cache.set('test_key', 'test_value', timeout=10)
    val = cache.get('test_key')
    print(f"Cache SET/GET test: {'SUCCESS' if val == 'test_value' else 'FAILED (Got ' + str(val) + ')'}")

    # Test clearing
    cache.clear()
    val_after_clear = cache.get('test_key')
    print(f"Cache CLEAR test: {'SUCCESS' if val_after_clear is None else 'FAILED (Key still exists)'}")

except Exception as e:
    print(f"ERROR: {e}")
