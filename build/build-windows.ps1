$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $Root
$Version = (python -c "import retrodeck; print(retrodeck.__version__)").Trim()
$Dist = Join-Path $Root "dist\RetroDeck"
if (Test-Path $Dist) { Remove-Item $Dist -Recurse -Force }
if (Test-Path (Join-Path $Root "dist\RetroDeck-$Version-windows.zip")) { Remove-Item (Join-Path $Root "dist\RetroDeck-$Version-windows.zip") -Force }
python -m pip install --upgrade pip
python -m pip install -r packaging\requirements-windows.txt
python -m PyInstaller --clean --noconfirm packaging\RetroDeck.spec
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}
if (!(Test-Path $Dist -PathType Container)) {
    throw "PyInstaller finished but the expected output directory is missing: $Dist"
}
$Zip = Join-Path $Root "dist\RetroDeck-$Version-windows.zip"
Compress-Archive -Path $Dist -DestinationPath $Zip -CompressionLevel Optimal
Write-Host "Windows release: $Dist"
Write-Host "Windows ZIP: $Zip"
