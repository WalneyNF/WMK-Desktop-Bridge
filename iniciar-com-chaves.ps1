# Inicia WMK Desktop Bridge com segredos recuperados via DPAPI para esta conta Windows.
param([string]$Workspace = '')
$ErrorActionPreference = 'Stop'
$base = Join-Path $env:LOCALAPPDATA 'WMKDesktopBridge\secrets'
$names = @('GROQ_API_KEY','OPENAI_API_KEY','GEMINI_API_KEY','WMK_BLENDER_TOKEN')
foreach ($name in $names) {
    $file = Join-Path $base ($name + '.dpapi')
    if (-not (Test-Path -LiteralPath $file)) { continue }
    $secure = Get-Content -LiteralPath $file -Raw | ConvertTo-SecureString
    $credential = New-Object System.Management.Automation.PSCredential('wmk', $secure)
    [Environment]::SetEnvironmentVariable($name, $credential.GetNetworkCredential().Password, 'Process')
}
if ($Workspace.Trim()) {
    if (-not (Test-Path -LiteralPath $Workspace -PathType Container)) { throw 'Pasta de trabalho nao existe' }
    $env:WMK_WORKSPACE = (Resolve-Path -LiteralPath $Workspace).Path
} else {
    Remove-Item Env:WMK_WORKSPACE -ErrorAction SilentlyContinue
}
try {
    Set-Location -LiteralPath $PSScriptRoot
    Write-Host 'WMK Desktop Bridge v0.6.0 em http://127.0.0.1:8767/agents' -ForegroundColor Cyan
    Write-Host 'Ctrl+C para parar. A configuracao de agente e Blender fica local.'
    py web_server.py
} finally {
    foreach ($name in $names) { Remove-Item ("Env:" + $name) -ErrorAction SilentlyContinue }
}
