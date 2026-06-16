$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

$logDir = Join-Path $PSScriptRoot "logs"
$pidFile = Join-Path $PSScriptRoot "jmcomic-bot.pid"
$logFile = Join-Path $logDir "jmcomic-bot.log"
$errFile = Join-Path $logDir "jmcomic-bot.err.log"
$qrcodePath = Join-Path $PSScriptRoot "napcat-qrcode.png"
$webuiConfigPath = Join-Path $PSScriptRoot "tools\napcat-docker\config\webui.json"

New-Item -ItemType Directory -Force $logDir | Out-Null

function Get-NapCatCredential {
  $token = (Get-Content -Raw $webuiConfigPath | ConvertFrom-Json).token
  $sha = [Security.Cryptography.SHA256]::Create()
  $bytes = [Text.Encoding]::UTF8.GetBytes($token + ".napcat")
  $hash = -join ($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString("x2") })
  $login = Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:6099/api/auth/login" `
    -ContentType "application/json" `
    -Body (@{ hash = $hash } | ConvertTo-Json)
  return $login.data.Credential
}

function Invoke-NapCatApi($path, $credential) {
  return Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:6099/api/$path" `
    -Headers @{ Authorization = "Bearer $credential" }
}

function Wait-NapCatLogin($credential) {
  $opened = $false
  while ($true) {
    $status = Invoke-NapCatApi "QQLogin/CheckLoginStatus" $credential
    if ($status.data.isLogin) {
      if (Test-Path $qrcodePath) {
        Remove-Item -LiteralPath $qrcodePath -Force
      }
      Write-Host "QQ logged in. QR code image removed."
      return
    }

    if ($status.data.loginError -like "*过期*") {
      Invoke-NapCatApi "QQLogin/RefreshQRcode" $credential | Out-Null
      Start-Sleep -Seconds 2
    }

    docker cp jm-napcat:/app/napcat/cache/qrcode.png $qrcodePath | Out-Null
    if (-not $opened -and (Test-Path $qrcodePath)) {
      Start-Process $qrcodePath
      $opened = $true
      Write-Host "QQ is not logged in. QR code saved and opened: $qrcodePath"
      Write-Host "Scan it with QQ, then approve login on your phone."
    }

    Start-Sleep -Seconds 3
  }
}

Write-Host "Starting NapCat container..."
$napcat = docker ps -a --filter "name=^/jm-napcat$" --format "{{.Names}}"
if ($napcat) {
  docker start jm-napcat | Out-Null
} else {
  docker compose -f .\docker-compose.napcat.yml up -d
}

for ($i = 0; $i -lt 30; $i++) {
  try {
    Invoke-WebRequest -Uri "http://127.0.0.1:6099" -UseBasicParsing -TimeoutSec 2 | Out-Null
    break
  } catch {
    Start-Sleep -Seconds 2
  }
}

try {
  .\configure_napcat_onebot.ps1
} catch {
  Write-Host "NapCat is not logged in. Opening QR code..."
  $credential = Get-NapCatCredential
  Wait-NapCatLogin $credential
  .\configure_napcat_onebot.ps1
}

$existing = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
if ($existing) {
  Write-Host "NoneBot already running on 127.0.0.1:8080."
  exit 0
}

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$process = Start-Process `
  -FilePath ".\.venv\Scripts\python.exe" `
  -ArgumentList ".\qqbot_jm.py" `
  -WorkingDirectory $PSScriptRoot `
  -RedirectStandardOutput $logFile `
  -RedirectStandardError $errFile `
  -WindowStyle Hidden `
  -PassThru

Set-Content -Path $pidFile -Value $process.Id -Encoding ASCII
Write-Host "NoneBot started in background. PID=$($process.Id)"
Write-Host "Log: $logFile"
