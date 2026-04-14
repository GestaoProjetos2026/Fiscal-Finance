@echo off
title Squad FISC App
echo Iniciando Squad FISC App...
cd /d "%~dp0"
python app.py
if %errorlevel% neq 0 (
    echo.
    echo ERRO ao iniciar o app. Veja a mensagem acima.
    pause
)
