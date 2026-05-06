# Smoke test launcher (Windows-friendly, one command from repo root):
#   .\scripts\smoke_auth.ps1
#   .\scripts\smoke_auth.ps1 -BaseUrl "http://127.0.0.1:8000"
Param(
    [string]$BaseUrl = ""
)
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $RepoRoot "venv\Scripts\python.exe"
if (-not (Test-Path $Py)) {
    $Py = "python"
}
$ScriptPath = Join-Path $PSScriptRoot "smoke_auth.py"
if ($BaseUrl) {
    & $Py $ScriptPath --base-url $BaseUrl
} else {
    & $Py $ScriptPath
}
exit $LASTEXITCODE
