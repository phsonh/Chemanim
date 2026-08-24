[CmdletBinding()]
param(
    [ValidateSet('Debug', 'Release')]
    [string]$Configuration = 'Release'
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
& (Join-Path $root 'tools\bootstrap_native_deps.ps1')
$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (-not (Test-Path -LiteralPath $vswhere)) {
    throw 'Visual Studio Installer (vswhere.exe) was not found.'
}

$vs = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (-not $vs) { throw 'Visual Studio with the C++ workload was not found.' }

$cmake = Join-Path $vs 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
$ninjaDirectory = Join-Path $vs 'Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja'
$vcvars = Join-Path $vs 'VC\Auxiliary\Build\vcvars64.bat'
$buildDirectory = Join-Path $root ("build\" + $Configuration.ToLowerInvariant())

if (-not (Test-Path -LiteralPath $cmake)) { throw "CMake was not found at $cmake" }
if (-not (Test-Path -LiteralPath $vcvars)) { throw "vcvars64.bat was not found at $vcvars" }

$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { $python = Join-Path $root '.deps\rdkit\python.exe' }
$configure = "`"$cmake`" -S `"$root`" -B `"$buildDirectory`" -G Ninja -DCMAKE_BUILD_TYPE=$Configuration -DCMAKE_MAKE_PROGRAM=`"$(Join-Path $ninjaDirectory 'ninja.exe')`" -DPython3_EXECUTABLE=`"$python`" -DCHEMANIM_RDKIT_ROOT=`"$(Join-Path $root '.deps\rdkit')`""
$build = "`"$cmake`" --build `"$buildDirectory`" --config $Configuration"
$buildCommand = "call `"$vcvars`" >nul && $configure && $build"
& $env:COMSPEC /d /c $buildCommand
if ($LASTEXITCODE -ne 0) { throw "Build failed with exit code $LASTEXITCODE" }

Write-Host "Built: $(Join-Path $buildDirectory 'chemanim.exe')"
