@echo off
echo ==============================================
echo Iniciando API Web - Modulo de Estoque
echo ==============================================

echo Verificando instalacao do Flask...
python -m pip install flask

echo.
echo Iniciando o servidor...
python api.py
pause
