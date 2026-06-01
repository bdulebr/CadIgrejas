import json
import traceback
import os
from datetime import datetime
from django.conf import settings

class JsonErrorLoggerMiddleware:
    """
    Middleware Zero-Trust que intercepta falhas (Exceptions/500) e as registra
    em um arquivo JSON Estruturado (JSONL) para auditoria e correções cirúrgicas.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.log_file = os.path.join(settings.BASE_DIR, 'logs', 'erros_criticos.jsonl')

        # Garante que o diretório e o arquivo existem
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        Esta função é acionada automaticamente pelo Django se alguma view lançar uma Exception.
        """
        # Ignorar erros de página não encontrada (404) para não poluir o log, se quisermos.
        # Mas Http404 não costuma acionar process_exception no middleware padrão se for bem tratada.

        # 1. Coletar rastreamento (Stacktrace)
        tb = traceback.format_exc()

        # 2. Coletar informações do usuário se logado
        user = "Anônimo"
        user_id = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user.username
            user_id = request.user.id

        # 3. Formatar o log em um dicionário
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "level": "ERROR",
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "user": user,
            "user_id": user_id,
            "path": request.path,
            "method": request.method,
            "query_params": dict(request.GET),
            "traceback": tb
        }

        # 4. Salvar de forma appendável (JSONL - uma linha por JSON)
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error_data, ensure_ascii=False) + '\n')
        except Exception as file_err:
            print(f"FATAL: Não foi possível escrever no log de erros JSON: {file_err}")

        # Retorna None para permitir que o Django continue seu fluxo de erro normal (mostrando tela de 500)
        return None
