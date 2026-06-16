$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$webuiConfig = Join-Path $root "tools\napcat-docker\config\webui.json"
$token = (Get-Content -Raw $webuiConfig | ConvertFrom-Json).token

$sha = [Security.Cryptography.SHA256]::Create()
$bytes = [Text.Encoding]::UTF8.GetBytes($token + ".napcat")
$hash = -join ($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString("x2") })

$login = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:6099/api/auth/login" `
  -ContentType "application/json" `
  -Body (@{ hash = $hash } | ConvertTo-Json)

$credential = $login.data.Credential
$headers = @{ Authorization = "Bearer $credential" }

$resp = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:6099/api/OB11Config/GetConfig" `
  -Headers $headers

if ($resp.code -ne 0) {
  throw "NapCat OB11 config unavailable: $($resp.message). Login QQ in NapCat WebUI first."
}

$config = $resp.data
$client = [pscustomobject]@{
  enable = $true
  name = "jmcomic-nonebot"
  url = "ws://host.docker.internal:8080/onebot/v11/ws"
  reportSelfMessage = $true
  messagePostFormat = "array"
  token = "jmcomic_local_bot"
  debug = $false
  heartInterval = 30000
  reconnectInterval = 30000
  verifyCertificate = $true
}

$config.network.websocketClients = @(
  @($config.network.websocketClients) |
    Where-Object { $_.name -ne "jmcomic-nonebot" }
) + @($client)

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:6099/api/OB11Config/SetConfig" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body (@{ config = ($config | ConvertTo-Json -Depth 30 -Compress) } | ConvertTo-Json)

Write-Host "NapCat OneBot reverse WebSocket configured."
