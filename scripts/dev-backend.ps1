param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $labRoot
& '.\.venv\Scripts\python.exe' backend\manage.py runserver "127.0.0.1:$Port"
exit $LASTEXITCODE
