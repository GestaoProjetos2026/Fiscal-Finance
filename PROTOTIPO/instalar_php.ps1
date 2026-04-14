Write-Host "=== INICIANDO INSTALACAO AUTOMATICA DO PHP ==="
$destDir = "C:\php"
New-Item -ItemType Directory -Force -Path $destDir | Out-Null

Write-Host "1. Baixando arquivos oficiais do PHP (Isso pode demorar alguns segundos)..."
$url = "https://windows.php.net/downloads/releases/archives/php-8.2.14-nts-Win32-vs16-x64.zip" 
$zipPath = "$destDir\php.zip"
Invoke-WebRequest -Uri $url -OutFile $zipPath

Write-Host "2. Extraindo arquivos em C:\php ..."
Expand-Archive -Path $zipPath -DestinationPath $destDir -Force
Remove-Item $zipPath

Write-Host "3. Configurando Variaveis de Ambiente do Windows..."
$envPATH = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($envPATH -notmatch "C:\\php") {
    [Environment]::SetEnvironmentVariable("PATH", $envPATH + ";C:\php", "User")
}

# Configura php.ini básico para funcionar perfeitamente
Copy-Item "$destDir\php.ini-development" "$destDir\php.ini" -ErrorAction SilentlyContinue

Write-Host "=== PHP INSTALADO COM SUCESSO! ==="
Write-Host "O caminho C:\php foi adicionado ao PATH."
Write-Host "Pressione qualquer tecla para sair."
