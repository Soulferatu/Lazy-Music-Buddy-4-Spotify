param(
    [int]$Port = 1337
)

$ErrorActionPreference = "Stop"
$AppImport = "wacken_playlist:create_app"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

Write-Host "Stopping existing Flask dev servers for $AppImport..."

$processes = Get-CimInstance Win32_Process |
    Where-Object {
        $_.CommandLine -and
        $_.CommandLine.Contains("-m flask") -and
        $_.CommandLine.Contains($AppImport)
    }

foreach ($process in $processes) {
    Write-Host "Stopping PID $($process.ProcessId)"
    Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
}

Write-Host "Starting Flask dev server on http://0.0.0.0:$Port (all interfaces)"
Write-Host "Access from this machine : http://127.0.0.1:$Port"
Write-Host "Access from phone/tablet : http://<your-PC-IP>:$Port"
Set-Location $RepoRoot
py -m flask --app $AppImport --debug run --host 0.0.0.0 --port $Port
