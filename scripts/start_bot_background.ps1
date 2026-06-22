$ErrorActionPreference = "Stop"

# Native mode (NapCatQQ-Desktop): NapCat runs as the Desktop GUI app and manages
# its own QQ login + reverse WebSocket. This script ONLY starts the Python bot.
# (Docker-era helpers -- docker compose / configure_napcat_onebot / qrcode -- are
# no longer used here; kept in the repo only for rollback. See QQBOT_SETUP.md.)

$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

$logDir = Join-Path $root "logs"
$pidFile = Join-Path $logDir "jmcomic-bot.pid"
$logFile = Join-Path $logDir "jmcomic-bot.log"
$errFile = Join-Path $logDir "jmcomic-bot.err.log"

New-Item -ItemType Directory -Force $logDir | Out-Null

# Kill ALL existing qqbot Python processes by command line. This catches stale /
# duplicate interpreters that aren't on 8080 or in the pid file -- such a zombie
# squatting on 8080 caused 403s during the Desktop migration.
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*qqbot_jm*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

# Backup: anything still listening on 8080, plus the pid file
$ids = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique
foreach ($id in $ids) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }
if (Test-Path $pidFile) {
  $oldPid = Get-Content $pidFile | Select-Object -First 1
  if ($oldPid) { Stop-Process -Id ([int]$oldPid) -Force -ErrorAction SilentlyContinue }
}

Start-Sleep -Seconds 1

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$process = Start-Process `
  -FilePath ".\.venv\Scripts\python.exe" `
  -ArgumentList ".\qqbot_jm.py" `
  -WorkingDirectory $root `
  -RedirectStandardOutput $logFile `
  -RedirectStandardError $errFile `
  -WindowStyle Hidden `
  -PassThru

Set-Content -Path $pidFile -Value $process.Id -Encoding ASCII
Write-Host "Python bot started. PID=$($process.Id)"
Write-Host "Make sure NapCatQQ-Desktop is running and logged in; it reverse-connects within ~30s."
Write-Host "Log: $logFile"
