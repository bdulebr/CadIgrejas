@echo off
echo ==============================================================
echo INICIANDO SERVIDOR DE PRODUCAO (MODO ZERO-TRUST TESTE LOCAL)
echo ==============================================================
echo - Debug Mode: DESATIVADO (Extrema Seguranca)
echo - Servidor Web: WAITRESS (Pronto para alta carga no Windows)
echo - Arquivos Estaticos: WHITENOISE (Compactados e Cacheados)
echo ==============================================================
echo.
echo Pressione CTRL+C para derrubar o servidor.
echo.
call venv\Scripts\activate
waitress-serve --port=8000 intranet.wsgi:application
pause
