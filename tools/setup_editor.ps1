$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root '.venv'
if (-not (Test-Path -LiteralPath $venv)) { py -3 -m venv $venv }
$python = Join-Path $venv 'Scripts\python.exe'
& $python -m pip install --upgrade pip
& $python -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
Write-Host "Editor environment ready: $python"
