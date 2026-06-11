@echo off
:start
echo ==============================================================
echo INICIANDO SERVIDOR DE DESENVOLVIMENTO (LIVE RELOAD ATIVADO)
echo ==============================================================
echo O sistema agora esta rodando com o monitor nativo do Django!
echo Qualquer alteracao em arquivos .py ou .html ira atualizar
echo o sistema em tempo real sem precisar reiniciar este prompt.
echo ==============================================================
echo.
echo Pressione CTRL+C para derrubar o servidor.
echo.
call venv\Scripts\activate
python manage.py bootstrap_sistema
python manage.py runserver 0.0.0.0:8000 --insecure
echo.
echo Servidor reiniciando (loop ativo)...
timeout /t 2 > NUL
goto start
