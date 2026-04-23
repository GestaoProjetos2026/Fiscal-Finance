@echo off
title Squad FISC App - Instalador de Dependencias
color 0A
echo.
echo  ====================================================
echo    SQUAD FISC APP - Instalador de Dependencias
echo    Python + Flask + PHP + Postman
echo  ====================================================
echo.

REM =====================================================
REM === 1. Verificar se Python esta instalado ===
REM =====================================================
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python NAO foi encontrado neste computador.
    echo.
    echo  Para instalar o Python:
    echo  1. Acesse: https://www.python.org/downloads/
    echo  2. Baixe a versao mais recente ^(3.10 ou superior^)
    echo  3. NA INSTALACAO: marque "Add Python to PATH" ^!
    echo  4. Depois de instalar, execute este arquivo novamente.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version') do set PYVER=%%v
echo [OK] %PYVER% encontrado.
echo.

REM =====================================================
REM === 2. Atualizar pip ===
REM =====================================================
echo [INFO] Atualizando pip...
python -m pip install --upgrade pip --quiet
echo [OK] pip atualizado.
echo.

REM =====================================================
REM === 3. Instalar dependencias Python (PyQt6, Flask, PyInstaller) ===
REM =====================================================
echo [INFO] Instalando dependencias Python (PyQt6, Flask, PyInstaller)...
cd /d "%~dp0.."
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao instalar dependencias Python. Verifique sua conexao com a internet.
    pause
    exit /b 1
)
echo [OK] Dependencias Python instaladas com sucesso.
echo.

REM =====================================================
REM === 4. Verificar e instalar PHP ===
REM =====================================================
echo [INFO] Verificando PHP...
php --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%v in ('php --version 2^>nul ^| findstr /i "PHP"') do (
        echo [OK] %%v ja instalado. Pulando instalacao.
        goto php_ok
    )
)

echo [INFO] PHP nao encontrado. Instalando automaticamente...
echo [INFO] Isso pode levar alguns segundos...
powershell -ExecutionPolicy Bypass -File "%~dp0..\instalar_php.ps1"
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao instalar o PHP.
    echo        O PHP e um requerimento obrigatorio deste sistema.
    echo        Verifique sua conexao com a internet e tente novamente.
    pause
    exit /b 1
)
echo [OK] PHP instalado com sucesso.

:php_ok
echo.

REM =====================================================
REM === 5. Verificar e instalar Postman ===
REM =====================================================
echo [INFO] Verificando Postman...

REM Checar se Postman ja esta instalado via winget
winget list --id Postman.Postman >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Postman ja esta instalado. Pulando instalacao.
    goto postman_ok
)

REM Checar se Postman esta instalado manualmente (pasta AppData)
if exist "%LOCALAPPDATA%\Postman\Postman.exe" (
    echo [OK] Postman ja esta instalado. Pulando instalacao.
    goto postman_ok
)

echo [INFO] Postman nao encontrado. Instalando via winget...
winget install -e --id Postman.Postman --silent --accept-source-agreements --accept-package-agreements
if %errorlevel% neq 0 (
    echo [AVISO] Instalacao automatica do Postman falhou.
    echo         Baixe manualmente em: https://www.postman.com/downloads/
    echo         O Postman e usado apenas para testar a API ^(nao e obrigatorio para rodar o app^).
    echo.
) else (
    echo [OK] Postman instalado com sucesso.
)

:postman_ok
echo.

REM =====================================================
echo  ====================================================
echo    Instalacao concluida!
echo.
echo    Dependencias instaladas:
echo    [*] Python + PyQt6 + Flask + PyInstaller
echo    [*] PHP 8.2 ^(motor de calculos fiscais^)
echo    [*] Postman ^(testes da API REST^)
echo.
echo    Agora voce pode rodar o app com: run_app.bat
echo  ====================================================
echo.
pause
