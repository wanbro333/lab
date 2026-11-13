$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
foreach ($serviceName in @('frontend', 'backend')) {
    $pidFile = Join-Path $labRoot ".runtime\$serviceName.pid"
    if (!(Test-Path -LiteralPath $pidFile)) { continue }
    $serverPid = [int](Get-Content -LiteralPath $pidFile -Raw).Trim()
    $serverProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$serverPid"
    if ($serverProcess) {
        $ownedBackend = $serviceName -eq 'backend' -and $serverProcess.ExecutablePath -eq (Join-Path $labRoot '.venv\Scripts\python.exe') -and $serverProcess.CommandLine.Contains('runserver')
        $ownedFrontend = $serviceName -eq 'frontend' -and $serverProcess.CommandLine.Contains((Join-Path $labRoot 'frontend\node_modules\vite\bin\vite.js'))
        if (!$ownedBackend -and !$ownedFrontend) { throw "PID $serverPid no longer belongs to this preview; not stopped." }
        & taskkill.exe /PID $serverPid /T /F | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Could not stop $serviceName preview." }
        Write-Host "Stopped $serviceName preview (PID $serverPid)."
    }
    Remove-Item -LiteralPath $pidFile
}
Write-Host 'Database remains running. To stop local ZIP MySQL: scripts/dev-mysql.ps1 -Action stop'
