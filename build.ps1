# Build de FlujoCaja como app de escritorio (one-dir) + zip.
# Requisitos: internet (para pip), el resto es local.
$ErrorActionPreference = "Stop"

Write-Host "== Instalando dependencias de build =="
& .\venv\Scripts\python.exe -m pip install -r requirements-dev.txt

Write-Host "== Ejecutando PyInstaller =="
& .\venv\Scripts\python.exe -m PyInstaller --noconfirm --clean FlujoCaja.spec

# Licencias y aviso de terceros junto al exe (obligatorio si se distribuye)
Write-Host "== Copiando licencias y avisos =="
Copy-Item "THIRD_PARTY_NOTICES.md" "dist\FlujoCaja\" -Force
if (-not (Test-Path "dist\FlujoCaja\licenses")) { New-Item -ItemType Directory "dist\FlujoCaja\licenses" | Out-Null }
Copy-Item "licenses\*.txt" "dist\FlujoCaja\licenses\" -Force

$zip = "dist\FlujoCaja-win.zip"
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path "dist\FlujoCaja" -DestinationPath $zip

Write-Host "Empaquetado listo: $zip"