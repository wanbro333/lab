param([string]$PythonCommand = 'python')
$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $labRoot
function Assert-Exit([string]$Step) { if ($LASTEXITCODE -ne 0) { throw "$Step failed (exit $LASTEXITCODE)." } }
function New-LabSecret {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    return [Convert]::ToBase64String($bytes)
}
if (!(Test-Path -LiteralPath '.env')) {
    $template = Get-Content -LiteralPath '.env.example' -Raw
    $template = $template.Replace('replace-with-a-long-random-secret', (New-LabSecret))
    $template = $template.Replace('replace-with-a-random-password', (New-LabSecret))
    $template = $template.Replace('replace-with-another-random-password', (New-LabSecret))
    [IO.File]::WriteAllText((Join-Path $labRoot '.env'), $template, (New-Object Text.UTF8Encoding($false)))
    Write-Host 'Created .env with random local secrets.'
}
if (!(Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    & $PythonCommand -m venv .venv
    Assert-Exit 'Create virtual environment'
}
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
Assert-Exit 'Install Python dependencies'
Push-Location frontend
try { & npm.cmd ci; Assert-Exit 'Install frontend dependencies' } finally { Pop-Location }
Write-Host 'Setup complete. Next: docker compose up -d --wait'
Write-Host 'Then: .\.venv\Scripts\python.exe backend\manage.py migrate'
Write-Host 'Optional demo: .\.venv\Scripts\python.exe backend\manage.py seed_demo --create-user'
