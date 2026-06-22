import os

views_content = """
import os
import requests
from django.core.cache import cache

def gerar_insight_ia(user):
    # Fetch from cache first to avoid slow load times
    cache_key = f"dashboard_insight_{user.id}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data

    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return {"versiculo": "O Senhor é o meu pastor e nada me faltará. (Salmos 23:1)", "insight": "Foque no essencial e organize sua semana com excelência."}
            
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = (
            f"Você é um conselheiro cristão de liderança. O usuário atual chama-se {user.first_name}. "
            "Gere uma resposta em formato JSON estrito com 2 chaves: "
            "'versiculo' (Um versículo encorajador na versão NAA, com a referência) e "
            "'insight' (Uma dica de 1 frase curta focada em liderança servidora, organização ou excelência no ministério). "
            "Apenas o JSON, sem markdown."
        )
        
        data = {
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=3)
        
        if response.status_code == 200:
            import json
            content = response.json()['choices'][0]['message']['content']
            result = json.loads(content)
            # Cache for 12 hours
            cache.set(cache_key, result, 43200)
            return result
    except Exception as e:
        print(f"Erro IA: {e}")
        
    return {"versiculo": "Tudo posso naquele que me fortalece. (Fp 4:13)", "insight": "Deus capacita os escolhidos. Tenha um excelente dia de serviço!"}
"""

with open(r'c:\Users\MarcosLira\Desktop\Marcos\Projeto\core\views.py', 'a', encoding='utf-8') as f:
    f.write(views_content)
