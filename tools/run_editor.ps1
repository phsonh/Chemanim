param(
    [string]$Document
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root

$editorArguments = @("$PSScriptRoot\editor.py")
if ($Document) {
    $editorArguments += $Document
}

$venvPython = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    throw 'Editor environment is missing. Run .\tools\setup_editor.ps1 first.'
}
& $venvPython @editorArguments
