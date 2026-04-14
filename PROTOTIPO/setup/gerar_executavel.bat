@echo off
title Squad FISC App - Gerador de Executavel
color 0B
echo.
echo  ====================================================
echo    SQUAD FISC APP - Gerando Executavel Unico (.exe)
echo  ====================================================
echo.

REM === Mudar para a pasta raiz do projeto ===
cd /d "%~dp0.."

REM === Verificar PyInstaller ===
pyinstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] PyInstaller nao encontrado. Instalando...
    pip install pyinstaller --quiet
)

REM === Limpar builds anteriores ===
if exist "dist" (
    echo [INFO] Removendo build anterior...
    rmdir /s /q dist
)
if exist "build" (
    rmdir /s /q build
)

REM === Gerar o .exe ===
echo [INFO] Compilando o app... (isso pode levar alguns minutos)
echo.
pyinstaller setup\SquadFiscApp.spec --distpath dist --workpath build --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Falha ao gerar o executavel.
    pause
    exit /b 1
)

echo.
echo  ====================================================
echo    SUCESSO! Executavel gerado em:
echo    %~dp0dist\SquadFiscApp.exe
echo.
echo    Voce pode copiar SOMENTE esse arquivo .exe
echo    para qualquer PC com Windows e ele vai rodar!
echo  ====================================================
echo.
pause
