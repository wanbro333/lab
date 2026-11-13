param([ValidateSet('init', 'start', 'stop')][string]$Action = 'start')
$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $labRoot
& '.\.venv\Scripts\python.exe' scripts\local_mysql.py $Action
exit $LASTEXITCODE
