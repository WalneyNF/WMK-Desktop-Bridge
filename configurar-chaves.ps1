# Configurar chaves WMK de forma protegida pelo usuário Windows (DPAPI).
# Não cole a chave no repositório nem no histórico do PowerShell.
$ErrorActionPreference = 'Stop'
$base = Join-Path $env:LOCALAPPDATA 'WMKDesktopBridge\secrets'
New-Item -ItemType Directory -Path $base -Force | Out-Null
$items = @{
    '1' = 'GROQ_API_KEY'
    '2' = 'OPENAI_API_KEY'
    '3' = 'GEMINI_API_KEY'
    '4' = 'WMK_BLENDER_TOKEN'
}
Write-Host 'WMK Desktop Bridge - configurar credenciais' -ForegroundColor Cyan
Write-Host '1 Groq | 2 OpenAI | 3 Gemini | 4 Token Blender'
Write-Host 'A chave sera salva cifrada por DPAPI para este usuario Windows.'
$choice = Read-Host 'Escolha 1-4'
if (-not $items.ContainsKey($choice)) { throw 'Escolha invalida' }
$keyName = $items[$choice]
$value = Read-Host "Informe $keyName (entrada oculta)" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($value)
try {
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    if ($plain.Length -lt 16) { throw 'Use valor com pelo menos 16 caracteres' }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
}
$encrypted = $value | ConvertFrom-SecureString
Set-Content -LiteralPath (Join-Path $base ($keyName + '.dpapi')) -Value $encrypted -Encoding Ascii
Write-Host "$keyName configurada. Nao compartilhe seu arquivo DPAPI." -ForegroundColor Green
