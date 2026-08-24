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

$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) {
    & py -3 @editorArguments
} else {
    & python @editorArguments
}
