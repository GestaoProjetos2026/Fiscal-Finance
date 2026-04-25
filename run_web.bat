@echo off
:: ============================================================
:: run_web.bat — Inicia a API Flask + abre o frontend web
:: Squad FISC — Fiscal Finance
:: ============================================================

title Fiscal Finance — Servidor Web

echo.
echo  ============================================================
echo   Fiscal Finance — Squad FISC
echo   Iniciando servidor web...
echo  ============================================================
echo.

:: Instala dependencias se necessario
echo  [1/3] Verificando dependencias Python...
cd /d "%~dp0src"
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo  [ERRO] Falha ao instalar dependencias.
    echo         Certifique-se que o Python e o pip estao instalados.
    pause
    exit /b 1
)

echo  [2/3] Iniciando API Flask em http://localhost:5000 ...
echo.

:: Inicia o Flask em segundo plano
start "API Fiscal Finance" /min python app.py

:: Aguarda o Flask subir (3 segundos)
echo  Aguardando servidor iniciar...
timeout /t 3 /nobreak >nul

:: Abre o frontend no navegador padrao
echo  [3/3] Abrindo frontend no navegador...
start "" "http://localhost:5000"

echo.
echo  ============================================================
echo   Sistema iniciado com sucesso!
echo.
echo   Frontend : http://localhost:5000/web
echo   API      : http://localhost:5000
echo   Swagger  : http://localhost:5000/docs
echo.
echo   Login padrao: admin@fiscal.com / admin123
echo.
echo   Para parar: feche a janela "API Fiscal Finance"
echo               ou pressione CTRL+C nela.
echo  ============================================================
echo.

pause
