$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $labRoot
function Assert-Exit([string]$Step) { if ($LASTEXITCODE -ne 0) { throw "$Step failed (exit $LASTEXITCODE)." } }
& '.\.venv\Scripts\python.exe' backend\manage.py check --settings=config.settings_test
Assert-Exit 'Django check'
& '.\.venv\Scripts\python.exe' backend\manage.py makemigrations --check --dry-run --settings=config.settings_test
Assert-Exit 'Migration check'
& '.\.venv\Scripts\python.exe' backend\manage.py test apps --settings=config.settings_test
Assert-Exit 'Backend tests'
Push-Location frontend
try {
    & npm.cmd run format:check
    Assert-Exit 'Frontend formatting'
    & npm.cmd run build
    Assert-Exit 'Frontend build'
} finally { Pop-Location }
Write-Host 'All local checks passed. MySQL integration is a separate check; see docs/01-local-development.md.'
