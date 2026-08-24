[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$deps = Join-Path $root '.deps'
$prefix = Join-Path $deps 'rdkit'
$config = Join-Path $prefix 'Library\lib\cmake\rdkit\rdkit-config.cmake'
$boostHeader = Join-Path $prefix 'Library\include\boost\version.hpp'
if ((Test-Path -LiteralPath $config) -and (Test-Path -LiteralPath $boostHeader)) {
    Write-Host "RDKit C++ dependencies are ready: $prefix"
    exit 0
}

New-Item -ItemType Directory -Force -Path $deps | Out-Null
$archive = Join-Path $deps 'micromamba.tar.bz2'
if (-not (Test-Path -LiteralPath $archive)) {
    Invoke-WebRequest -Uri 'https://micro.mamba.pm/api/micromamba/win-64/latest' -OutFile $archive
}
$extract = Join-Path $deps 'micromamba-extract'
New-Item -ItemType Directory -Force -Path $extract | Out-Null
tar -xf $archive -C $extract
$micromamba = Join-Path $extract 'Library\bin\micromamba.exe'
if (-not (Test-Path -LiteralPath $micromamba)) { throw 'micromamba.exe was not extracted.' }

& $micromamba create -y -p $prefix -c conda-forge 'rdkit=2026.03.5' 'librdkit-dev=2026.03.5' 'libboost-devel=1.90.0'
if ($LASTEXITCODE -ne 0) { throw "RDKit environment creation failed with exit code $LASTEXITCODE" }
if (-not (Test-Path -LiteralPath $config)) { throw 'The installed package did not provide rdkit-config.cmake.' }
Write-Host "RDKit C++ dependencies are ready: $prefix"
