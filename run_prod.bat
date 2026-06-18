@echo off
cd /d "%~dp0"
:start
echo ==============================================================
echo INICIANDO SERVIDOR DE PRODUCAO (MODO ZERO-TRUST TESTE LOCAL)
echo ==============================================================

rem Leitura basica do .env para pegar o modo DEBUG
set DEBUG_MODE=False
for /f "tokens=1,2 delims==" %%A in (.env) do (
    if "%%A"=="DEBUG" set DEBUG_MODE=%%B
)

if "%DEBUG_MODE%"=="True" (
    echo - Debug Mode: [ALERTA] ATIVADO [Vulneravel]
) else (
    echo - Debug Mode: DESATIVADO [Extrema Seguranca]
)

echo - Servidor Web: WAITRESS (Pronto para alta carga no Windows)
echo - Arquivos Estaticos: WHITENOISE (Compactados e Cacheados)
echo ==============================================================
echo.
echo [1/3] Verificando integridade e seguranca de producao...
call venv\Scripts\activate
python manage.py check --deploy

echo.
echo [2/3] Aplicando atualizacoes no Banco de Dados (Migrate)...
python manage.py migrate

echo.
echo [3/3] Coletando arquivos estaticos (WhiteNoise)...
python manage.py collectstatic --noinput

echo.
echo Pressione CTRL+C para derrubar o servidor e S (Sim) para sair do loop.
echo.
set USE_HTTPS=False

echo [HOT-RELOAD] Iniciando Cão de Guarda (Daemon da IA) em background...
start /B venv\Scripts\python manage.py ai_daemon

echo [HOT-RELOAD] Iniciando Servidor Web com monitoramento (Hupper)...
hupper -m waitress --port=8005 intranet.wsgi:application
echo.
echo Servidor reiniciando (loop ativo)...
timeout /t 2 > NUL
goto start
