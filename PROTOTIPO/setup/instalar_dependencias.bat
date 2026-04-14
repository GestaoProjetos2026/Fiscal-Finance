@echo off
title Squad FISC App - Instalador de Dependencias
color 0A
echo.
echo  ====================================================
echo    SQUAD FISC APP - Instalador de Dependencias
echo  ====================================================
echo.

REM === 1. Verificar se Python esta instalado ===
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python NAO foi encontrado neste computador.
    echo.
    echo  Para instalar o Python:
    echo  1. Acesse: https://www.python.org/downloads/
    echo  2. Baixe a versao mais recente ^(3.10 ou superior^)
    echo  3. NA INSTALACAO: marque "Add Python to PATH" ^^!
    echo  4. Depois de instalar, execute este arquivo novamente.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version') do set PYVER=%%v
echo [OK] %PYVER% encontrado.
echo.

REM === 2. Atualizar pip ===
echo [INFO] Atualizando pip...
python -m pip install --upgrade pip --quiet
echo [OK] pip atualizado.
echo.

REM === 3. Instalar dependencias do requirements.txt ===
echo [INFO] Instalando dependencias (PyQt6, PyInstaller)...
cd /d "%~dp0.."
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao instalar dependencias. Verifique sua conexao com a internet.
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas com sucesso.
echo.

echo  ====================================================
echo    Instalacao concluida!
echo    Agora voce pode rodar o app com: run_app.bat
echo  ====================================================
echo.
pause
