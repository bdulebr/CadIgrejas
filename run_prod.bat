@echo off
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
    echo - Debug Mode: [ALERTA] ATIVADO (Vulneravel)
) else (
    echo - Debug Mode: DESATIVADO (Extrema Seguranca)
)

echo - Servidor Web: WAITRESS (Pronto para alta carga no Windows)
echo - Arquivos Estaticos: WHITENOISE (Compactados e Cacheados)
echo ==============================================================
echo.
echo Pressione CTRL+C para derrubar o servidor e S (Sim) para sair do loop.
echo.
call venv\Scripts\activate
waitress-serve --port=8000 intranet.wsgi:application
echo.
echo Servidor reiniciando (loop ativo)...
timeout /t 2 > NUL
goto start
